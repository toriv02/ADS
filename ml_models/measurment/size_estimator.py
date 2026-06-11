import cv2
import numpy as np
from .geometry_utils import compute_line_length, compute_bbox_width_height
from .config import DEFAULT_REFERENCE_METERS

class SizeEstimator:
    def __init__(self, image_path=None, reference_pixels=None, reference_meters=None):
        self.image_path = image_path
        self.reference_pixels = reference_pixels
        self.reference_meters = reference_meters
        self.meters_per_pixel = None
        if reference_pixels is not None and reference_meters is not None:
            self.meters_per_pixel = reference_meters / reference_pixels

    def calibrate_from_reference(self, reference_pixels, reference_meters):
        self.reference_pixels = reference_pixels
        self.reference_meters = reference_meters
        self.meters_per_pixel = reference_meters / reference_pixels
        return self.meters_per_pixel

    def calibrate_from_known_object(self, image, bbox, known_meters, object_class='car'):
        width_pixels, height_pixels = compute_bbox_width_height(bbox)
        avg_pixels = (width_pixels + height_pixels) / 2
        self.meters_per_pixel = known_meters / avg_pixels
        return self.meters_per_pixel

    def estimate_size(self, pixel_length):
        if self.meters_per_pixel is None:
            raise ValueError("Calibration not performed. Call calibrate_from_reference first.")
        return pixel_length * self.meters_per_pixel

    def estimate_bbox_size(self, bbox):
        width_px, height_px = compute_bbox_width_height(bbox)
        width_m = self.estimate_size(width_px)
        height_m = self.estimate_size(height_px)
        return width_m, height_m

    def estimate_polygon_area(self, polygon):
        area_px = cv2.contourArea(np.array(polygon, dtype=np.float32))
        area_m = area_px * (self.meters_per_pixel ** 2)
        return area_m

    def set_image(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)

def calibrate_from_reference(reference_pixels, reference_meters):
    estimator = SizeEstimator()
    estimator.calibrate_from_reference(reference_pixels, reference_meters)
    return estimator

def estimate_size(image_path, bbox_pixels, reference_data):
    estimator = SizeEstimator()
    estimator.calibrate_from_reference(reference_data['pixels'], reference_data['meters'])
    return estimator.estimate_size(bbox_pixels)