from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    TEACHER = 'Teacher'
    TA = 'Teaching Assistant'
    UNREGISTERED = 'Unregistered'


class CustomUser(AbstractUser):
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.UNREGISTERED)
    courses = models.ManyToManyField('assignment_manager.Course', related_name='staff', blank=True)
    gitlab_id = models.IntegerField(blank=True, null=True)

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_ta(self):
        return self.role == Role.TA

    def save(self, *args, **kwargs):
        # add staff to assignment repos
        super().save(*args, **kwargs)
        from services.gitlab_services import GitlabService
        gs = GitlabService()
        for course in self.courses.all():
            gs.add_system_user_to_course(user=self, course=course)




class LoginEvent(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f"LoginEvent(user={self.user.username}, timestamp={self.timestamp})"