// api/transcript.js
const { YoutubeTranscript } = require('youtube-transcript');

export default async function handler(req, res) {
  // CORS 설정 (필수)
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // OPTIONS 요청 처리 (브라우저 사전 검사)
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { videoId } = req.query;

  if (!videoId) {
    return res.status(400).json({ error: 'Video ID is required' });
  }

  try {
    console.log(`Fetching transcript for: ${videoId}`);

    // 1. 자막 가져오기 시도
    // lang을 지정하지 않으면 자동으로 가능한 언어를 가져옵니다.
    const transcriptList = await YoutubeTranscript.fetchTranscript(videoId);

    if (!transcriptList || transcriptList.length === 0) {
      throw new Error("Empty transcript");
    }

    // 2. 텍스트 합치기
    const fullText = transcriptList.map((item) => item.text).join(' ');

    // 3. 성공 응답
    return res.status(200).json({ text: fullText });

  } catch (error) {
    console.error('Transcript Error Detail:', error);

    // 에러 종류별 메시지 처리
    if (error.message.includes('Transcript is disabled')) {
      return res.status(404).json({ error: '이 영상에는 자막(CC)이 없습니다.' });
    }
    
    // 그 외 서버 에러
    return res.status(500).json({ 
      error: '자막을 가져오는 중 오류가 발생했습니다.',
      details: error.message 
    });
  }
}
