import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import os
import time
from typing import List, Dict, Any, Callable
import psutil

def get_optimal_workers(task_type: str = "cpu_intensive") -> int:
    """
    작업 유형에 따른 최적 워커 수 계산
    
    Args:
        task_type: 작업 유형 ("cpu_intensive", "io_intensive", "mixed")
    
    Returns:
        최적 워커 수
    """
    cpu_count = psutil.cpu_count(logical=False)  # 물리 코어 수
    logical_count = psutil.cpu_count(logical=True)  # 논리 코어 수
    
    if task_type == "cpu_intensive":
        # CPU 집약적 작업: 물리 코어 수 사용
        return min(cpu_count, 4)  # 최대 4개로 제한
    elif task_type == "io_intensive":
        # I/O 집약적 작업: 논리 코어 수 사용
        return min(logical_count, 8)  # 최대 8개로 제한
    else:  # mixed
        # 혼합 작업: 중간값 사용
        return min((cpu_count + logical_count) // 2, 6)

def analyze_frames_optimized(frames: List[Dict], batch_size: int = 5, 
                           max_workers: int = None) -> List[Dict]:
    """
    최적화된 프레임 분석 - 동적 워커 수 조정
    
    Args:
        frames: 프레임 정보 리스트
        batch_size: 배치 크기
        max_workers: 최대 워커 수 (None이면 자동 계산)
    
    Returns:
        분석 결과 리스트
    """
    if not frames:
        return []
    
    # 최적 워커 수 계산
    if max_workers is None:
        max_workers = get_optimal_workers("cpu_intensive")
    
    print(f"프레임 분석 시작: {len(frames)}개 프레임, 배치 크기: {batch_size}, 워커 수: {max_workers}")
    
    results = []
    start_time = time.time()
    
    # 프레임을 배치로 나누어 처리
    for i in range(0, len(frames), batch_size):
        batch = frames[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        print(f"배치 {batch_num} 처리 중... ({len(batch)}개 프레임)")
        batch_start = time.time()
        
        # 작은 배치로 병렬 처리
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            try:
                # analyze_single_frame 함수를 동적으로 임포트
                from app.services.deepfake_detector_optimized import predict_image
                
                def analyze_single_frame(frame):
                    return {**predict_image(frame["path"]), "time": frame["time"]}
                
                batch_results = list(executor.map(analyze_single_frame, batch))
                results.extend(batch_results)
                
            except Exception as e:
                print(f"배치 {batch_num} 처리 실패: {e}")
                # 실패한 배치는 기본값으로 채움
                for frame in batch:
                    results.append({
                        "error": str(e),
                        "time": frame["time"]
                    })
        
        batch_time = time.time() - batch_start
        print(f"배치 {batch_num} 완료: {batch_time:.2f}초")
        
        # 메모리 정리
        import gc
        gc.collect()
    
    total_time = time.time() - start_time
    print(f"프레임 분석 완료: {len(results)}개 결과, 총 소요시간: {total_time:.2f}초")
    
    return results

def analyze_frames_adaptive(frames: List[Dict]) -> List[Dict]:
    """
    적응형 프레임 분석 - 프레임 수에 따라 전략 자동 조정
    
    Args:
        frames: 프레임 정보 리스트
    
    Returns:
        분석 결과 리스트
    """
    frame_count = len(frames)
    
    if frame_count <= 5:
        # 소량: 단일 프로세스로 처리
        print("소량 프레임: 단일 프로세스 처리")
        return analyze_frames_single_process(frames)
    elif frame_count <= 20:
        # 중간량: 작은 배치로 처리
        print("중간량 프레임: 작은 배치 처리")
        return analyze_frames_optimized(frames, batch_size=3, max_workers=2)
    else:
        # 대량: 큰 배치로 처리
        print("대량 프레임: 큰 배치 처리")
        return analyze_frames_optimized(frames, batch_size=5, max_workers=4)

def analyze_frames_single_process(frames: List[Dict]) -> List[Dict]:
    """
    단일 프로세스로 프레임 분석 (소량 데이터용)
    
    Args:
        frames: 프레임 정보 리스트
    
    Returns:
        분석 결과 리스트
    """
    results = []
    
    for i, frame in enumerate(frames):
        try:
            from app.services.deepfake_detector_optimized import predict_image
            result = {**predict_image(frame["path"]), "time": frame["time"]}
            results.append(result)
            print(f"프레임 {i+1}/{len(frames)} 처리 완료")
        except Exception as e:
            print(f"프레임 {i+1} 처리 실패: {e}")
            results.append({"error": str(e), "time": frame["time"]})
    
    return results

def monitor_system_resources():
    """
    시스템 리소스 모니터링
    
    Returns:
        시스템 리소스 정보
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "memory_total_gb": memory.total / (1024**3)
        }
    except Exception as e:
        return {"error": str(e)}

def optimize_batch_size(frame_count: int, available_memory_gb: float) -> int:
    """
    사용 가능한 메모리에 따라 최적 배치 크기 계산
    
    Args:
        frame_count: 총 프레임 수
        available_memory_gb: 사용 가능한 메모리 (GB)
    
    Returns:
        최적 배치 크기
    """
    # 메모리 기반 배치 크기 계산
    if available_memory_gb >= 8:
        return min(frame_count, 10)
    elif available_memory_gb >= 4:
        return min(frame_count, 5)
    else:
        return min(frame_count, 3)

# 기존 함수와의 호환성을 위한 래퍼
def analyze_frames_in_parallel(frames, batch_size=5):
    """기존 함수와의 호환성을 위한 래퍼"""
    return analyze_frames_optimized(frames, batch_size)




