from ultralytics import YOLO
import cv2

class GroundAnalyzer:
    def __init__(self, model_path='yolov8n.pt'):
        self.model = YOLO(model_path)

    def detect(self, image_path, conf_threshold=0.25):
        results = self.model(image_path, conf=conf_threshold)
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                detections.append({
                    'class': self.model.names[cls_id],
                    'confidence': float(box.conf[0]),
                    'bbox': [float(x) for x in box.xyxy[0].tolist()]
                })
        return detections