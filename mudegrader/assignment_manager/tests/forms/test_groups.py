from django.test import TestCase

from assignment_manager.factories import CourseFactory, AssignmentFactory
from assignment_manager.forms import GroupForm


class GroupFormTest(TestCase):
    """Tests for the GroupForm."""

    def test_valid_form(self):
        """Test if GroupForm is valid with valid data."""
        course = CourseFactory()
        assignment = AssignmentFactory(
            course=course
        )
        form_data = {
            'name': 'Test Group',
            'assignment_id': assignment,
        }
        form = GroupForm(data=form_data)
        self.assertTrue(form.is_valid())
