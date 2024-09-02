from typing import Any
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.db.models import JSONField

from django.utils.html import escape

from assignment_manager.tag_model import Tag
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.signals import post_save
from django.dispatch import receiver




class Comment(models.Model):
    """Model for a single comment, linked to some other object."""
    # TODO: this needs to be added when authentication is in place
    author = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    comment_text = models.TextField()
    comment_time = models.DateTimeField(auto_now_add=True)
    # this way a comment can be related to anything we want to add comments to
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    class Meta:
        ordering = ['-comment_time']

class Student(models.Model):
    net_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    enrollment_year = models.IntegerField(blank=True, null=True)
    program = models.CharField(max_length=100, blank=True, null=True)
    comments = GenericRelation(Comment)
    event_history = models.ManyToManyField('Event', related_name='students', blank=True)
    msc_track = models.CharField(max_length=100, blank=True, null=True)
    self_assessed_skill = models.CharField(max_length=100, blank=True, null=True)
    nationality_type = models.CharField(max_length=100, blank=True, null=True)
    start_year_in_mude = models.IntegerField(blank=True, null=True)
    # todo: rename this to student number?
    brightspace_id = models.CharField(max_length=100, blank=True, null=True)
    gitlab_id = models.CharField(max_length=100, blank=True, null=True)
    public_ssh_key = models.CharField(max_length=100, blank=True, null=True)
    courses_enrolled = models.ManyToManyField('Course', related_name='enrolled_students', blank=True)
    tags = models.ManyToManyField('Tag', related_name="students", blank=True)
    
    summary_report_url = models.CharField(max_length=100) # new field

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.net_id})'

    def get_absolute_url(self):
        return reverse('student_details', kwargs={'pk': self.pk})

    def get_details_link_html(self):
        return f'<a class="details-link" href="{ self.get_absolute_url() }">{ escape(self.__str__()) }</a>'

    def get_version_control_url(self):
        # maybe there is a better way but this solves a circular import issue
        from services.gitlab_services import GitlabService
        gs = GitlabService()
        try:
            url = gs.get_student_url(student_gitlab_id=self.gitlab_id)

            return url
        except:
            return None
        
    def formatted_attributes(self):
        attributes = {
            'Net ID': self.net_id,
            'First Name': self.first_name,
            'Last Name': self.last_name,
            'Email': self.email,
            'Enrollment Year': self.enrollment_year,
            'Program': self.program,
            'MSc Track': self.msc_track,
            'Self-Assessed Skill': self.self_assessed_skill,
            'Nationality Type': self.nationality_type,
            'Start Year in MUDE': self.start_year_in_mude,
            'Brightspace ID': self.brightspace_id,
            'GitLab ID': self.gitlab_id,
            'Public SSH Key': self.public_ssh_key,
        }
        formatted_text = "\n".join([f"{key}: {value}" for key, value in attributes.items() if value])
        return formatted_text

