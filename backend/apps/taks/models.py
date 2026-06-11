from django.db import models
from django.conf import settings

class Task(models.Model):
    MATERIAL_TYPES = (
        ('satellite', 'Спутниковый снимок'),
        ('ground', 'Наземный снимок'),
        ('video', 'Видео'),
    )
    QUALITY_PROFILES = (
        ('fast', 'Быстрое'),
        ('balanced', 'Качественное'),
        ('high', 'Высокое'),
    )
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('preprocessing', 'Предобработка'),
        ('processing', 'Анализ'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES)
    quality_profile = models.CharField(max_length=20, choices=QUALITY_PROFILES, default='balanced')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    working_directory = models.CharField(max_length=500, blank=True)
    original_file = models.FileField(upload_to='uploads/', null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    reference_pixels = models.FloatField(null=True, blank=True)
    reference_meters = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class Solution(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='solution')
    total_parking_spots = models.IntegerField(default=0)
    occupied_parking_spots = models.IntegerField(default=0)
    free_parking_spots = models.IntegerField(default=0)
    public_transport_stops = models.IntegerField(default=0)
    road_width = models.FloatField(null=True, blank=True)
    sidewalk_width = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class RoadNetworkObject(models.Model):
    OBJECT_TYPES = (
        ('road_lane', 'Полоса движения'),
        ('parking_spot', 'Парковочное место'),
        ('bus_stop', 'Остановка'),
        ('building', 'Здание'),
        ('sidewalk', 'Тротуар'),
        ('bike_lane', 'Велодорожка'),
        ('green_zone', 'Зелёная зона'),
    )
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='objects')
    object_type = models.CharField(max_length=30, choices=OBJECT_TYPES)
    geometry = models.JSONField()
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    area = models.FloatField(null=True, blank=True)
    is_occupied = models.BooleanField(null=True)
    bbox_x1 = models.FloatField(null=True)
    bbox_y1 = models.FloatField(null=True)
    bbox_x2 = models.FloatField(null=True)
    bbox_y2 = models.FloatField(null=True)