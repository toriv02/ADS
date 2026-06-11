import cv2
import numpy as np
from .config import CLASSES

def mask_to_polygons(mask, epsilon=1.0, min_area=100):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polygons = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon * peri, True)
        if len(approx) >= 3:
            polygon = approx.squeeze().tolist()
            if isinstance(polygon[0], list):
                polygon = polygon
            else:
                polygon = [polygon]
            polygons.append({
                'contour': cnt,
                'polygon': polygon,
                'area': area
            })
    return polygons

def extract_objects(pred_mask, original_size=None):
    h, w = pred_mask.shape
    if original_size:
        pred_mask = cv2.resize(pred_mask, original_size, interpolation=cv2.INTER_NEAREST)
        h, w = original_size
    objects = []
    for class_id, class_name in enumerate(CLASSES):
        class_mask = (pred_mask == class_id).astype(np.uint8) * 255
        polygons = mask_to_polygons(class_mask)
        for poly in polygons:
            geometry = {
                'type': 'Polygon',
                'coordinates': [poly['polygon']]
            }
            objects.append({
                'type': class_name,
                'class_id': class_id,
                'area': poly['area'],
                'geometry': geometry,
                'bbox': cv2.boundingRect(poly['contour'])
            })
    return objects