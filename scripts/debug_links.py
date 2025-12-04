import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://pantelis.github.io/courses/ai/syllabus/index.html"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print(f"Links found on {url}:")
for link in soup.find_all('a', href=True):
    href = link['href']
    full_url = urljoin(url, href)
    print(f" - Href: {href} -> Full: {full_url}")
