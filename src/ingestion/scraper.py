import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
from src.ingestion.store import MongoStore

from src.ingestion.youtube_loader import YouTubeLoader
from src.ingestion.slide_loader import SlideLoader

class WebScraper:
    def __init__(self, start_url, allowed_domains=None, base_path=None):
        self.start_url = start_url
        self.allowed_domains = allowed_domains or [urlparse(start_url).netloc]
        self.base_path = base_path or urlparse(start_url).path
        self.visited = set()
        self.store = MongoStore()
        self.rp = RobotFileParser()
        self.setup_robots_txt(start_url)
        
        self.yt_loader = YouTubeLoader()
        self.slide_loader = SlideLoader()

    def setup_robots_txt(self, url):
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        print(f"Checking robots.txt at: {robots_url}")
        try:
            self.rp.set_url(robots_url)
            self.rp.read()
        except Exception as e:
            print(f"Warning: Could not read robots.txt: {e}")

    def can_fetch(self, url):
        return self.rp.can_fetch("*", url)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        if parsed.netloc not in self.allowed_domains:
            return False
        return True

    def process_pdf(self, url):
        print(f"Processing PDF: {url}")
        data = self.slide_loader.load_pdf(url)
        if data:
            self.store.save_document(url, data['text'], "", doc_type="slide", metadata={"pages": data['pages']})

    def process_youtube(self, url):
        print(f"Processing YouTube: {url}")
        data = self.yt_loader.get_transcript(url)
        if data:
            self.store.save_document(url, data['text'], "", doc_type="video", metadata={"video_id": data['video_id'], "transcript": data['transcript']})

    def scrape(self):
        queue = [self.start_url]
        
        while queue:
            url = queue.pop(0)
            if url in self.visited:
                continue
            
            self.visited.add(url)
            
            if url.lower().endswith('.pdf'):
                self.process_pdf(url)
                continue

            if not self.can_fetch(url):
                print(f"Skipping (robots.txt disallowed): {url}")
                continue

            print(f"Crawling: {url}")
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    print(f"Failed to fetch {url}: Status {response.status_code}")
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                
                for img in soup.find_all('img'):
                    alt = img.get('alt', '')
                    src = img.get('src', '')
                    if alt:
                        img.replace_with(f"\n[Image: {alt} (URL: {urljoin(url, src)})]\n")
                
                for script in soup(["script", "style"]):
                    script.decompose()
                text_content = soup.get_text(separator='\n', strip=True)
                
                self.store.save_document(url, text_content, response.text)
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    full_url = full_url.split('#')[0]
                    
                    if "youtube.com" in full_url or "youtu.be" in full_url:
                        if full_url not in self.visited:
                            self.process_youtube(full_url)
                            self.visited.add(full_url)
                        continue

                    if full_url not in self.visited and self.is_valid_url(full_url):
                        queue.append(full_url)
                
                for iframe in soup.find_all('iframe', src=True):
                    src = iframe['src']
                    full_src = urljoin(url, src)
                    if "youtube.com" in full_src or "youtu.be" in full_src:
                        if full_src not in self.visited:
                            self.process_youtube(full_src)
                            self.visited.add(full_src)

                time.sleep(0.5)

            except Exception as e:
                print(f"Error processing {url}: {e}")

if __name__ == "__main__":
    scraper = WebScraper("https://pantelis.github.io/courses/ai/")
    scraper.scrape()
