from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import traceback
import sys

# [수정된 부분] 임포트 방식 변경 및 디버깅 코드 추가
try:
    import youtube_transcript_api
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    youtube_transcript_api = None
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 1. 라이브러리 로드 실패 시 디버깅 정보 출력
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Library Error',
                'detail': 'youtube_transcript_api 모듈을 불러오지 못했습니다. requirements.txt를 확인하세요.',
                'sys_path': str(sys.path)
            }, ensure_ascii=False).encode('utf-8'))
            return

        try:
            query = urlparse(self.path).query
            params = parse_qs(query)
            video_id = params.get('videoId', [None])[0]

            if not video_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Video ID is required'}).encode('utf-8'))
                return

            print(f"Fetching: {video_id}")
            
            # [디버깅] 현재 로드된 라이브러리 위치 확인 (로그용)
            print(f"Loaded Library: {youtube_transcript_api.__file__}")

            # 2. 자막 가져오기 (메서드 호출 방식)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'en-US', 'ja'])
            
            full_text = " ".join([t['text'] for t in transcript_list])
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except AttributeError as e:
            # "get_transcript" 속성 에러가 날 경우 처리
            error_trace = traceback.format_exc()
            print(f"ATTRIBUTE ERROR: {error_trace}")
            
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Name Collision Error', 
                'detail': '프로젝트 내부에 youtube_transcript_api.py 라는 파일이 있어서 충돌이 발생했습니다. 해당 파일을 삭제하세요.',
                'python_error': str(e)
            }, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
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

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
