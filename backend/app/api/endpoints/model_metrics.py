from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def model_metrics():
    return {"precision": 0.92, "recall": 0.91, "f1_score": 0.91}
