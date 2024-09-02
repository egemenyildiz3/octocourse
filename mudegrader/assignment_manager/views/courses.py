from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from assignment_manager.forms import CourseForm, FeedbackTemplateForm
from assignment_manager.models import Course, FeedbackTemplate
from authentication.models import CustomUser
from assignment_manager.decorators import teacher_required

from services.gitlab_services import GitlabService

from assignment_manager.services.import_export import query_to_csv, import_any_model_csv
from assignment_manager.services.url_params import add_query_params
from graderandfeedbacktool.feedback_utils import generate_html_from_markdown_template


# Functions related to managing courses

class CourseDetailView(DetailView):
    """Render details of a specific course."""
    model = Course
    template_name = 'courses/course_details.html'
    context_object_name = 'course'


def course_list(request):
    """Render a list of all courses."""
    user = request.user
    if 'selected_course_id' in request.session:
        del request.session['selected_course_id']

    courses = user.courses.all()
    show_cookie_banner = 'cookie_consent' not in request.COOKIES
    context = {
        'courses': courses,
        'user': user,
        'show_cookie_banner': show_cookie_banner
    }
    return render(request, 'courses/course_list.html', context)


@teacher_required
def add_course(request):
    """Render a form to add a new course to the system."""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save(commit=False)
                    course.created_by = request.user
                    course.save()
                    request.user.courses.add(course)
                    gs = GitlabService()
                    gs.create_course(course)
                    return redirect(course_list)
            except Exception as e:
                error_message = f'Something went wrong while creating course. Check the admin panel. Error: {e}'
                messages.error(request,error_message)
                context = {
                    'form': form,
                }
                return render(request, 'courses/add_course.html', context)
        else:
            for error in form.errors.values():
                messages.error(request,error.as_text())
            context = {
                'form': form,
            }
            return render(request, 'courses/add_course.html', context)
    else:
        form = CourseForm()

    return render(request, 'courses/add_course.html', {'form': form})


def delete_course(request, course_id):
    """Delete a course from the system."""
    course = get_object_or_404(Course, id=course_id)
    gs = GitlabService()
    gs.remove_course(course)
    course.delete()
    return redirect('course_list')


def edit_course(request, pk):
    """Edit an existing course."""
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    gs = GitlabService()
                    gs.edit_course(course)
                    return redirect('course_details', pk=pk)
            except IntegrityError as e:
                error_message = f'Something went wrong while editing course. Check the admin panel. Error: {e}'
                messages.error(request,error_message )
                context = {
                    'form': form,
                }
                return render(request, 'courses/edit_course.html', context)
        else:
            for error in form.errors.values():
                messages.error(request,error.as_text())
            context = {
                'form': form,
            }
            return render(request, 'courses/edit_course.html', context)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/edit_course.html', {'form': form, 'course': course})


def export_all_courses(request):
    courses = Course.objects.all()
    response = query_to_csv(courses)
    return response

@require_POST
def import_courses_csv(request):
    """
    Only for POST request; request should have request.FILES.file with a csv file.
    Students are linked to the currently selected course.
    """
    file_list = request.FILES.getlist('file')
    removed_fields = ['tags', 'enrolled_students', 'assignments']
    for csv_file in file_list:
        import_any_model_csv(csv_file=csv_file, model=Course, remove_fields=removed_fields)
    return redirect(request.META.get('HTTP_REFERER', reverse('course_list')))

def staff_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    staff_members = course.staff.all()
    return render(request, 'courses/staff_list.html', {'course': course, 'staff_members': staff_members})


def feedback_template_view(request, course_id: int, template_id=None):
    template_string = ""
    if request.method == 'POST':
        if template_id:
            template = get_object_or_404(FeedbackTemplate, pk=template_id)
            form = FeedbackTemplateForm(request.POST, instance=template)
        else:
            form = FeedbackTemplateForm(request.POST)

        if form.is_valid():
            template = form.save()
            template_string = template.text
            if not template_id:
                return redirect(reverse('feedback_template_view', args=[course_id, template.id]))
    else:
        if template_id:
            template = get_object_or_404(FeedbackTemplate, pk=template_id)
            form = FeedbackTemplateForm(instance=template)
            template_string = template.text
        else:
            form = FeedbackTemplateForm()
    context_dict = {
        'thing': 'jasper',
        'stuff': 'eijkenboom',
    }
    result = generate_html_from_markdown_template(template_string, context_dict)
    templates = FeedbackTemplate.objects.all()
    context = {
        'form': form,
        'templates': templates,
        'result': result,
        'course_id': course_id,
        'fields': context_dict.keys(),
    }
    return render(request, 'courses/feedback_template_manager.html', context)
