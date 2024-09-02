from django import forms
from .models import TaskGrades, Feedback, SubmissionUnits, Submissions


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        widgets = {
            'date_provided': forms.DateInput(attrs={'type': 'date'})
        }
        fields = ['feedback_file_path', 'date_provided']


class TaskGradeForm(forms.ModelForm):
    class Meta:
        model = TaskGrades
        fields = ['question_id', 'points_received', 'graded_by_teacher_id', 'grading_type']

class SubmissionUnitGradeForm(forms.ModelForm):
    class Meta:
        model = SubmissionUnits
        fields = ['total_grade', 'feedback']

# todo: rename this to SubmissionForm?
class SubmissionGradeForm(forms.ModelForm):
    class Meta:
        model = Submissions
        fields = ['tags', 'total_grade', 'feedback']