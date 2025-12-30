from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import sys
import traceback

# 안전하게 라이브러리 임포트
try:
    import youtube_transcript_api
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    youtube_transcript_api = None
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. CORS 설정 (필수)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 2. 라이브러리 설치 확인 (디버깅용)
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Library Error',
                'detail': '라이브러리가 설치되지 않았습니다. requirements.txt가 api 폴더 안에 있는지 확인하세요.'
            }, ensure_ascii=False).encode('utf-8'))
            return

        try:
            # 3. URL에서 Video ID 추출
            query = urlparse(self.path).query
            params = parse_qs(query)
            video_id = params.get('videoId', [None])[0]

            if not video_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Video ID is required'}).encode('utf-8'))
                return

            print(f"Fetching transcript for: {video_id}")

            # 4. 자막 가져오기 (한국어 -> 영어 -> 자동생성 순)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'en-US', 'ja'])
            
            # 5. 텍스트 합치기
            full_text = " ".join([t['text'] for t in transcript_list])
            
            # 6. 성공 응답
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 에러 처리
            error_msg = str(e)
            print(f"ERROR: {error_msg}")
            
            if "TranscriptsDisabled" in error_msg:
                status_code = 404
                client_msg = "이 영상은 자막을 제공하지 않습니다."
            elif "NoTranscriptFound" in error_msg:
                status_code = 404
                client_msg = "지원하는 언어(한국어/영어)의 자막이 없습니다."
            else:
                status_code = 500
                client_msg = f"서버 오류: {error_msg}"

            self.send_response(status_code)
            self.end_headers()
            self.wfile.write(json.dumps({'error': client_msg, 'detail': error_msg}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
