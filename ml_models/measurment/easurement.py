import cv2
import math
import numpy as np

def pixel_distance(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def compute_scale_factor(ref_start, ref_end, real_meters):
    px_dist = pixel_distance(ref_start, ref_end)
    return px_dist / real_meters if px_dist != 0 else 0

def correct_perspective(image, src_points, dst_width, dst_height):
    src = np.float32(src_points)
    dst = np.float32([[0,0],[dst_width,0],[dst_width,dst_height],[0,dst_height]])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(image, M, (dst_width, dst_height))
    return warped, M

def object_real_size(bbox_px, scale_factor):
    width_px = bbox_px[2] - bbox_px[0]
    height_px = bbox_px[3] - bbox_px[1]
    return width_px / scale_factor, height_px / scale_factor