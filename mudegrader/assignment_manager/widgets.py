# widgets.py
from django.forms.widgets import ClearableFileInput

class MultipleFileInput(ClearableFileInput):
    template_name = 'multiple_file_input.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['multiple'] = True
        return context
