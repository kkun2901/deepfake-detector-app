from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import analyze_video, submit_report, report_download, model_guide, analyze_video_optimized, analysis_server

app = FastAPI(
    title="Deepfake Detection API",
    version="1.0.0",
    description="Video & Audio-based Deepfake Detection with Report Generation"
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서 접근 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 라우터 등록
app.include_router(analyze_video.router, prefix="/analyze-video", tags=["Analysis"])
app.include_router(analysis_server.router, prefix="/analysis-server", tags=["Analysis Server"])
app.include_router(analyze_video_optimized.router, prefix="/analyze-video-optimized", tags=["Analysis (Optimized)"])
app.include_router(submit_report.router, prefix="/submit-report", tags=["Reports"])
app.include_router(report_download.router, prefix="/download-report", tags=["Reports"])
app.include_router(model_guide.router, prefix="/model-guide", tags=["Model Development"])

@app.get("/")
def root():
    return {"message": "Deepfake Detection API Running"}

