from fastapi import APIRouter
from app.utils.helpers import get_analysis_result

router = APIRouter()

@router.get("/{video_id}", summary="Get Analysis Result")
async def get_result(video_id: str):
    result = get_analysis_result(video_id)
    if result:
        return result
    return {"error": "결과를 찾을 수 없습니다."}
