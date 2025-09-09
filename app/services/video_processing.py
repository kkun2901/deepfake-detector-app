import cv2
import os

def extract_frames(video_path: str, output_dir: str, frame_rate: float = 0.2):
    """영상에서 일정 간격으로 프레임 추출 (기본: 5fps), 각 프레임의 타임스탬프 포함"""
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * frame_rate) if fps > 0 else 1

    frame_count = 0
    saved_frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            frame_time = frame_count / fps if fps > 0 else 0  # 현재 프레임의 시간(초)
            frame_filename = os.path.join(output_dir, f"frame_{frame_count}.jpg")
            cv2.imwrite(frame_filename, frame)
            saved_frames.append({"path": frame_filename, "time": round(frame_time, 2)})
        frame_count += 1
    cap.release()
    return saved_frames
