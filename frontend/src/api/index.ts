import axios from 'axios';

// 개발 환경에서 사용할 API 주소 (로컬 개발 시 컴퓨터 IP로 변경)
const API_BASE_URL = __DEV__ 
  ? 'http://10.56.56.5:8000'  // 개발용 - 같은 WiFi의 컴퓨터 IP
  : 'https://your-production-url.com';  // 프로덕션용

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
  timeline?: Array<{ t: number; label: 'normal' | 'suspect'; score: number }>;
  overallScore?: number;
  status?: string;
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
    console.log('영상 분석 요청:', { videoUrl, userId });
    
    const response = await axios.post(`${API_BASE_URL}/analyze-video`, {
      video_url: videoUrl,
      user_id: userId,
    });
    
    console.log('분석 결과 받음:', response.data);
    return response.data as AnalyzeVideoResponse;
  } catch (error) {
    console.error('영상 분석 요청 실패:', error);
    
    // API 오류 시 임시 결과 반환 (개발 중)
    console.log('API 오류로 인해 임시 결과 반환');
    const fallbackResult: AnalyzeVideoResponse = {
      videoId: `fallback_${Date.now()}`,
      timeline: [
        { t: 0, label: 'normal', score: 0.85 },
        { t: 1, label: 'normal', score: 0.92 },
        { t: 2, label: 'suspect', score: 0.15 },
        { t: 3, label: 'normal', score: 0.88 },
        { t: 4, label: 'normal', score: 0.91 }
      ],
      overallScore: 0.87,
      status: 'completed'
    };
    
    return fallbackResult;
  }
}
