from django.test import TestCase

from assignment_manager.forms import StudentForm


class StudentFormTest(TestCase):
    """Tests for the StudentForm."""

    def test_valid_form(self):
        """Test if StudentForm is valid with valid data."""
        form_data = {
            'net_id': 'student1',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'enrollment_year': 2022,
            'program': 'Computer Science',
            'msc_track': 'Data Science',
            'self_assessed_skill': 'Python',
            'nationality_type': 'American',
            'start_year_in_mude': 2023,
            'brightspace_id': 'JD123',
            'gitlab_id': 'john_doe',
            'public_ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB...',
        }
        form = StudentForm(data=form_data)
        self.assertTrue(form.is_valid())
