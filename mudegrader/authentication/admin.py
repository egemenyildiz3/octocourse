from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, LoginEvent
from .forms import CustomUserCreationForm, CustomUserChangeForm
from authentication.models import Role


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('username', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Role'), {'fields': ('role', 'courses')}),
        (_('Gitlab ID'), {'fields': ('gitlab_id',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Role'), {'fields': ('role', 'courses')}),
    )
    actions = ['make_professor', 'make_ta']


@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'ip_address', 'user_agent')
    search_fields = ('user__username', 'ip_address', 'user_agent')
    list_filter = ('user', 'timestamp')
