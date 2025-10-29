from fastapi import APIRouter, UploadFile, File, Form
import os
from app.utils.helpers import upload_video, save_analysis_result

router = APIRouter()

@router.post("/", summary="Submit Report")
async def submit_report(
    user_id: str = Form(..., description="사용자 ID (예: testuser)"),
    video: UploadFile = File(..., description="업로드할 동영상 파일")
):
    try:
        # 윈도우 호환 임시 저장 디렉토리
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, video.filename)

        with open(temp_path, "wb") as buffer:
            buffer.write(await video.read())

        video_url = upload_video(temp_path, user_id)
        save_analysis_result(video.filename, {"user_id": user_id, "video_url": video_url})
        return {"message": "업로드 성공", "video_url": video_url}
    except Exception as e:
        return {"error": str(e)}
