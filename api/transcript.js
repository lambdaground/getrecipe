
// api/transcript.js
const { YoutubeTranscript } = require('youtube-transcript');

export default async function handler(req, res) {
  // CORS 설정 (다른 곳에서 요청해도 허용)
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');

  const { videoId } = req.query;

  if (!videoId) {
    return res.status(400).json({ error: 'Video ID is required' });
  }

  try {
    // 유튜브 자막 가져오기 (한국어 우선, 없으면 영어)
    const transcriptList = await YoutubeTranscript.fetchTranscript(videoId, {
      lang: 'ko', 
    }).catch(() => {
        // 한국어 실패시 영어 시도 혹은 자동생성 가져오기
        return YoutubeTranscript.fetchTranscript(videoId);
    });

    if (!transcriptList || transcriptList.length === 0) {
      return res.status(404).json({ error: 'No transcript found' });
    }

    // 자막 텍스트만 합치기
    const fullText = transcriptList.map((item) => item.text).join(' ');

    res.status(200).json({ text: fullText });
  } catch (error) {
    console.error('Transcript Error:', error);
    res.status(500).json({ error: 'Failed to fetch transcript. (자막이 없는 영상일 수 있습니다)' });
  }
}