class Course(models.Model):
    """Model to store information about courses."""
    id = models.AutoField(primary_key=True)
    # todo: course code should be case-insensitive
    #   we could also make a different type for this
    course_code = models.SlugField(max_length=250)
    description = models.TextField(null=True, blank=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    department = models.CharField(max_length=255, null=True, blank=True)
    gitlab_subgroup_id = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    selected_feedback_template = models.ForeignKey('FeedbackTemplate', on_delete=models.DO_NOTHING, blank=True, null=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course_code', 'start_year', 'end_year'], name='unique_fields')
        ]

    def __str__(self):
        return f"{self.course_code} {str(self.start_year)}/{str(self.end_year)}"
    
    @property
    def unique_name(self):
        return f'{self.course_code}-{str(self.start_year)}-{str(self.end_year)}'

    def get_version_control_url(self):
        # maybe there is a better way but this solves a circular import issue
        from services.gitlab_services import GitlabService
        gs = GitlabService()

        try:
            url = gs.get_course_url(course_gitlab_subgroup_id=self.gitlab_subgroup_id)
            return url
        except:
            return None

    def save(self, *args, **kwargs):
        # force the course code to always be upper case
        self.course_code = self.course_code.upper()

        for course in Course.objects.filter(course_code=self.course_code).exclude(pk=self.pk).all():
            if course.start_year == self.start_year and course.end_year == self.end_year:
                raise ValidationError(f"The course code {self.course_code} for years {self.start_year} to {self.end_year} is already in use.")
        super().save(*args, **kwargs)

# Weekday and Interval are used for automatic server-side retrieval of submissions
class Weekday(models.IntegerChoices):
    SUNDAY = 0, 'Sunday'
    MONDAY = 1, 'Monday'
    TUESDAY = 2, 'Tuesday'
    WEDNESDAY = 3, 'Wednesday'
    THURSDAY = 4, 'Thursday'
    FRIDAY = 5, 'Friday'
    SATURDAY = 6, 'Saturday'
class Interval(models.IntegerChoices):
    # the integer is the amount of hours
    NONE = -1, "None"
    DAY = 24, 'Day'
    WEEK = 168, 'Week'

class Assignment(models.Model):
    """Model to store information about assignments.
    Titles of assignments are validated to be link-friendly.
    """
    id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, related_name='assignments', on_delete=models.CASCADE)
    # TODO: Should this not just be name?
    title = models.SlugField(max_length=255)
    description = models.TextField(null=True, blank=True)
    # this field is necessary as the Comment model has a genericForeignKey
    comments = GenericRelation(Comment)
    event_history = models.ManyToManyField('Event', related_name='assignments', blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    total_points = models.IntegerField()
    # assignment_path = models.CharField(max_length=255, null=True, default="/")
    is_published = models.BooleanField(default=False)
    gitlab_subgroup_id = models.CharField(max_length=100, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="assignments", blank=True)
    is_individual = models.BooleanField(default=True)
    server_check_interval = models.IntegerField(choices=Interval.choices, default=Interval.DAY)

    extra_checks = JSONField(default=list, blank=True)

    class Meta:
        unique_together = ('course_id', 'title')

    @property
    def path_in_filesystem(self) -> str:
        from services.path_utils import get_assignment_path

        return get_assignment_path(self)

    @property
    def submission_path_in_filesystem(self) -> str:
        from services.path_utils import get_submission_path
        return get_submission_path(self)

    def __str__(self):
        return f"{self.title}"
    

    def get_version_control_url(self):
        # maybe there is a better way but this solves a circular import issue
        from services.gitlab_services import GitlabService
        gs = GitlabService()

        try:
            url = gs.get_assignment_url(assignment_gitlab_id=self.gitlab_subgroup_id)
            return url
        except:
            return None

@receiver(post_save, sender=Assignment)
def server_check_interval_update(sender, instance, created, **kwargs):
    if instance.pk:
        update_periodic_task(instance)

def update_periodic_task(instance: Assignment):

    task_name = f"asg.tasks.{instance.title}.periodic_check"
    try:
        task = PeriodicTask.objects.get(name=task_name)
    except PeriodicTask.DoesNotExist:
        task = None
    
    if instance.server_check_interval == Interval.NONE:
        if task:
            task.delete()
        return
    
    if instance.server_check_interval == Interval.DAY:
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        if not task:
            task = PeriodicTask.objects.create(
                name=task_name,
                task='asg.tasks.assignment_periodic_check_routine',
                interval=schedule,
                args=f"[{instance.id}]",
                expires=instance.due_date,
            )
        else:
            task.interval = schedule
            task.save()
        return
    
    if instance.server_check_interval == Interval.WEEK:
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=7,
            period=IntervalSchedule.DAYS,
        )
        if not task:
            task = PeriodicTask.objects.create(
                name=task_name,
                task='asg.tasks.assignment_periodic_check_routine',
                interval=schedule,
                args=f"[{instance.id}]",
                expires=instance.due_date,
            )
        else:
            task.interval = schedule
            task.save()
        return

class Group(models.Model):
    """Model to store information about assignment groups."""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assignments = models.ManyToManyField(Assignment,related_name='groups', blank= True)
    comments = GenericRelation(Comment)
    event_history = models.ManyToManyField('Event', related_name='groups', blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField('Tag', related_name="groups", blank=True)

    def get_absolute_url(self):
        return reverse('group_details', kwargs={'pk': self.pk})
    def __str__(self):
        return f"{self.name}"

    def get_details_link_html(self):
        return f'<a class="details-link" href="{ self.get_absolute_url() }">{ escape(self.__str__()) }</a>'



class GroupMember(models.Model):
    """Model to represent the membership of students in groups."""
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Student, related_name="memberships", on_delete=models.CASCADE)
    group_id = models.ForeignKey(Group, related_name='group_members', on_delete=models.CASCADE)
    join_date = models.DateTimeField(auto_now_add=True)
    leave_date = models.DateTimeField(null=True, blank=True)

class GroupRepo(models.Model):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    repository_id = models.IntegerField()
    assignment = models.ForeignKey(Assignment, related_name='group_repositories', on_delete=models.CASCADE)

class StudentRepo(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    repository_id = models.IntegerField()
    assignment = models.ForeignKey(Assignment, related_name='student_repositories', on_delete=models.CASCADE)

class AssignmentUnit(models.Model):
    """Model to represent units/files associated with a specific assignment"""
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='assignments/', max_length=500)
    type_choices = [
        ('master', 'Master Notebook'),
        ('non_master', 'Non-Master Notebook'),
    ]
    type = models.CharField(max_length=20, choices=type_choices, default="non_master")
    total_points = models.IntegerField(null=True, blank=True)  # New field
    number_of_tasks = models.IntegerField(null=True, blank=True)  # New field
    is_graded = models.BooleanField(default=False)  # New field
    is_gradable = models.BooleanField(default=True)  # New field
    #weight = models.FloatField(default=1.0)  # New field

class Event(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.DO_NOTHING)
    text = models.CharField(max_length=2480)
    name = models.CharField(max_length=100)
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # object_id = models.PositiveIntegerField()
    # content_object = GenericForeignKey('content_type', 'object_id')

class Tasks(models.Model):
    # should not have id because django creates id's by itself
    id = models.AutoField(primary_key=True)
    # use task_number instead of id
    task_number = models.IntegerField(null=True) # new field
    assignment_unit = models.ForeignKey(AssignmentUnit, on_delete=models.CASCADE)
    question_text = models.TextField(null=True, blank=True)
    question_path = models.CharField(max_length=255, null=True, blank=True)
    max_score = models.FloatField()  # Ensure this field exists # consider it as max_points
    is_auto_graded = models.BooleanField(default=False) # new field

class FeedbackTemplate(models.Model):
    text = models.TextField()
