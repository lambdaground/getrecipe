from http.server import BaseHTTPRequestHandler
import json
import sys
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        result = {}
        
        try:
            # 라이브러리 임포트 시도
            import youtube_transcript_api
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # 여기가 핵심! 파이썬이 읽은 파일의 진짜 위치를 알아냄
            loaded_file_path = getattr(youtube_transcript_api, '__file__', '알 수 없음')
            
            result = {
                "상태": "임포트 성공 (그러나 기능이 없는 가짜일 수 있음)",
                "범인_파일_위치": loaded_file_path,  # 이 경로가 중요합니다!
                "현재_폴더_파일들": os.listdir('.'),   # 현재 폴더에 무슨 파일이 있는지 확인
                "YouTubeTranscriptApi_내용물": str(dir(YouTubeTranscriptApi)) # get_transcript가 있는지 확인
            }
            
        except ImportError as e:
            result = {
                "상태": "임포트 실패",
                "에러_내용": str(e),
                "현재_폴더_위치": os.getcwd(),
                "현재_폴더_파일들": os.listdir('.')
            }
        except Exception as e:
            result = {
                "상태": "알 수 없는 에러",
                "에러_내용": str(e)
            }
            
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))
