import hashlib

from django.db import models
from django.utils.html import format_html


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # Store colors as HEX codes
    background_color = models.CharField(max_length=7, blank=True)
    text_color = models.CharField(max_length=7, editable=False)
    course = models.ForeignKey('Course', related_name="tags", on_delete=models.CASCADE)

    @staticmethod
    def get_text_color(background_hex):
        # Convert hex to RGB
        r, g, b = int(background_hex[1:3], 16), int(background_hex[3:5], 16), int(background_hex[5:7], 16)

        # Calculate luminance
        r, g, b = [x/255.0 for x in (r, g, b)]
        r, g, b = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055) ** 2.4 for x in (r, g, b)]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Return black for light backgrounds and white for dark backgrounds
        return '#000000' if luminance > 0.5 else '#FFFFFF'

    def save(self, *args, **kwargs):
        bg_color=None
        if not self.background_color :
            hash_obj = hashlib.sha256(self.name.encode())
            bg_color = f"#{hash_obj.hexdigest()[:6]}"
            self.background_color = bg_color
        else:
            bg_color = self.background_color
        if self.background_color and not self.text_color:
            self.text_color = self.get_text_color(bg_color)
        super().save(*args, **kwargs)

    @property
    def to_html(self):
        return format_html(
            '<span class="tag" style="background-color: {}; color: {};">{}</span>',
            self.background_color,
            self.text_color,
            self.name
        )

    def __str__(self):
        return self.name