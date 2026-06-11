import cv2
import os
from .file_utils import ensure_directory

def extract_frames(video_path, output_dir=None, fps=1.0):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    if output_dir is None:
        base_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(base_dir, f"{video_name}_frames")
    ensure_directory(output_dir)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    original_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = max(1, int(original_fps / fps)) if fps > 0 else 1

    frame_paths = []
    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            out_path = os.path.join(output_dir, f"frame_{saved_count:06d}.jpg")
            cv2.imwrite(out_path, frame)
            frame_paths.append(out_path)
            saved_count += 1
        frame_count += 1

    cap.release()
    return frame_paths