import cv2
import os
import numpy as np
from typing import List, Dict, Tuple
import time

def extract_frames_optimized(video_path: str, output_dir: str, frame_rate: float = 0.2, 
                           face_detection: bool = True, min_face_size: int = 50):
    """
    최적화된 프레임 추출 - 얼굴 탐지 포함
    
    Args:
        video_path: 영상 파일 경로
        output_dir: 프레임 저장 디렉토리
        frame_rate: 프레임 추출 간격 (초)
        face_detection: 얼굴 탐지 사용 여부
        min_face_size: 최소 얼굴 크기 (픽셀)
    
    Returns:
        추출된 프레임 정보 리스트
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # OpenCV 비디오 캡처
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("영상을 열 수 없습니다.")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * frame_rate) if fps > 0 else 1
    
    # 얼굴 탐지기 초기화 (선택적)
    face_cascade = None
    if face_detection:
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if face_cascade.empty():
                print("얼굴 탐지기 로딩 실패, 얼굴 탐지 비활성화")
                face_detection = False
        except Exception as e:
            print(f"얼굴 탐지기 초기화 실패: {e}, 얼굴 탐지 비활성화")
            face_detection = False

    frame_count = 0
    saved_frames = []
    start_time = time.time()
    
    print(f"프레임 추출 시작: {frame_rate}초 간격, 얼굴 탐지: {face_detection}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % frame_interval == 0:
            frame_time = frame_count / fps if fps > 0 else 0
            
            # 얼굴 탐지 (선택적)
            if face_detection and face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                # 얼굴이 없거나 너무 작으면 스킵
                if len(faces) == 0:
                    frame_count += 1
                    continue
                    
                # 가장 큰 얼굴 선택
                largest_face = max(faces, key=lambda x: x[2] * x[3])
                if largest_face[2] < min_face_size or largest_face[3] < min_face_size:
                    frame_count += 1
                    continue
                
                # 얼굴 영역으로 크롭
                x, y, w, h = largest_face
                face_frame = frame[y:y+h, x:x+w]
                
                # 얼굴 영역을 정사각형으로 리사이즈
                face_frame = cv2.resize(face_frame, (224, 224))
                frame_to_save = face_frame
            else:
                # 얼굴 탐지 없이 전체 프레임 사용
                frame_to_save = cv2.resize(frame, (224, 224))
            
            # 프레임 저장
            frame_filename = os.path.join(output_dir, f"frame_{frame_count}.jpg")
            cv2.imwrite(frame_filename, frame_to_save)
            
            saved_frames.append({
                "path": frame_filename, 
                "time": round(frame_time, 2),
                "frame_number": frame_count,
                "face_detected": face_detection and len(faces) > 0 if face_detection else None
            })
            
        frame_count += 1
    
    cap.release()
    
    extraction_time = time.time() - start_time
    print(f"프레임 추출 완료: {len(saved_frames)}개 프레임, 소요시간: {extraction_time:.2f}초")
    
    return saved_frames

def extract_frames_smart(video_path: str, output_dir: str, target_frames: int = 10):
    """
    스마트 프레임 추출 - 목표 프레임 수에 맞춰 자동 조정
    
    Args:
        video_path: 영상 파일 경로
        output_dir: 프레임 저장 디렉토리
        target_frames: 목표 프레임 수
    
    Returns:
        추출된 프레임 정보 리스트
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("영상을 열 수 없습니다.")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    cap.release()
    
    # 동적 프레임 간격 계산
    if duration <= 5:
        frame_rate = 0.5  # 2초마다 1프레임
    elif duration <= 10:
        frame_rate = 1.0  # 1초마다 1프레임
    elif duration <= 30:
        frame_rate = 2.0  # 2초마다 1프레임
    else:
        frame_rate = 3.0  # 3초마다 1프레임
    
    # 목표 프레임 수에 맞춰 조정
    estimated_frames = int(duration / frame_rate)
    if estimated_frames > target_frames:
        frame_rate = duration / target_frames
    
    return extract_frames_optimized(video_path, output_dir, frame_rate, face_detection=True)

def analyze_frame_quality(frame_path: str) -> Dict[str, float]:
    """
    프레임 품질 분석
    
    Args:
        frame_path: 프레임 파일 경로
    
    Returns:
        품질 지표 딕셔너리
    """
    try:
        image = cv2.imread(frame_path)
        if image is None:
            return {"error": "이미지를 읽을 수 없습니다"}
        
        # 밝기 분석
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        # 대비 분석
        contrast = np.std(gray)
        
        # 선명도 분석 (라플라시안 분산)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 블러 정도 분석
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "sharpness": float(laplacian_var),
            "blur_score": float(blur_score),
            "quality_score": float((contrast + laplacian_var) / 2)  # 종합 품질 점수
        }
    except Exception as e:
        return {"error": str(e)}

# 기존 함수와의 호환성을 위한 래퍼
def extract_frames(video_path: str, output_dir: str, frame_rate: float = 0.2):
    """기존 함수와의 호환성을 위한 래퍼"""
    return extract_frames_optimized(video_path, output_dir, frame_rate, face_detection=False)




