from http.server import BaseHTTPRequestHandler
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
import json
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. CORS 및 헤더 설정 (필수)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 2. 쿼리 파라미터에서 videoId 추출
        query = urlparse(self.path).query
        params = parse_qs(query)
        video_id = params.get('videoId', [None])[0]

        if not video_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Video ID required'}).encode('utf-8'))
            return

        try:
            # 3. 자막 가져오기 (한국어 -> 영어 순으로 시도)
            # Python 라이브러리는 '자동 생성 자막'도 아주 잘 가져옵니다.
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'en-US'])
            
            # 4. 텍스트만 합치기
            full_text = " ".join([t['text'] for t in transcript_list])
            
            # 성공 응답
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 에러 처리
            error_msg = str(e)
            print(f"Error fetching transcript: {error_msg}")
            
            if "TranscriptsDisabled" in error_msg:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({'error': '자막이 비활성화된 영상입니다.'}, ensure_ascii=False).encode('utf-8'))
            elif "NoTranscriptFound" in error_msg:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({'error': '한국어 또는 영어 자막을 찾을 수 없습니다.'}, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'서버 오류: {error_msg}'}, ensure_ascii=False).encode('utf-8'))

    # 브라우저 사전 요청(OPTIONS) 처리
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()
