from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

class YouTubeLoader:
    def __init__(self):
        pass

    def extract_video_id(self, url):
        query = urlparse(url)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return None

    def get_transcript(self, url):
        video_id = self.extract_video_id(url)
        if not video_id:
            print(f"Could not extract video ID from {url}")
            return None

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([t['text'] for t in transcript_list])
            return {
                "video_id": video_id,
                "transcript": transcript_list,
                "text": full_text
            }
        except Exception as e:
            print(f"Error fetching transcript for {url}: {e}")
            return None
