from django.contrib import admin
from django.utils.html import format_html

from assignment_manager.tag_model import Tag
from assignment_manager.models import (Student, Group, GroupMember, Course, Assignment, AssignmentUnit, Comment, Event,
                                       Tasks, StudentRepo, GroupRepo, FeedbackTemplate)
from django.contrib import admin


# Register your models here.
admin.site.register(Student)
admin.site.register(Group)
admin.site.register(GroupMember)
admin.site.register(Assignment)
admin.site.register(AssignmentUnit)
admin.site.register(Comment)
admin.site.register(Event)
admin.site.register(Tasks)
admin.site.register(StudentRepo)
admin.site.register(GroupRepo)
admin.site.register(FeedbackTemplate)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored_tag', 'background_color', 'course')

    def colored_tag(self, obj):
        """Display the tag with its respective background and text colors."""
        return format_html(
            '<span style="background-color: {}; color: {};">{}</span>',
            obj.background_color,
            obj.text_color,
            obj.name
        )
    colored_tag.short_description = "Tag Preview"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'description', 'start_year', 'end_year', 'department', 'get_created_by')
    search_fields = ('course_code', 'description', 'department', 'created_by__username')

    def get_created_by(self, obj):
        return obj.created_by.username if obj.created_by else 'N/A'
    get_created_by.short_description = 'Created By'
