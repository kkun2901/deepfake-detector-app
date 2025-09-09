from app.core.firebase import db, bucket
import uuid

def upload_video(file_path: str, user_id: str):
    """Firebase Storage에 영상 업로드 후 URL 반환"""
    blob_name = f"videos/{user_id}/{uuid.uuid4()}.mp4"
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    blob.make_public()
    return blob.public_url

def save_analysis_result(video_id: str, result: dict):
    """분석 결과 Firestore 저장"""
    db.collection("analysis_results").document(video_id).set(result)
    return True

def get_analysis_result(video_id: str):
    """저장된 분석 결과 Firestore에서 조회"""
    doc = db.collection("analysis_results").document(video_id).get()
    if doc.exists:
        return doc.to_dict()
    return None
