from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(Teachers)
admin.site.register(Submissions)
admin.site.register(GradeHistory)
admin.site.register(TaskGrades)
admin.site.register(Feedback)
admin.site.register(SubmissionUnits)
