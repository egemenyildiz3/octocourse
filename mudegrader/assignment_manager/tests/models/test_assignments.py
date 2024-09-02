from django.test import TestCase

from assignment_manager.models import Course, Assignment, AssignmentUnit
from django.utils import timezone
from datetime import timedelta
from authentication.models import CustomUser, Role


class AssignmentModelTest(TestCase):
    """Tests for the Assignment model."""

    def setUp(self):
        """Set up an assignment for testing."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.course = Course.objects.create(
            course_code='CS101',
            description='Introduction to Computer Science',
            start_year=2022,
            end_year=2023,
            department='Computer Science',
            created_by=self.user
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            title='Arslan',
            description='First assignment',
            start_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=7),
            total_points=100,
            is_published=True
        )

    def test_assignment_creation(self):
        """Test creating an assignment with valid data."""
        self.assertEqual(self.assignment.title, 'Arslan')
        self.assertTrue(self.assignment.is_published)



class AssignmentUnitModelTest(TestCase):
    """Tests for the AssignmentUnit model."""

    def setUp(self):
        """Set up an assignment unit for testing."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.course = Course.objects.create(
            course_code='CS101',
            description='Introduction to Computer Science',
            start_year=2022,
            end_year=2023,
            department='Computer Science',
            created_by=self.user
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            title='Arslan',
            description='First assignment',
            start_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=7),
            total_points=100,
            is_published=True
        )
        self.assignment_unit = AssignmentUnit.objects.create(
            assignment=self.assignment,
            name='Egeman',
            file='path/to/file',
            type='master'
        )

    def test_assignment_unit_creation(self):
        """Test creating an assignment unit with valid data."""
        self.assertEqual(self.assignment_unit.name, 'Egeman')
        self.assertEqual(self.assignment_unit.type, 'master')
