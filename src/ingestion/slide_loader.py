import requests
import io
from pypdf import PdfReader

class SlideLoader:
    def __init__(self):
        pass

    def load_pdf(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch PDF {url}: {response.status_code}")
                return None

            f = io.BytesIO(response.content)
            reader = PdfReader(f)
            
            text_content = ""
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                text_content += f"\n--- Page {i+1} ---\n{text}"
                pages.append({"page": i+1, "text": text})
            
            return {
                "pages": pages,
                "text": text_content
            }
        except Exception as e:
            print(f"Error processing PDF {url}: {e}")
            return None
