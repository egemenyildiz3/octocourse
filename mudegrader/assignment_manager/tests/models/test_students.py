from django.test import TestCase

from assignment_manager.models import Student


class StudentsModelTest(TestCase):
    """Tests for the Students model."""

    def setUp(self):
        """Set up a student for testing."""
        self.student = Student.objects.create(
            first_name='Mohammed',
            last_name='Yusuf',
            email='mohammed@example.com',
            enrollment_year=2022,
            program='Computer Science',
            msc_track='Data Science',
            self_assessed_skill='Python',
            nationality_type='American',
            start_year_in_mude=2023,
            brightspace_id='MJ123',
            gitlab_id='mohammed_yusuf',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB...'
        )

    def test_student_creation(self):
        """Test creating a student with valid data."""
        self.assertEqual(self.student.first_name, 'Mohammed')
        self.assertEqual(self.student.last_name, 'Yusuf')
        self.assertEqual(self.student.email, 'mohammed@example.com')

