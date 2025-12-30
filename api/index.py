from http.server import BaseHTTPRequestHandler
import json
import pkg_resources

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 현재 설치된 모든 라이브러리 목록 가져오기
        installed_packages = [f"{d.project_name}=={d.version}" for d in pkg_resources.working_set]
        
        # youtube-transcript-api가 목록에 있는지 확인
        is_installed = any("youtube-transcript-api" in pkg.lower() for pkg in installed_packages)

        result = {
            "상태": "서버 연결 성공 (Alive)",
            "라이브러리_설치_여부": "✅ 설치됨" if is_installed else "❌ 설치 안 됨 (이게 원인!)",
            "설치된_라이브러리_전체": installed_packages
        }

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))
