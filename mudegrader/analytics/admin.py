from django.contrib import admin
from .models import ExamMetadata, StudentExams, StudentExerciseAttempts, StudentQuestionAttempts, ExamExercises, ExamQuestions, BuddyCheck, BuddyCheckQuestion

# Register your models here.

admin.site.register(ExamMetadata)
admin.site.register(StudentExams)
admin.site.register(StudentExerciseAttempts)
admin.site.register(StudentQuestionAttempts)
admin.site.register(ExamExercises)
admin.site.register(ExamQuestions)
admin.site.register(BuddyCheck)
admin.site.register(BuddyCheckQuestion)