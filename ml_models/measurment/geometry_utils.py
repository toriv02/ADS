import numpy as np
import cv2

def pixel_to_real(pixel_value, meters_per_pixel):
    return pixel_value * meters_per_pixel

def compute_polygon_area(polygon, meters_per_pixel=None):
    if isinstance(polygon, list):
        polygon = np.array(polygon, dtype=np.float32)
    area_pixels = cv2.contourArea(polygon)
    if meters_per_pixel is not None:
        return area_pixels * (meters_per_pixel ** 2)
    return area_pixels

def compute_line_length(point1, point2):
    return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def compute_bbox_width_height(bbox):
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    return width, height