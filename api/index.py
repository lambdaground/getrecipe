from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        # 외부 라이브러리 없이 순수 파이썬만으로 응답
        self.wfile.write(json.dumps({
            "status": "Alive",
            "message": "파이썬 서버가 정상 작동 중입니다!"
        }).encode('utf-8'))
