import os
import cv2
from celery import shared_task
from django.core.files.storage import default_storage
from apps.tasks.models import Task, Solution, RoadNetworkObject
from apps.tasks.serializers import RoadNetworkObjectSerializer

@shared_task(bind=True)
def start_preprocessing(self, task_id):
    task = Task.objects.get(id=task_id)
    task.status = 'preprocessing'
    task.save()

    try:
        from ml_models.preprocessor import enhance_image, extract_frames
        from ml_models.ground_detector import detect_objects as detect_ground
        from ml_models.satellite_segmenter import segment_image
        from ml_models.measurement import SizeEstimator

        input_path = task.original_file.path if task.original_file else None
        if not input_path or not os.path.exists(input_path):
            raise FileNotFoundError(f"Original file not found for task {task_id}")

        if task.material_type == 'video':
            frame_dir = os.path.join(task.working_directory, 'frames')
            frame_paths = extract_frames(input_path, output_dir=frame_dir, fps=1.0)
            image_paths = [enhance_image(p, quality=task.quality_profile) for p in frame_paths]
        else:
            enhanced = enhance_image(input_path, quality=task.quality_profile)
            image_paths = [enhanced]

        task.status = 'processing'
        task.save()

        all_objects = []
        if task.material_type == 'satellite':
            for img_path in image_paths:
                result = segment_image(img_path)
                all_objects.extend(result['objects'])
        else:
            for img_path in image_paths:
                result = detect_ground(img_path)
                all_objects.extend(result['objects'])

        estimator = SizeEstimator()
        if task.reference_pixels and task.reference_meters:
            estimator.calibrate_from_reference(task.reference_pixels, task.reference_meters)

        for obj in all_objects:
            if 'bbox' in obj:
                width_px = obj['bbox'][2] - obj['bbox'][0]
                height_px = obj['bbox'][3] - obj['bbox'][1]
                if estimator.meters_per_pixel:
                    obj['width'] = estimator.estimate_size(width_px)
                    obj['height'] = estimator.estimate_size(height_px)
            if 'area' in obj and estimator.meters_per_pixel:
                obj['area'] = estimator.estimate_polygon_area(obj['geometry']['coordinates'][0])

        solution, _ = Solution.objects.get_or_create(task=task)
        RoadNetworkObject.objects.filter(solution=solution).delete()

        parking_total = 0
        parking_occupied = 0
        parking_free = 0
        bus_stops = 0
        road_widths = []
        sidewalk_widths = []

        for obj in all_objects:
            obj_data = {
                'solution': solution,
                'object_type': obj['type'],
                'geometry': obj['geometry'],
                'width': obj.get('width'),
                'height': obj.get('height'),
                'area': obj.get('area'),
                'is_occupied': obj.get('is_occupied'),
            }
            if 'bbox' in obj:
                obj_data['bbox_x1'] = obj['bbox'][0]
                obj_data['bbox_y1'] = obj['bbox'][1]
                obj_data['bbox_x2'] = obj['bbox'][2]
                obj_data['bbox_y2'] = obj['bbox'][3]
            RoadNetworkObject.objects.create(**obj_data)

            if obj['type'] == 'parking_spot':
                parking_total += 1
                if obj.get('is_occupied'):
                    parking_occupied += 1
                else:
                    parking_free += 1
            elif obj['type'] == 'bus_stop':
                bus_stops += 1
            elif obj['type'] == 'road_lane' and obj.get('width'):
                road_widths.append(obj['width'])
            elif obj['type'] == 'sidewalk' and obj.get('width'):
                sidewalk_widths.append(obj['width'])

        solution.total_parking_spots = parking_total
        solution.occupied_parking_spots = parking_occupied
        solution.free_parking_spots = parking_free
        solution.public_transport_stops = bus_stops
        solution.road_width = max(road_widths) if road_widths else None
        solution.sidewalk_width = max(sidewalk_widths) if sidewalk_widths else None
        solution.save()

        task.status = 'completed'
        task.save()

    except Exception as e:
        task.status = 'failed'
        task.save()
        raise self.retry(exc=e, countdown=60, max_retries=3)