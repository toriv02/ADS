from celery.signals import task_failure, task_success
from apps.tasks.models import Task

@task_failure.connect(sender=start_preprocessing)
def handle_task_failure(sender, task_id, exception, **kwargs):
    if hasattr(task_id, 'id'):
        task_obj = Task.objects.get(id=task_id.id)
    else:
        task_obj = Task.objects.get(id=task_id)
    task_obj.status = 'failed'
    task_obj.save()

@task_success.connect(sender=start_preprocessing)
def handle_task_success(sender, result, **kwargs):
    pass