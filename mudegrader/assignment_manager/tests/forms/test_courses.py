from django.test import TestCase

from assignment_manager.forms import CourseForm


class CourseFormTest(TestCase):
    """Tests for the CourseForm."""

    def test_valid_form(self):
        """Test if CourseForm is valid with valid data."""
        form_data = {
            'course_code': 'CS101',
            'description': 'Introduction to Computer Science',
            'start_year': 2022,
            'end_year': 2023,
            'department': 'Computer Science',
        }
        form = CourseForm(data=form_data)
        self.assertTrue(form.is_valid())