from fastapi import APIRouter, UploadFile, File, Form
import os, uuid
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from app.services.video_processing import extract_frames
from app.services.deepfake_detector import predict_image
from app.services.audio_processing import AudioProcessor
from app.utils.helpers import save_analysis_result, create_smart_timeline, create_analysis_summary, create_segment_analysis_details
import asyncio

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
        
        # 작은 배치로 병렬 처리
        with ProcessPoolExecutor(max_workers=2) as executor:  # 워커 수 감소
            batch_results = list(executor.map(analyze_single_frame, batch))
            results.extend(batch_results)
        
        # 메모리 정리
        import gc
        gc.collect()
    
    return results

@router.post("/start-analysis", summary="Start Video Analysis")
async def start_analysis(user_id: str = Form(...), video: UploadFile = File(...)):
    """
    영상 분석 시작 (백그라운드에서 처리)
    
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
        asyncio.create_task(process_video_background(analysis_id, video_path, user_id, video.filename))
        
        # 즉시 분석 ID 반환
        return {
            "analysis_id": analysis_id,
            "status": "started",
            "message": "분석이 시작되었습니다. 잠시 후 결과를 확인해주세요."
        }
        
    except Exception as e:
        print(f"분석 시작 오류: {e}")
        return {"error": str(e)}

@router.get("/get-result/{analysis_id}", summary="Get Analysis Result")
async def get_result(analysis_id: str):
    """
    분석 결과 조회
    
    Args:
        analysis_id: 분석 ID
    
    Returns:
        분석 결과 또는 진행 상태
    """
    try:
        from app.utils.helpers import get_analysis_result
        
        result = get_analysis_result(analysis_id)
        
        if result:
            return {
                "status": "completed",
                "result": result
            }
        else:
            return {
                "status": "processing",
                "message": "분석이 진행 중입니다. 잠시 후 다시 확인해주세요."
            }
            
    except Exception as e:
        print(f"결과 조회 오류: {e}")
        return {"error": str(e)}

# 백그라운드에서 비디오 처리
async def process_video_background(analysis_id: str, video_path: str, user_id: str, video_filename: str):
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
        frame_dir = os.path.join(temp_dir, f"{video_filename}_frames")
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

        # 앙상블 결과 계산 (안전한 키 접근)
        fake_confidences = []
        real_confidences = []
        
        for r in results:
            if "fake_confidence" in r:
                fake_confidences.append(r["fake_confidence"])
            if "real_confidence" in r:
                real_confidences.append(r["real_confidence"])
        
        fake_conf = sum(fake_confidences) / len(fake_confidences) if fake_confidences else 0
        real_conf = sum(real_confidences) / len(real_confidences) if real_confidences else 0
        
        # 딥페이크 프레임 비율 기준으로 판정 (50% 이상이면 FAKE)
        fake_frames = len([r for r in results if r.get("ensemble_result") == "FAKE"])
        total_frames = len(results)
        fake_ratio = fake_frames / total_frames if total_frames > 0 else 0
        
        final_label = "FAKE" if fake_ratio >= 0.5 else "REAL"
        print(f"최종 결과: {final_label} (딥페이크 프레임 비율: {fake_ratio:.1%}, FAKE: {fake_conf:.3f}, REAL: {real_conf:.3f})")

        # 오디오 분석
        print("오디오 분석 시작...")
        audio_processor = AudioProcessor()
        audio_analysis = audio_processor.analyze_audio(video_path)
        print(f"오디오 분석 완료: {audio_analysis}")
        
        # 스마트 타임라인 생성
        timeline = create_smart_timeline(results, min_segment_duration=2.0)
        
        # 분석 요약 생성
        video_analysis = {
            "overall_result": final_label,
            "overall_confidence": round(fake_conf, 4),  # 딥페이크 확률로 수정
            "total_frames": len(results),
            "fake_frames": len([r for r in results if r["ensemble_result"] == "FAKE"]),
            "real_frames": len([r for r in results if r["ensemble_result"] == "REAL"])
        }
        
        summary = create_analysis_summary(video_analysis, audio_analysis, timeline)
        
        # 구간별 상세 분석
        detailed_segments = []
        for segment in timeline:
            segment_details = create_segment_analysis_details(segment, video_analysis, audio_analysis)
            detailed_segments.append({
                **segment,
                "details": segment_details
            })
        
        # 최종 결과 구성
        analysis_result = {
            "videoId": analysis_id,
            "video_name": video_filename,
            "user_id": user_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "video_info": {
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "frame_rate_used": frame_rate
            },
            "summary": summary,
            "timeline": detailed_segments,
            "video_analysis": video_analysis,
            "audio_analysis": audio_analysis,
            "raw_frame_results": results  # 디버깅용
        }
        
        # 결과 저장
        save_analysis_result(analysis_result["videoId"], analysis_result)
        
        # 임시 파일 정리
        try:
            os.remove(video_path)
            print("임시 영상 파일 정리 완료")
        except Exception as e:
            print(f"임시 파일 정리 실패: {e}")
        
        print(f"=== 분석 완료: {analysis_result['videoId']} ===")
        
    except Exception as e:
        print(f"분석 중 오류 발생: {e}")
        # 오류 결과도 저장
        error_result = {
            "videoId": analysis_id,
            "video_name": video_filename,
            "user_id": user_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "error"
        }
        save_analysis_result(analysis_id, error_result)
