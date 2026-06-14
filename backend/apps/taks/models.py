from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_active = models.BooleanField(default=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

class Task(models.Model):
    STATUS_CHOICES = [('pending', 'Ожидает'), ('processing', 'В работе'), ('completed', 'Завершена')]
    TYPE_CHOICES = [('ground', 'Наземный'), ('satellite', 'Спутниковый')]
    QUALITY_CHOICES = [('fast', 'Быстрое'), ('quality', 'Качественное'), ('high', 'Высокое')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    target_quality = models.CharField(max_length=10, choices=QUALITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    working_directory = models.CharField(max_length=500, blank=True)
    source_file = models.FileField(upload_to='uploads/')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    reference_size_m = models.FloatField(default=1.0)
    reference_point_start_x = models.FloatField(null=True)
    reference_point_start_y = models.FloatField(null=True)
    reference_point_end_x = models.FloatField(null=True)
    reference_point_end_y = models.FloatField(null=True)

class Solution(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    occupied_parking_spots = models.IntegerField(default=0)
    free_parking_spots = models.IntegerField(default=0)
    public_transport_stops = models.IntegerField(default=0)
    road_width = models.FloatField(default=0.0)
    sidewalk_width = models.FloatField(default=0.0)

class RoadNetworkObject(models.Model):
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    object_type = models.CharField(max_length=50)
    position_x = models.FloatField()
    position_y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    area = models.FloatField(null=True)
    is_occupied = models.BooleanField(null=True)