from fastapi import APIRouter, UploadFile, File, Form
import os, uuid
from concurrent.futures import ProcessPoolExecutor
from app.services.video_processing import extract_frames
from app.services.deepfake_detector import predict_image
from app.utils.helpers import save_analysis_result

router = APIRouter()

# 전역 함수 (멀티프로세싱에서 호출 가능)
def analyze_single_frame(frame):
    return {**predict_image(frame["path"]), "time": frame["time"]}

def analyze_frames_in_parallel(frames):
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(analyze_single_frame, frames))
    return results

@router.post("/", summary="Analyze Video")
async def analyze_video(user_id: str = Form(...), video: UploadFile = File(...)):
    try:
        # 임시 저장
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        video_path = os.path.join(temp_dir, video.filename)
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())

        # 프레임 추출 (path + time)
        frame_dir = os.path.join(temp_dir, f"{video.filename}_frames")
        frames = extract_frames(video_path, frame_dir, frame_rate=0.2)
        if not frames:
            raise Exception("프레임 추출 실패: 영상이 비어있거나 지원되지 않는 형식입니다.")

        # 병렬 프레임 분석
        results = analyze_frames_in_parallel(frames)

        # 평균 확률 계산
        fake_conf = sum(r["confidence"] for r in results if r["ensemble_result"] == "FAKE") / len(results)
        real_conf = sum(r["confidence"] for r in results if r["ensemble_result"] == "REAL") / len(results)
        final_label = "FAKE" if fake_conf > real_conf else "REAL"

        # 결과 데이터
        result_data = {
            "video": video.filename,
            "frames_analyzed": len(frames),
            "final_label": final_label,
            "average_fake_confidence": round(fake_conf, 4),
            "average_real_confidence": round(real_conf, 4),
            "frame_results": results,
            "user_id": user_id
        }

        # Firestore 저장
        video_id = f"{video.filename}-{uuid.uuid4()}"
        save_analysis_result(video_id, result_data)

        return {"video_id": video_id, **result_data}

    except Exception as e:
        return {"error": str(e)}
