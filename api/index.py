from http.server import BaseHTTPRequestHandler
import json
import traceback

# 라이브러리 임포트를 try-except로 감싸서, 없으면 에러 메시지를 보여주게 함
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 라이브러리 설치 실패 시 500 에러 대신 친절한 메시지 출력
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'CRITICAL: youtube_transcript_api 라이브러리가 설치되지 않았습니다. requirements.txt를 확인하세요.'}, ensure_ascii=False).encode('utf-8'))
            return

            print(f"Attempting to fetch transcript for: {video_id}") # 로그 남기기

            # 자막 가져오기 (언어 순서 중요)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'en-US', 'ja'])
            
            full_text = " ".join([t['text'] for t in transcript_list])
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 상세 에러를 Vercel 로그(Function Logs)에 출력
            error_trace = traceback.format_exc()
            print(f"ERROR: {error_trace}")

            error_msg = str(e)
            
            if "TranscriptsDisabled" in error_msg:
                status_code = 404
                client_msg = "자막이 비활성화된 영상입니다."
            elif "NoTranscriptFound" in error_msg:
                status_code = 404
                client_msg = "지원되는 언어(한국어/영어) 자막이 없습니다."
            elif "Cookies" in error_msg or "Sign in" in error_msg:
                 status_code = 403
                 client_msg = "유튜브에서 봇 접근을 차단했습니다. (쿠키 필요)"
            else:
                status_code = 500
                client_msg = f"서버 내부 오류: {error_msg}"

            self.send_response(status_code)
            self.end_headers()
            self.wfile.write(json.dumps({'error': client_msg, 'detail': error_msg}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
