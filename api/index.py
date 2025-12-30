from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import traceback

# 라이브러리 임포트
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
except ImportError:
    YouTubeTranscriptApi = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. CORS 및 헤더 설정
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 2. 라이브러리 설치 확인
        if YouTubeTranscriptApi is None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Library Error', 'detail': 'requirements.txt가 최상위 폴더에 있는지 확인하세요.'}, ensure_ascii=False).encode('utf-8'))
            return

        try:
            # 3. URL 파싱
            query = urlparse(self.path).query
            params = parse_qs(query)
            video_id = params.get('videoId', [None])[0]

            if not video_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Video ID required'}).encode('utf-8'))
                return

            print(f"Fetching transcript for: {video_id}")

            # 4. 자막 가져오기 (강력한 모드)
            # list_transcripts()를 사용하면 수동/자동 자막을 모두 탐색합니다.
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            
            # (1) 한국어 자막 시도 (수동 -> 자동 순)
            try:
                transcript = transcript_list.find_transcript(['ko'])
            except:
                # (2) 영어 자막 시도
                try:
                    transcript = transcript_list.find_transcript(['en', 'en-US'])
                except:
                    # (3) 그것도 없으면 '자동 생성된' 아무 자막이나 가져오기
                    try:
                        # 그냥 첫 번째로 잡히는거 아무거나 가져옴 (보통 해당 영상의 원어)
                        for t in transcript_list:
                            transcript = t
                            break
                    except:
                        pass
            
            if not transcript:
                raise Exception("사용 가능한 자막을 찾을 수 없습니다.")

            # 5. 자막 데이터 가져와서 텍스트로 변환
            # (만약 한국어가 아니면 한국어로 번역해서 가져오기 시도)
            if transcript.language_code != 'ko':
                try:
                    transcript = transcript.translate('ko')
                except:
                    pass # 번역 실패하면 그냥 원문 사용

            final_data = transcript.fetch()
            
            # 텍스트만 깔끔하게 합치기
            formatter = TextFormatter()
            text_formatted = formatter.format_transcript(final_data)
            
            # 줄바꿈 문자를 공백으로 변경
            full_text = text_formatted.replace('\n', ' ')

            # 6. 성공 응답
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'text': full_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 에러 로그 출력
            error_trace = traceback.format_exc()
            print(f"ERROR: {error_trace}")
            
            error_msg = str(e)
            client_msg = f"자막 오류: {error_msg}"
            
            # 구체적인 에러 메시지 처리
            if "TranscriptsDisabled" in error_msg:
                client_msg = "이 영상은 자막 기능이 꺼져 있습니다."
            elif "NoTranscriptFound" in error_msg:
                client_msg = "이 영상에는 자막이 없습니다."
            elif "Cookies" in error_msg or "Sign in" in error_msg:
                client_msg = "유튜브가 Vercel 서버의 접근을 차단했습니다. (쿠키 필요)"

            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': client_msg, 'detail': error_msg}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
