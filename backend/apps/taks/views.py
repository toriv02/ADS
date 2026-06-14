from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Task, Solution
from .serializers import TaskSerializer, SolutionSerializer
from .tasks import process_ground_task, process_satellite_task
import json

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all()
        return Task.objects.filter(user=user)

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        if task.material_type == 'ground':
            process_ground_task.delay(task.id)
        else:
            process_satellite_task.delay(task.id)

    @action(detail=True, methods=['post'])
    def correct(self, request, pk=None):
        task = self.get_object()
        data = json.loads(request.body)
        solution = Solution.objects.get(task=task)
        for obj_data in data.get('objects', []):
            RoadNetworkObject.objects.filter(id=obj_data['id']).update(**obj_data)
        return Response({'status': 'updated'})

    @action(detail=True, methods=['get'])
    def export_geojson(self, request, pk=None):
        task = self.get_object()
        solution = Solution.objects.get(task=task)
        features = []
        for obj in solution.roadnetworkobject_set.all():
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [task.longitude, task.latitude]},
                'properties': {'type': obj.object_type, 'width': obj.width, 'height': obj.height}
            })
        geojson = {'type': 'FeatureCollection', 'features': features}
        return Response(geojson)