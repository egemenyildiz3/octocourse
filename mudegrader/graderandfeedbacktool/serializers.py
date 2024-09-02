from rest_framework import serializers
from .models import Teachers, Submissions, GradeHistory, TaskGrades, Feedback


class TeachersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teachers
        fields = ['id', 'first_name', 'last_name', 'email', 'department']


class SubmissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submissions
        fields = ['id', 'assignment_id', 'student_id', 'group_id', 'submission_time', 'file_path', 'grading_status',
                  'feedback']


class GradeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeHistory
        fields = ['id', 'grade_id', 'previous_points', 'new_points', 'changed_by_teacher_id', 'change_reason',
                  'date_changed']


class TaskGradesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskGrades
        fields = ['id', 'submission_id', 'question_id', 'points_received', 'graded_by_teacher_id', 'date_graded',
                  'grading_type']


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'grade_id', 'feedback_file_path', 'date_provided']
