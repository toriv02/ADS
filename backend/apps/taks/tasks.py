from celery import shared_task
from django.core.files.base import ContentFile
from ml_models.ground_analyzer import GroundAnalyzer
from ml_models.satellite_analyzer import UNet
from ml_models.measurement import compute_scale_factor, object_real_size
from .models import Task, Solution, RoadNetworkObject
import cv2
import torch
import os

ground_analyzer = GroundAnalyzer('models/yolo_best.pt')
sat_model = UNet(7)
sat_model.load_state_dict(torch.load('models/unet_satellite.pth'))
sat_model.eval()

@shared_task
def process_ground_task(task_id):
    task = Task.objects.get(id=task_id)
    task.status = 'processing'
    task.save()
    detections = ground_analyzer.detect(task.source_file.path)
    solution = Solution.objects.create(task=task)
    for det in detections:
        scale = compute_scale_factor(
            (task.reference_point_start_x, task.reference_point_start_y),
            (task.reference_point_end_x, task.reference_point_end_y),
            task.reference_size_m
        )
        w, h = object_real_size(det['bbox'], scale)
        RoadNetworkObject.objects.create(
            solution=solution,
            object_type=det['class'],
            position_x=det['bbox'][0],
            position_y=det['bbox'][1],
            width=w,
            height=h
        )
    task.status = 'completed'
    task.save()

@shared_task
def process_satellite_task(task_id):
    task = Task.objects.get(id=task_id)
    task.status = 'processing'
    task.save()
    img = cv2.imread(task.source_file.path)
    img_tensor = torch.from_numpy(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).float().permute(2,0,1) / 255.0
    with torch.no_grad():
        mask = sat_model(img_tensor.unsqueeze(0))
        mask = torch.argmax(mask, dim=1).squeeze(0).numpy()
    solution = Solution.objects.create(task=task)
    task.status = 'completed'
    task.save()