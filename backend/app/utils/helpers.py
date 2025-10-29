from app.core.firebase import db, bucket
import uuid
from typing import List, Dict, Any
from datetime import datetime

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

def create_smart_timeline(frame_results: List[Dict], min_segment_duration: float = 2.0) -> List[Dict]:
    """
    프레임 결과를 스마트하게 구간화하여 타임라인 생성
    
    Args:
        frame_results: 프레임별 분석 결과 리스트
        min_segment_duration: 최소 구간 길이 (초)
    
    Returns:
        구간화된 타임라인 리스트
    """
    if not frame_results:
        return []
    
    timeline = []
    current_segment = None
    segment_id = 1
    
    for i, frame in enumerate(frame_results):
        frame_time = frame.get("time", 0.0)
        frame_result = frame.get("ensemble_result", "UNKNOWN")
        frame_confidence = frame.get("confidence", 0.0)
        
        # 첫 번째 프레임이거나 구간을 분할해야 하는 경우
        if (current_segment is None or 
            should_split_segment(current_segment, frame_result, frame_time, min_segment_duration)):
            
            # 이전 구간이 있으면 완료
            if current_segment:
                timeline.append(current_segment)
            
            # 새 구간 시작
            current_segment = {
                "segment_id": segment_id,
                "start": frame_time,
                "end": frame_time,
                "duration": 0.0,
                "result": frame_result,
                "confidence": frame_confidence,
                "frame_count": 1,
                "frames": [frame]
            }
            segment_id += 1
        else:
            # 현재 구간에 프레임 추가
            current_segment["end"] = frame_time
            current_segment["duration"] = current_segment["end"] - current_segment["start"]
            current_segment["frame_count"] += 1
            current_segment["frames"].append(frame)
            
            # 신뢰도 업데이트 (평균)
            total_confidence = sum(f.get("confidence", 0.0) for f in current_segment["frames"])
            current_segment["confidence"] = round(total_confidence / current_segment["frame_count"], 4)
    
    # 마지막 구간 추가
    if current_segment:
        timeline.append(current_segment)
    
    return timeline

def should_split_segment(current_segment: Dict, new_result: str, new_time: float, min_duration: float) -> bool:
    """
    새로운 구간을 시작해야 하는지 판단
    
    Args:
        current_segment: 현재 구간 정보
        new_result: 새로운 프레임의 결과
        new_time: 새로운 프레임의 시간
        min_duration: 최소 구간 길이
    
    Returns:
        구간을 분할해야 하면 True
    """
    # 결과가 다르면 분할
    if current_segment["result"] != new_result:
        return True
    
    # 최소 구간 길이를 고려한 분할 로직
    current_duration = new_time - current_segment["start"]
    
    # 너무 긴 구간은 분할 (선택적)
    if current_duration > 30.0:  # 30초 이상이면 분할
        return True
    
    return False

def create_analysis_summary(video_analysis: Dict, audio_analysis: Dict, timeline: List[Dict]) -> Dict:
    """
    분석 결과 요약 정보 생성
    
    Args:
        video_analysis: 비디오 분석 결과
        audio_analysis: 오디오 분석 결과
        timeline: 타임라인 구간 리스트
    
    Returns:
        요약 정보 딕셔너리
    """
    total_duration = max(segment["end"] for segment in timeline) if timeline else 0.0
    total_frames = sum(segment["frame_count"] for segment in timeline)
    
    # 전체 결과 결정 (다수결)
    fake_segments = sum(1 for segment in timeline if segment["result"] == "FAKE")
    real_segments = sum(1 for segment in timeline if segment["result"] == "REAL")
    
    overall_result = "FAKE" if fake_segments > real_segments else "REAL"
    
    # 전체 신뢰도 계산
    if timeline:
        total_confidence = sum(segment["confidence"] for segment in timeline)
        overall_confidence = round(total_confidence / len(timeline), 4)
    else:
        overall_confidence = 0.0
    
    return {
        "overall_result": overall_result,
        "overall_confidence": overall_confidence,
        "total_duration": total_duration,
        "total_segments": len(timeline),
        "total_frames_analyzed": total_frames,
        "analysis_method": "video_audio_ensemble",
        "fake_segments": fake_segments,
        "real_segments": real_segments
    }

def create_segment_analysis_details(segment: Dict, video_analysis: Dict, audio_analysis: Dict) -> Dict:
    """
    구간별 상세 분석 정보 생성
    
    Args:
        segment: 구간 정보
        video_analysis: 비디오 분석 결과
        audio_analysis: 오디오 분석 결과
    
    Returns:
        구간별 상세 분석 정보
    """
    # 구간 내 프레임들의 비디오 분석 결과 집계
    segment_frames = segment.get("frames", [])
    
    if segment_frames:
        # 비디오 분석 세부사항
        video_details = {
            "fake_confidence": round(sum(f.get("confidence", 0.0) for f in segment_frames if f.get("ensemble_result") == "FAKE") / len(segment_frames), 4),
            "real_confidence": round(sum(f.get("confidence", 0.0) for f in segment_frames if f.get("ensemble_result") == "REAL") / len(segment_frames), 4),
            "model_results": {
                "model1": segment_frames[0].get("model1", {}).get("label", "UNKNOWN"),
                "model2": segment_frames[0].get("model2", {}).get("label", "UNKNOWN")
            }
        }
    else:
        video_details = {
            "fake_confidence": 0.0,
            "real_confidence": 0.0,
            "model_results": {"model1": "UNKNOWN", "model2": "UNKNOWN"}
        }
    
    # 오디오 분석 세부사항
    audio_result = audio_analysis.get("final_result", {})
    audio_details = {
        "fake_confidence": audio_result.get("confidence", 0.0) if audio_result.get("is_fake_voice", False) else 0.0,
        "real_confidence": audio_result.get("confidence", 0.0) if not audio_result.get("is_fake_voice", False) else 0.0,
        "deepvoice_detected": audio_analysis.get("deepvoice_detection", {}).get("is_deepvoice", False),
        "semantic_mismatch": audio_analysis.get("semantic_analysis", {}).get("semantic_mismatch", False)
    }
    
    return {
        "video": video_details,
        "audio": audio_details
    }
