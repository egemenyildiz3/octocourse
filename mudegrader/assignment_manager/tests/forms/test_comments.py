from django.test import TestCase

from assignment_manager.forms import CommentForm


class CommentFormTest(TestCase):
    """Tests for the CommentForm."""

    def test_valid_form(self):
        """Test if CommentForm is valid with valid data."""
        form_data = {
            'comment_text': 'Test Comment! aBcDeF123!@#$! ',
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
