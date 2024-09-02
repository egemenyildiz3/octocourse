from django.db import models
from assignment_manager.models import Student,Group
from graderandfeedbacktool.models import Teachers
# Create your models here.


class ExamMetadata(models.Model):
    name = models.CharField(max_length=255)
    exam_date = models.DateTimeField()
    attempt = models.CharField(max_length=255)
    created_by_teacher = models.ForeignKey(Teachers, on_delete=models.CASCADE)
    comments = models.TextField()

class StudentExams(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam_metadata = models.ForeignKey(ExamMetadata, on_delete=models.CASCADE)
    grade = models.IntegerField()

class StudentExerciseAttempts(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exercise = models.ForeignKey('ExamExercises', on_delete=models.CASCADE)
    grade = models.IntegerField()

class StudentQuestionAttempts(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey('ExamQuestions', on_delete=models.CASCADE)
    points_awarded = models.IntegerField()

class ExamExercises(models.Model):
    exam_metadata = models.ForeignKey(ExamMetadata, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    number_of_questions = models.IntegerField()
    total_points = models.IntegerField()
    topic = models.CharField(max_length=255)
    author_teacher = models.ForeignKey(Teachers, on_delete=models.SET_NULL, null=True, blank=True)

class ExamQuestions(models.Model):
    exercise = models.ForeignKey(ExamExercises, on_delete=models.CASCADE)
    text = models.TextField()
    points = models.IntegerField()
    type = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    author_teacher = models.ForeignKey(Teachers, on_delete=models.SET_NULL, null=True, blank=True)


class BuddyCheck(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_time = models.DateTimeField()
    on_time = models.BooleanField()
    overall_performance = models.IntegerField()
    comments = models.TextField()

class BuddyCheckQuestion(models.Model):
    buddy_check = models.ForeignKey(BuddyCheck, on_delete=models.CASCADE)
    question_text = models.TextField()
    category = models.CharField(max_length=255)  # "attendance", "participation", "peer assessment"
    score = models.IntegerField()