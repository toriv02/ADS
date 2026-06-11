from rest_framework import serializers
from .models import Task, Solution, RoadNetworkObject

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('id', 'user', 'status', 'working_directory', 'created_at', 'updated_at')

class RoadNetworkObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadNetworkObject
        fields = '__all__'
        read_only_fields = ('id',)

class SolutionSerializer(serializers.ModelSerializer):
    objects = RoadNetworkObjectSerializer(many=True, read_only=True)

    class Meta:
        model = Solution
        fields = '__all__'
        read_only_fields = ('id', 'created_at')