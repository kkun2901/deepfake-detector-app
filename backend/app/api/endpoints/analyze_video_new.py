from fastapi import APIRouter, UploadFile, File, Form
import os, uuid
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from app.services.video_processing import extract_frames
from app.services.deepfake_detector import predict_image
from app.services.audio_processing import AudioProcessor
from app.utils.helpers import save_analysis_result, create_smart_timeline, create_analysis_summary, create_segment_analysis_details

router = APIRouter()

# 전역 함수 (멀티프로세싱에서 호출 가능)
def analyze_single_frame(frame):
    return {**predict_image(frame["path"]), "time": frame["time"]}

def analyze_frames_in_parallel(frames, batch_size=5):
    """메모리 절약을 위한 배치 처리"""
    results = []
    
    # 프레임을 배치로 나누어 처리
    for i in range(0, len(frames), batch_size):
        batch = frames[i:i + batch_size]
        print(f"배치 {i//batch_size + 1} 처리 중... ({len(batch)}개 프레임)")
        
        with ProcessPoolExecutor(max_workers=2) as executor:
            batch_results = list(executor.map(analyze_single_frame, batch))
            results.extend(batch_results)
        
        # 배치 처리 후 메모리 정리
        import gc
        gc.collect()
    
    return results

@router.post("/", summary="Analyze Video")
async def analyze_video(user_id: str = Form(...), video: UploadFile = File(...)):
    """
    영상 업로드 및 딥페이크 분석
    
    Args:
        user_id: 사용자 ID
        video: 분석할 영상 파일
    
    Returns:
        분석 ID (즉시 반환)
    """
    try:
        print(f"=== 영상 분석 시작: {video.filename} ===")
        
        # 분석 ID 생성
        analysis_id = str(uuid.uuid4())
        print(f"분석 ID 생성: {analysis_id}")
        
        # 임시 저장
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        video_path = os.path.join(temp_dir, f"{analysis_id}_{video.filename}")
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())
        
        # 백그라운드에서 분석 시작
        import asyncio
        asyncio.create_task(process_video_background(analysis_id, video_path, user_id))
        
        # 즉시 분석 ID 반환
        return analysis_id
        
    except Exception as e:
        print(f"분석 시작 오류: {e}")
        return {"error": str(e)}

# 백그라운드에서 비디오 처리
async def process_video_background(analysis_id: str, video_path: str, user_id: str):
    """
    백그라운드에서 비디오 분석 처리
    """
    try:
        print(f"백그라운드 분석 시작: {analysis_id}")
        
        # 동영상 길이 확인 및 동적 프레임 추출 간격 설정
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        # 영상 길이에 따른 프레임 추출 간격 동적 조정
        if duration <= 5:
            frame_rate = 0.5  # 2초마다 1프레임 (짧은 영상)
        elif duration <= 10:
            frame_rate = 1.0  # 1초마다 1프레임 (중간 영상)
        elif duration <= 30:
            frame_rate = 2.0  # 2초마다 1프레임 (긴 영상)
        else:
            frame_rate = 3.0  # 3초마다 1프레임 (매우 긴 영상)
        
        print(f"영상 길이: {duration:.1f}초, 프레임 추출 간격: {frame_rate}초")
        
        # 프레임 추출
        temp_dir = os.path.join(os.getcwd(), "temp")
        frame_dir = os.path.join(temp_dir, f"{analysis_id}_frames")
        frames = extract_frames(video_path, frame_dir, frame_rate=frame_rate)
        if not frames:
            raise Exception("프레임 추출 실패: 영상이 비어있거나 지원되지 않는 형식입니다.")

        # 병렬 프레임 분석 (배치 처리)
        print(f"총 {len(frames)}개 프레임을 배치로 처리합니다...")
        results = analyze_frames_in_parallel(frames, batch_size=3)  # 배치 크기 더 작게
        print(f"프레임 분석 완료: {len(results)}개 결과")
        
        # 프레임 파일들 즉시 삭제 (메모리 절약)
        import shutil
        try:
            shutil.rmtree(frame_dir)
            print("프레임 파일들 정리 완료")
        except Exception as e:
            print(f"프레임 파일 정리 실패: {e}")

        # 평균 확률 계산
        fake_conf = sum(r["confidence"] for r in results if r["ensemble_result"] == "FAKE") / len(results)
        real_conf = sum(r["confidence"] for r in results if r["ensemble_result"] == "REAL") / len(results)
        final_label = "FAKE" if fake_conf > real_conf else "REAL"
        
        # 음성 분석
        print("음성 분석 시작...")
        audio_processor = AudioProcessor()
        audio_analysis = audio_processor.analyze_audio(video_path)
        print("음성 분석 완료")
        
        # 스마트 타임라인 생성
        timeline = create_smart_timeline(results)
        
        # 분석 요약 생성
        summary = create_analysis_summary(
            video_analysis={"overall_result": final_label, "confidence": max(fake_conf, real_conf)},
            audio_analysis=audio_analysis,
            timeline=timeline
        )
        
        # 세그먼트별 상세 분석
        segment_details = create_segment_analysis_details(timeline)
        
        # 최종 결과 데이터 구성
        result_data = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "timeline": timeline,
            "segment_details": segment_details,
            "audio_analysis": audio_analysis
        }
        
        # 결과 저장
        save_analysis_result(analysis_id, result_data)
        print(f"분석 완료 및 저장: {analysis_id}")
        
        # 임시 파일 정리
        try:
            os.remove(video_path)
            print("임시 비디오 파일 정리 완료")
        except Exception as e:
            print(f"임시 파일 정리 실패: {e}")
            
    except Exception as e:
        print(f"백그라운드 분석 오류: {e}")
        # 오류 상태 저장
        error_data = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "failed"
        }
        save_analysis_result(analysis_id, error_data)
