

from django.test import TestCase
from unittest.mock import patch, MagicMock
from graderandfeedbacktool.feedback_utils import generate_html_from_markdown_template, apply_template, markdown_to_html

class MarkdownToHtmlTests(TestCase):

    def test_apply_template(self):
        template_string = "Hello, {{ name }}!"
        context_dict = {"name": "World"}
        expected_result = "Hello, World!"
        result = apply_template(template_string, context_dict)
        self.assertEqual(result, expected_result)

    @patch('pypandoc.convert_text')
    def test_markdown_to_html(self, mock_convert_text):
        markdown_text = "# Heading"
        expected_html = "<h1>Heading</h1>"
        mock_convert_text.return_value = expected_html
        result = markdown_to_html(markdown_text)
        mock_convert_text.assert_called_once_with(markdown_text, 'html', format='md')
        self.assertEqual(result, expected_html)

    @patch('pypandoc.convert_text')
    def test_generate_html_from_markdown_template(self, mock_convert_text):
        template_string = "# Hello, {{ name }}!"
        context_dict = {"name": "World"}
        expected_markdown = "# Hello, World!"
        expected_html = "<h1>Hello, World!</h1>"
        mock_convert_text.return_value = expected_html

        result = generate_html_from_markdown_template(template_string, context_dict)
        mock_convert_text.assert_called_once_with(expected_markdown, 'html', format='md')
        self.assertEqual(result, expected_html)
