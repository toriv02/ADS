import os
import json
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Task, Solution, RoadNetworkObject
from .serializers import TaskSerializer, SolutionSerializer, RoadNetworkObjectSerializer
from ..processing.tasks import start_preprocessing

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all()
        return Task.objects.filter(user=user)

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user, status='pending')
        work_dir = f"tasks/{task.id}"
        default_storage.makedirs(work_dir)
        task.working_directory = work_dir
        uploaded_file = self.request.FILES.get('media_file')
        if uploaded_file:
            file_path = default_storage.save(f"{work_dir}/original_{uploaded_file.name}", ContentFile(uploaded_file.read()))
            task.original_file = file_path
        task.save()
        start_preprocessing.delay(task.id)

    @action(detail=True, methods=['get'])
    def solution(self, request, pk=None):
        task = self.get_object()
        try:
            solution = task.solution
            serializer = SolutionSerializer(solution)
            return Response(serializer.data)
        except Solution.DoesNotExist:
            return Response({'detail': 'Решение ещё не готово'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def export_geojson(self, request, pk=None):
        task = self.get_object()
        try:
            solution = task.solution
        except Solution.DoesNotExist:
            return Response({'detail': 'Решение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        features = []
        for obj in solution.objects.all():
            feature = {
                'type': 'Feature',
                'geometry': obj.geometry,
                'properties': {
                    'type': obj.object_type,
                    'width': obj.width,
                    'height': obj.height,
                    'area': obj.area,
                    'is_occupied': obj.is_occupied,
                    'task_id': task.id
                }
            }
            features.append(feature)

        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        return Response(geojson)

    @action(detail=True, methods=['post'])
    def update_objects(self, request, pk=None):
        task = self.get_object()
        solution, _ = Solution.objects.get_or_create(task=task)
        objects_data = request.data.get('objects', [])
        RoadNetworkObject.objects.filter(solution=solution).delete()
        for obj_data in objects_data:
            RoadNetworkObject.objects.create(solution=solution, **obj_data)
        return Response({'status': 'updated'})