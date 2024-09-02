from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from assignment_manager.models import Course
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


class CustomUserCreationForm(UserCreationForm):
    courses = forms.ModelMultipleChoiceField(queryset=Course.objects.all(), required=False)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'courses')


class CustomUserChangeForm(UserChangeForm):
    courses = forms.ModelMultipleChoiceField(queryset=Course.objects.all(), required=False)

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'courses')


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')

        if username is not None and '@' in username:
            try:
                user = get_user_model().objects.get(email=username)
                cleaned_data['username'] = user.username
            except get_user_model().DoesNotExist:
                raise ValidationError("This email does not exist.")
        return cleaned_data

