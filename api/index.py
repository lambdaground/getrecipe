from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import sys
import os

# 1. 라이브러리 임포트 (경로 확인용 디버깅 포함)
try:
    import youtube_transcript_api
    from youtube_transcript_api import YouTubeTranscriptApi
    
    # [중요] 라이브러리가 어디서 로딩됐는지 확인
    lib_path = youtube_transcript_api.__file__
    print(f"DEBUG: Loaded library from {lib_path}")
    
except ImportError:
    YouTubeTranscriptApi = None
    lib_path = "Not Installed"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')

        # 2. 라이브러리 상태 체크
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': '라이브러리 미설치'}, ensure_ascii=False).encode('utf-8'))
            return

        # 3. [핵심] 가짜 파일 감지 로직
        # 만약 로딩된 경로에 'api'라는 글자가 포함되어 있으면, 님이 만든 파일임 -> 에러 발생시킴
        if "api/youtube_transcript_api.py" in lib_path or "api\\youtube_transcript_api.py" in lib_path:
             self.send_response(500)
             self.end_headers()
             msg = {
                 "error": "치명적 오류: 파일 이름 충돌",
                 "detail": f"api 폴더 안에 youtube_transcript_api.py 파일이 있습니다. 제발 지워주세요! (현재 위치: {lib_path})"
             }
             self.wfile.write(json.dumps(msg, ensure_ascii=False).encode('utf-8'))
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

            # 4. 자막 가져오기 (list_transcripts 사용)
            # 여기가 실행된다는 건 진짜 라이브러리를 불러왔다는 뜻입니다.
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['ko'])
            except:
                try:
                    transcript = transcript_list.find_transcript(['en'])
                except:
                    for t in transcript_list:
                        transcript = t
                        break
            
            final_data = transcript.fetch()
            full_text = " ".join([t['text'] for t in final_data])
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except AttributeError as e:
            # 여전히 AttributeError가 난다면...
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'AttributeError 발생', 
                'detail': '여전히 가짜 파일을 읽고 있습니다. api 폴더를 삭제하고 다시 만드세요.',
                'loaded_path': lib_path
            }, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()
