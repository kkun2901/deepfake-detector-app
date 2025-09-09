from fastapi import FastAPI
from app.api.endpoints import analyze_video, get_result, submit_report, report_download

app = FastAPI(
    title="Deepfake Detection API",
    version="1.0.0",
    description="Video & Audio-based Deepfake Detection with Report Generation"
)

# 라우터 등록
app.include_router(analyze_video.router, prefix="/analyze-video", tags=["Analysis"])
app.include_router(get_result.router, prefix="/get-result", tags=["Result"])
app.include_router(submit_report.router, prefix="/submit-report", tags=["Reports"])
app.include_router(report_download.router, prefix="/download-report", tags=["Reports"])

@app.get("/")
def root():
    return {"message": "Deepfake Detection API Running"}
