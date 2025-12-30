from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

# 안전한 임포트 (충돌 방지)
try:
    import youtube_transcript_api
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. CORS 헤더 (필수)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 2. 라이브러리 설치 체크
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': '라이브러리 설치 실패: requirements.txt를 확인하세요.'}, ensure_ascii=False).encode('utf-8'))
            return

        try:
            # 3. URL 파싱
            query = urlparse(self.path).query
            params = parse_qs(query)
            video_id = params.get('videoId', [None])[0]

            if not video_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Video ID required'}).encode('utf-8'))
                return

            # 4. 자막 가져오기
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'en-US'])
            full_text = " ".join([t['text'] for t in transcript_list])
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 5. 에러 처리
            self.send_response(500)
            self.end_headers()
            error_msg = str(e)
            
            # 사용자에게 보여줄 친절한 메시지
            if "TranscriptsDisabled" in error_msg:
                client_msg = "자막이 없는 영상입니다."
            elif "NoTranscriptFound" in error_msg:
                client_msg = "한국어/영어 자막을 찾을 수 없습니다."
            else:
                client_msg = f"서버 에러: {error_msg}"
                
            self.wfile.write(json.dumps({'error': client_msg, 'detail': error_msg}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
