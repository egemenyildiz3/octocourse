from django.db import models
from assignment_manager.models import Group, Assignment, Student, AssignmentUnit, Tasks

class Teachers(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    department = models.CharField(max_length=100)


class Submissions(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=255) # this is the file path for the feedback
    feedback = models.TextField(blank=True, null=True)
    is_passed = models.BooleanField(default=False)
    # --- TAGS ---
    tags = models.ManyToManyField('assignment_manager.Tag', related_name="submissions", blank=True) # new field
    # --- GRADE/POINTS ---
    # constraint = total_grade should be sum of total_grade of each submission_unit
    total_grade = models.FloatField(null=True, blank=True)
    total_points = models.FloatField(null=True, blank=True)
    auto_graded_grade = models.FloatField(null=True, blank=True) # new field

    # --- GRADING STATUS ---
    is_graded = models.BooleanField(default=False) # new field

    # --- GRADING LEVEL ---
    is_graded_at_this_level = models.BooleanField(default=False) # new field

    # --- NOT USED ---
    # dont use grading_status; instead use is_graded
    grading_status = models.TextField(default='Not Graded')
    

class SubmissionUnits(models.Model):
    id = models.AutoField(primary_key=True)
    submission = models.ForeignKey(Submissions, related_name='submission_units', on_delete=models.CASCADE)
    assignment_unit = models.ForeignKey(AssignmentUnit, on_delete=models.CASCADE)
    submission_time = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=255)
    feedback = models.TextField(blank=True, null=True)
    converted_file_path = models.CharField(null=True, max_length=255, default=None)

    # --- GRADE and POINTS ---
    total_grade = models.FloatField(null=True, blank=True)
    # total_points recevied for the submission unit
    total_points = models.IntegerField(null=True)  # new field
    auto_graded_grade = models.FloatField(null=True, blank=True) # new field
    # --- NUMBER OF TASKS ---
    number_of_tasks = models.IntegerField(null=True)  # new field
    # --- GRADING STATUS ---
    is_graded = models.BooleanField(default=False)  # new field
    # --- GRADING LEVEL ---
    is_graded_at_this_level = models.BooleanField(default=False) # new field

    # --- NOT USED ---
    # dont use grading_status; instead use is_graded
    grading_status = models.TextField(default='Not Graded')


class TaskGrades(models.Model):
    
    # should be task_grade_number
    question_id = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE)
    submission_unit = models.ForeignKey(SubmissionUnits, related_name='task_grades', on_delete=models.CASCADE)
    graded_by_teacher_id = models.ForeignKey('Teachers', on_delete=models.CASCADE, null=True, blank=True)
    date_graded = models.DateTimeField(null=True, blank=True)
    
    # --- GRADE/POINTS ---
    max_points = models.FloatField() # new field
    points_received = models.FloatField(blank=True)
    # --- GRADING TYPE ---
    is_auto_graded = models.BooleanField(default=False) # new field
    # --- GRADING STATUS ---
    is_graded = models.BooleanField(default=False)  # new field

    # --- NOT USED ---
    grading_type = models.CharField(max_length=100, null=True, blank=True)

class Feedback(models.Model):
    submission_id = models.ForeignKey('Submissions', on_delete=models.CASCADE, null=True, blank=True,related_name='feedbacks')
    grade_id = models.ForeignKey('TaskGrades', related_name='grade_feedback', on_delete=models.CASCADE, null=True, blank=True)
    feedback_text = models.TextField(null=True, blank=True)
    feedback_file_path = models.CharField(max_length=255, null=True, blank=True)
    date_provided = models.DateTimeField()

class GradeHistory(models.Model):
    grade_id = models.ForeignKey('TaskGrades', on_delete=models.CASCADE, null=True, blank=True)
    previous_points = models.IntegerField()
    new_points = models.IntegerField()
    changed_by_teacher_id = models.ForeignKey('Teachers', on_delete=models.CASCADE, null=True, blank=True)
    change_reason = models.TextField()
    date_changed = models.DateTimeField()
