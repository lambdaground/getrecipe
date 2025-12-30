from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import traceback

# 1. 라이브러리 설치 여부 확인 (안전장치)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 2. 헤더 설정 (CORS 허용)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 3. 라이브러리가 없으면 500 에러 대신 안내 메시지 출력
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Configuration Error',
                'detail': 'youtube_transcript_api 라이브러리가 설치되지 않았습니다. requirements.txt 파일을 확인하세요.'
            }, ensure_ascii=False).encode('utf-8'))
            return

        # 4. 핵심 로직 시작 (try 블록 필수)
        try:
            # URL 파싱
            query = urlparse(self.path).query
            params = parse_qs(query)
            video_id = params.get('videoId', [None])[0]

            if not video_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Video ID is required'}).encode('utf-8'))
                return

            print(f"Fetching: {video_id}")

            # 자막 가져오기
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'en-US', 'ja'])
            
            # 텍스트 합치기
            full_text = " ".join([t['text'] for t in transcript_list])
            
            # 성공 응답 (200)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 에러 핸들링 (여기가 line 35 근처)
            error_trace = traceback.format_exc()
            print(f"ERROR: {error_trace}")

            error_msg = str(e)
            
            if "TranscriptsDisabled" in error_msg:
                status_code = 404
                client_msg = "자막이 비활성화된 영상입니다."
            elif "NoTranscriptFound" in error_msg:
                status_code = 404
                client_msg = "지원되는 언어(한국어/영어) 자막이 없습니다."
            else:
                status_code = 500
                client_msg = f"서버 오류: {error_msg}"

            self.send_response(status_code)
            self.end_headers()
            self.wfile.write(json.dumps({'error': client_msg, 'detail': error_msg}, ensure_ascii=False).encode('utf-8'))

    # 브라우저 사전 요청(OPTIONS) 처리
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
