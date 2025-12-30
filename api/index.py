from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import sys

# 라이브러리 안전 임포트
try:
    import youtube_transcript_api
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. CORS 설정
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 2. 라이브러리 설치 확인 (에러 진단용)
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Library Error',
                'detail': '라이브러리가 설치되지 않았습니다. requirements.txt가 최상위 폴더에 있는지 확인하세요.'
            }, ensure_ascii=False).encode('utf-8'))
            return

        try:
            # 3. URL 파싱
            query = urlparse(self.path).query
            params = parse_qs(query)
            video_id = params.get('videoId', [None])[0]

            if not video_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Video ID is required'}).encode('utf-8'))
                return

            print(f"Fetching: {video_id}")

            # 4. 자막 가져오기
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'en-US', 'ja'])
            full_text = " ".join([t['text'] for t in transcript_list])
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 5. 에러 처리
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Server Error', 'detail': str(e)}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
