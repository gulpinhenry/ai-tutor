from langchain.text_splitter import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_document(self, doc):
        doc_type = doc.get('type', 'web_page')
        
        if doc_type == 'slide':
            return self.chunk_slide(doc)
        elif doc_type == 'video':
            return self.chunk_video(doc)
        else:
            return self.chunk_web(doc)

    def chunk_slide(self, doc):
        chunks = []
        pages = doc.get('metadata', {}).get('pages', [])
        for page in pages:
            text = page.get('text', '')
            page_num = page.get('page')
            if text.strip():
                sub_chunks = self.splitter.split_text(text)
                for sub in sub_chunks:
                    chunks.append({
                        "text": sub,
                        "metadata": {"source": doc['url'], "type": "slide", "span": str(page_num)}
                    })
        return chunks

    def chunk_video(self, doc):
        chunks = []
        transcript = doc.get('metadata', {}).get('transcript', [])
        
        current_chunk_text = []
        current_length = 0
        start_time = None
        
        for segment in transcript:
            text = segment.get('text', '')
            start = segment.get('start')
            duration = segment.get('duration')
            
            if start_time is None:
                start_time = start
            
            current_chunk_text.append(text)
            current_length += len(text)
            
            if current_length >= self.splitter._chunk_size:
                end_time = start + duration
                chunk_text = " ".join(current_chunk_text)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": doc['url'], 
                        "type": "video", 
                        "span": f"{start_time:.2f}-{end_time:.2f}",
                        "start": start_time,
                        "end": end_time
                    }
                })
                current_chunk_text = []
                current_length = 0
                start_time = None
        
        if current_chunk_text:
            chunk_text = " ".join(current_chunk_text)
            last_seg = transcript[-1]
            end_time = last_seg['start'] + last_seg['duration']
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source": doc['url'], 
                    "type": "video", 
                    "span": f"{start_time:.2f}-{end_time:.2f}",
                    "start": start_time,
                    "end": end_time
                }
            })
            
        return chunks

    def chunk_web(self, doc):
        text = doc.get('content', '')
        raw_chunks = self.splitter.split_text(text)
        return [{
            "text": c,
            "metadata": {"source": doc['url'], "type": "web_page", "span": None}
        } for c in raw_chunks]

    def chunk_text(self, text):
        return self.splitter.split_text(text)
