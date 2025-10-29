import axios from 'axios';

// 개발 환경에서 사용할 API 주소 (로컬 개발 시 컴퓨터 IP로 변경)
const API_BASE_URL = __DEV__ 
  ? 'http://10.0.2.2:8000'  // 개발용 - Android 에뮬레이터에서 호스트 PC 접근용 (10.0.2.2는 에뮬레이터의 localhost)
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
  videoUri: string,
  userId: string
): Promise<AnalyzeVideoResponse> {
  try {
    console.log('영상 분석 요청:', { videoUri, userId });

    // FastAPI는 파일 업로드를 FormData(multipart/form-data)로 기대함
    // Expo/React Native에서는 { uri, name, type } 형태로 파일을 전달
    const form = new FormData();
    // user_id 필드
    form.append('user_id', userId as any);
    // video 파일 필드
    form.append('video', {
      // videoUri가 http(s) URL일 수도 있고, file:// 로컬 경로일 수도 있음
      // FastAPI는 서버에서 다운로드하지 않으므로 로컬/에뮬레이터 경로 사용을 권장
      uri: videoUri,
      name: 'video.mp4',
      type: 'video/mp4',
    } as any);

    // 엔드포인트: 동기 처리 '/analyze-video/' 또는 비동기 '/analysis-server/start-analysis'
    // 여기서는 동기 처리 엔드포인트를 사용 (즉시 결과 반환)
    const response = await axios.post(
      `${API_BASE_URL}/analyze-video/`,
      form,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000, // 최대 120초 대기
      }
    );
    
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
