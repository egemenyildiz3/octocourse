from django.test import TestCase
from unittest.mock import patch
from assignment_manager.models import AssignmentUnit, Assignment, Course
from django.conf import settings
from django.utils import timezone
from authentication.models import CustomUser, Role

# Assuming these are imported from your module
from services.path_utils import get_assignment_path, get_assignment_otter_generated_path, get_submission_path, get_feedback_path

class PathUtilsTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            role=Role.TEACHER,
        )
        self.user.set_password('testpassword')
        
        self.course_code = "test_course"
        self.assignment_title = "test_assignment"
        self.unit_name = "test_unit"
        
        self.course = Course.objects.create(
            course_code=self.course_code,
            description="Test Course",
            start_year=2021,
            end_year=2022,
            department="Computer Science",
            created_by=self.user
        )

        self.assignment = Assignment.objects.create(
            course=self.course,
            title=self.assignment_title,
            description="Test Assignment Description",
            start_date=timezone.now(),
            due_date=timezone.now(),
            gitlab_subgroup_id=1,
            total_points=100
        )
        
        self.assignment_unit = AssignmentUnit.objects.create(
            assignment=self.assignment,
            name=self.unit_name
        )

@patch.object(settings, 'ASSIGNMENTS_ROOT', '/fake/assignments/root')
def test_get_assignment_path(self):
    expected_path = f'/fake/assignments/root/{self.course_code.lower()}/{self.assignment_title}'
    actual_path = get_assignment_path(self.assignment)
    self.assertEqual(actual_path, expected_path)

@patch.object(settings, 'ASSIGNMENTS_OTTER_GENERATED_ROOT', '/fake/otter/generated/root')
def test_get_assignment_otter_generated_path(self):
    expected_path = f'/fake/otter/generated/root/{self.course_code.lower()}/{self.assignment_title}/{self.unit_name}'
    actual_path = get_assignment_otter_generated_path(self.assignment_unit)
    self.assertEqual(actual_path, expected_path)

@patch.object(settings, 'SUBMISSIONS_ROOT', '/fake/submissions/root')
def test_get_submission_path(self):
    expected_path = f'/fake/submissions/root/{self.course_code.lower()}/{self.assignment_title}'
    actual_path = get_submission_path(self.assignment)
    self.assertEqual(actual_path, expected_path)

@patch.object(settings, 'SUBMISSIONS_ROOT', '/fake/submissions/root')
def test_get_feedback_path(self):
    expected_path = f'/fake/submissions/root/{self.course_code.lower()}/{self.assignment_title}'
    actual_path = get_feedback_path(self.course_code, self.assignment_title)
    self.assertEqual(actual_path, expected_path)
