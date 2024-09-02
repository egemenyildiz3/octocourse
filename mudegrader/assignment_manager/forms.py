import datetime

from django import forms
from django.db import models

from .models import Student, Course, Assignment, Group, Comment, AssignmentUnit, Tasks, FeedbackTemplate
from assignment_manager.tag_model import Tag
from .widgets import MultipleFileInput

class StudentForm(forms.ModelForm):
    """Form for adding or editing student information."""
    class Meta:
        model = Student
        fields = [
            "net_id",
            "first_name",
            "last_name",
            "email",
            "enrollment_year",
            "program",
            "msc_track",
            "self_assessed_skill",
            "nationality_type",
            "start_year_in_mude",
            "brightspace_id",
            "gitlab_id",
            "public_ssh_key",
            "tags",
        ]
        widgets = {
            'tags': forms.SelectMultiple(),
        }


class GroupForm(forms.ModelForm):
    """Form for adding or editing group information."""
    class Meta:
        model = Group
        fields = ['name', 'tags']
        widgets = {
            'tags': forms.SelectMultiple(),
        }

class CourseForm(forms.ModelForm):
    """Form for adding or editing course information."""
    class Meta:
        model = Course
        fields = '__all__'
        exclude = ['gitlab_subgroup_id', 'created_by']
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        # automatically fill start and end year with current and next year
        self.fields['start_year'].initial = datetime.datetime.now().year
        self.fields['end_year'].initial = datetime.datetime.now().year + 1
        # add asterisk (*) to required fields
        for field_name, field in self.fields.items():
            if field.required:
                field.label = f"{field.label}*"

class CommentForm(forms.ModelForm):
    """Form for creating comments."""
    comment_text = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter your comment here...'}),
        required=True
    )
    class Meta:
        model = Comment
        fields = ['comment_text']

class TagForm(forms.ModelForm):
    background_color = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '#XXXXXX or leave blank to randomly generate..'})
    )
    class Meta:
        model = Tag
        fields = ['name', 'background_color']

class AssignmentForm(forms.ModelForm):
    """Form for adding or editing assignment information."""
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'total_points', 'is_individual', 'tags', 'due_date', 'server_check_interval']
        widgets = {
            # connect flatpickr to date fields
            'due_date': forms.DateTimeInput(attrs={'class': 'flatpickr', 'placeholder': 'YYYY-MM-DD HH:MM'}, format='%Y-%m-%d %H:%M'),
            # dropdown for tag
            'tags': forms.SelectMultiple(),
        }

    master_notebook_file = forms.FileField(required=False, widget=MultipleFileInput)
    non_master_notebook_file = forms.FileField(required=False, widget=MultipleFileInput)

    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        self.fields['total_points'].initial = 0 


class AssignmentUnitForm(forms.ModelForm):
    class Meta:
        model = AssignmentUnit
        fields = ['name', 'file', 'type', 'total_points', 'number_of_tasks', 'is_graded']

class TaskForm(forms.ModelForm):
    class Meta:
        model = Tasks
        fields = ['max_score']

class FeedbackTemplateForm(forms.ModelForm):
    class Meta:
        model = FeedbackTemplate
        fields = ['text']