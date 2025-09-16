import axios from 'axios';

const API_BASE_URL = 'http://10.56.56.21:8000'; // 실제 주소로 바꿔줘

export interface TimelineItem {
  start: number;
  end: number;
  ensemble_result: 'real' | 'fake';
  confidence: number;
}

export interface AnalysisResultResponse {
  videoId: string;
  timeline: TimelineItem[];
}

export interface AnalyzeVideoResponse {
  videoId: string;
}

export async function fetchAnalysisResult(videoId: string): Promise<AnalysisResultResponse> {
  try {
    const response = await axios.get(`${API_BASE_URL}/get-result/${videoId}`);
    return response.data as AnalysisResultResponse;
  } catch (error) {
    console.error('분석 결과 조회 실패:', error);
    throw error;
  }
}

export async function analyzeVideo(
  videoUrl: string,
  userId: string
): Promise<AnalyzeVideoResponse> {
  try {
    const response = await axios.post(`${API_BASE_URL}/analyze-video`, {
      video_url: videoUrl,
      user_id: userId,
    });
    return response.data as AnalyzeVideoResponse;
  } catch (error) {
    console.error('영상 분석 요청 실패:', error);
    throw error;
  }
}
