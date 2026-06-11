from django.contrib.auth.models import AbstractUser
from django.db import models

class Employee(AbstractUser):
    is_superuser = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"