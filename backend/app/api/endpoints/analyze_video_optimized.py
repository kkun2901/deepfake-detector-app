from fastapi import APIRouter, UploadFile, File, Form
import os, uuid
from datetime import datetime
from app.services.video_processing_optimized import extract_frames_smart, analyze_frame_quality
from app.services.deepfake_detector_optimized import predict_image, cleanup_memory
from app.services.parallel_processing_optimized import analyze_frames_adaptive, monitor_system_resources
from app.services.audio_processing import AudioProcessor
from app.utils.helpers import save_analysis_result, create_smart_timeline, create_analysis_summary, create_segment_analysis_details

router = APIRouter()

@router.post("/", summary="Analyze Video (Optimized)")
async def analyze_video(user_id: str = Form(...), video: UploadFile = File(...)):
    """
    최적화된 영상 업로드 및 딥페이크 분석
    
    최적화 기능:
    - 스마트 프레임 추출 (얼굴 탐지 포함)
    - 적응형 병렬 처리
    - 메모리 최적화
    - 시스템 리소스 모니터링
    
    Args:
        user_id: 사용자 ID
        video: 분석할 영상 파일
    
    Returns:
        분석 결과 (타임라인, 신뢰도, 음성 분석 포함)
    """
    try:
        print(f"=== 최적화된 영상 분석 시작: {video.filename} ===")
        
        # 시스템 리소스 모니터링
        system_resources = monitor_system_resources()
        print(f"시스템 리소스: CPU {system_resources.get('cpu_percent', 0):.1f}%, "
              f"메모리 {system_resources.get('memory_percent', 0):.1f}%")
        
        # 임시 저장
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        video_path = os.path.join(temp_dir, video.filename)
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())

        # 동영상 정보 확인
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        print(f"영상 정보: 길이 {duration:.1f}초, FPS {fps:.1f}, 총 프레임 {int(frame_count)}")
        
        # 스마트 프레임 추출 (얼굴 탐지 포함)
        frame_dir = os.path.join(temp_dir, f"{video.filename}_frames")
        frames = extract_frames_smart(video_path, frame_dir, target_frames=10)
        
        if not frames:
            raise Exception("프레임 추출 실패: 영상이 비어있거나 지원되지 않는 형식입니다.")

        print(f"프레임 추출 완료: {len(frames)}개 프레임")
        
        # 프레임 품질 분석
        quality_scores = []
        for frame in frames:
            quality = analyze_frame_quality(frame["path"])
            if "error" not in quality:
                quality_scores.append(quality["quality_score"])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        print(f"평균 프레임 품질: {avg_quality:.2f}")

        # 적응형 프레임 분석
        results = analyze_frames_adaptive(frames)
        print(f"프레임 분석 완료: {len(results)}개 결과")
        
        # 프레임 파일들 즉시 삭제 (메모리 절약)
        import shutil
        try:
            shutil.rmtree(frame_dir)
            print("프레임 파일들 정리 완료")
        except Exception as e:
            print(f"프레임 파일 정리 실패: {e}")

        # 평균 확률 계산
        valid_results = [r for r in results if "error" not in r]
        if not valid_results:
            raise Exception("모든 프레임 분석 실패")
        
        fake_conf = sum(r["confidence"] for r in valid_results if r["ensemble_result"] == "FAKE") / len(valid_results)
        real_conf = sum(r["confidence"] for r in valid_results if r["ensemble_result"] == "REAL") / len(valid_results)
        final_label = "FAKE" if fake_conf > real_conf else "REAL"
        
        # 음성 분석
        print("음성 분석 시작...")
        audio_processor = AudioProcessor()
        audio_analysis = audio_processor.analyze_audio(video_path)
        print("음성 분석 완료")
        
        # 스마트 타임라인 생성
        timeline = create_smart_timeline(valid_results, min_segment_duration=2.0)
        
        # 분석 요약 생성
        video_analysis = {
            "overall_result": final_label,
            "overall_confidence": round(max(fake_conf, real_conf), 4),
            "total_frames": len(valid_results),
            "fake_frames": len([r for r in valid_results if r["ensemble_result"] == "FAKE"]),
            "real_frames": len([r for r in valid_results if r["ensemble_result"] == "REAL"]),
            "average_quality": round(avg_quality, 4),
            "processing_optimization": "enabled"
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
            "videoId": str(uuid.uuid4()),
            "video_name": video.filename,
            "user_id": user_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "video_info": {
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "frames_extracted": len(frames),
                "face_detection": "enabled",
                "quality_score": round(avg_quality, 4)
            },
            "summary": summary,
            "timeline": detailed_segments,
            "video_analysis": video_analysis,
            "audio_analysis": audio_analysis,
            "system_resources": system_resources,
            "optimization_info": {
                "smart_extraction": True,
                "adaptive_processing": True,
                "memory_optimization": True,
                "face_detection": True
            },
            "raw_frame_results": valid_results
        }
        
        # 결과 저장
        save_analysis_result(analysis_result["videoId"], analysis_result)
        
        # 임시 파일 정리
        try:
            os.remove(video_path)
            print("임시 영상 파일 정리 완료")
        except Exception as e:
            print(f"임시 파일 정리 실패: {e}")
        
        # 메모리 정리
        cleanup_memory()
        
        print(f"=== 최적화된 분석 완료: {analysis_result['videoId']} ===")
        
        return analysis_result
        
    except Exception as e:
        print(f"분석 중 오류 발생: {e}")
        # 메모리 정리
        cleanup_memory()
        return {"error": str(e), "video_name": video.filename}




