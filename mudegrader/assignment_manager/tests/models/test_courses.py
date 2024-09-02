from django.test import TestCase

from assignment_manager.models import Course
from authentication.models import CustomUser, Role


class CourseModelTest(TestCase):
    """Tests for the Course model."""

    def setUp(self):
        """Set up a course for testing."""
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

    def test_course_creation(self):
        """Test creating a course with valid data."""
        self.assertEqual(self.course.course_code, 'CS101')
        self.assertEqual(self.course.department, 'Computer Science')

