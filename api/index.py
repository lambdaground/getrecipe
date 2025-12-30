from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import sys
import os

# [핵심] 유령 폴더 차단 (Exorcism Code)
# 파이썬이 라이브러리를 찾을 때 '_vendor' 폴더는 아예 쳐다보지 말라고 명령합니다.
sys.path = [p for p in sys.path if "_vendor" not in p]

# 이제 안전하게 임포트 시도
try:
    import youtube_transcript_api
    from youtube_transcript_api import YouTubeTranscriptApi
    
    # 확인용: 이제 어디서 로딩되는지 봅시다. (/var/lang/lib/... 이어야 정상)
    lib_path = youtube_transcript_api.__file__
    
except ImportError:
    YouTubeTranscriptApi = None
    lib_path = "Not Installed"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')

        # 디버깅: 라이브러리 위치 출력 (성공하면 나중에 지워도 됨)
        print(f"DEBUG: Library loaded from {lib_path}")

        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': '라이브러리 미설치'}, ensure_ascii=False).encode('utf-8'))
            return

        # 여전히 _vendor에서 로딩된다면 에러 띄움
        if "_vendor" in lib_path:
             self.send_response(500)
             self.end_headers()
             self.wfile.write(json.dumps({
                 'error': '캐시 문제 발생', 
                 'detail': 'Vercel 캐시가 옛날 파일을 붙잡고 있습니다. Vercel 대시보드에서 Redeploy를 해야 합니다.',
                 'path': lib_path
             }, ensure_ascii=False).encode('utf-8'))
             return

        try:
            query = urlparse(self.path).query
            params = parse_qs(query)
            video_id = params.get('videoId', [None])[0]

            if not video_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Video ID required'}).encode('utf-8'))
                return

            # 자막 가져오기 (list_transcripts 기능 사용)
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            # 한국어 -> 영어 -> 자동생성 순서
            try: transcript = transcript_list.find_transcript(['ko'])
            except: 
                try: transcript = transcript_list.find_transcript(['en'])
                except: 
                    # 자동생성된 자막이라도 가져옴
                    for t in transcript_list:
                        transcript = t
                        break
            
            if not transcript:
                raise Exception("자막을 찾을 수 없습니다.")

            final_data = transcript.fetch()
            full_text = " ".join([t['text'] for t in final_data])
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e), 'path': lib_path}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()
