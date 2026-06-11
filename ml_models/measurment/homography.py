import cv2
import numpy as np

def find_homography(src_points, dst_points):
    H, _ = cv2.findHomography(np.array(src_points), np.array(dst_points))
    return H

def correct_perspective(image, src_points, dst_points):
    H = find_homography(src_points, dst_points)
    h, w = image.shape[:2]
    dst_size = (int(dst_points[2][0]), int(dst_points[2][1]))
    warped = cv2.warpPerspective(image, H, dst_size)
    return warped, H

def apply_homography_to_points(points, H):
    pts = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(pts, H)
    return transformed.reshape(-1, 2).tolist()