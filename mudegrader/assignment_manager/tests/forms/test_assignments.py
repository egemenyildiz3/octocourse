from django.test import TestCase

from assignment_manager.forms import AssignmentForm
from assignment_manager.models import Interval


class AssignmentFormTest(TestCase):
    """Tests for the AssignmentForm."""

    def test_valid_form(self):
        """Test if AssignmentForm is valid with valid data."""
        form_data = {
            'title': 'Test_Assignment',
            'description': 'This is a test assignment',
            'total_points': 100,
            'master_notebook_file': None,
            'non_master_notebook_file': None,
            'server_check_interval': Interval.DAY,
        }
        form = AssignmentForm(data=form_data)
        self.assertTrue(form.is_valid())