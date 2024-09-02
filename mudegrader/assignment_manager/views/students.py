from django.apps import apps
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.html import escape
from django.views.generic import DetailView

from assignment_manager.forms import StudentForm, Student, Course
from assignment_manager.views.comments import CommentMixin
from assignment_manager.forms import StudentForm, Student
from assignment_manager.models import Course
from assignment_manager.services.import_export import query_to_csv, import_any_model_csv
from assignment_manager.services.url_params import add_query_params
from assignment_manager.models import Event
from services.gitlab_services import GitlabService
from graderandfeedbacktool.feedback_service import send_summary_report

from assignment_manager.services.import_kiril_output import load_class


# Functions related to managing students
class StudentDetailView(CommentMixin, DetailView):
    """Render details of a specific student."""
    model = Student
    template_name = 'students/student_details.html'
    context_object_name = 'student'

def student_list(request):
    """Render a list of all students."""
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, id=course_id)
    students = course.enrolled_students.all()
    return render(request, 'students/students_list.html', {'students': students, 'course_id' : course_id})


def add_student(request):
    """Render a form to add a new student to the system."""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            course_id = request.session['selected_course_id']
            course = get_object_or_404(Course, id=course_id)
            student.courses_enrolled.add(course)
            #object_to_text = model_to_dict(student)
            object_to_text = student.formatted_attributes()
            event = Event.objects.create(
                name="Student: Created",
                user=request.user,
                text=f"Student created with the following values:\n{object_to_text}",
            )
            student.event_history.add(event)
            student.save()
            return redirect(student_list)
    else:
        form = StudentForm()

    return render(request, 'students/add_student.html', {'form': form})


def delete_student(request, student_id):
    """Delete a student from the system."""
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return redirect(request.META.get('HTTP_REFERER', 'students/students_list'))


def search_students(request):
    """Search for students by their first name."""
    if 'search_query' in request.GET:
        search_query = request.GET['search_query']
        students = Student.objects.filter(
            first_name__icontains=search_query
        )
    else:
        students = Student.objects.all()
    course_id = request.session['selected_course_id']
    return render(request, 'students/students_list.html', {'students': students, 'course_id' : course_id})


def filter_students(request):
    """
    Filter students based on a selected attribute and value.

    This function allows filtering students based on various attributes such as first name, last name, etc.
    It dynamically constructs the filter expression based on the selected attribute and value.
    """

    if request.method == 'GET':
        filter_param = request.GET.get('filter')
        value = request.GET.get('value')
        if filter_param and value:
            # Define the filter expression dynamically
            filter_expr = f"{filter_param}__icontains"
            # Filter students based on the selected attribute and value
            students = Student.objects.filter(**{filter_expr: value})
        else:
            students = Student.objects.all()
    else:
        # If the request method is not GET, return all students
        students = Student.objects.all()
    
    # Retrieve field names and labels of the Student model
    student_fields = {field.name: field.verbose_name for field in Student._meta.fields}
    course_id = request.session['selected_course_id']
    # Pass the filtered students and field names to the template
    return render(request, 'students/students_list.html', {'students': students, 'student_fields': student_fields, 'course_id' : course_id})


def edit_student(request, student_id):
    """Edit an existing student."""
    student = get_object_or_404(Student, id=student_id)
    old_dict = dict(model_to_dict(student))
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            new_student = form.save(commit=False)
            new_dict = model_to_dict(new_student)
            common_keys_with_diff_values = [(k, old_dict[k], new_dict[k]) for k in old_dict if k in new_dict and old_dict[k] != new_dict[k]]
            event_text = "Changed:"
            for key, old_val, new_val in common_keys_with_diff_values:
                # Escaping is very important here, as this string is turned into HTML directly
                # and otherwise we allow users to write arbitrary javascript code inside
                event_text += f'{key}: {escape(old_val)} -> {escape(new_val)}'
            event_text += ""
            event = Event.objects.create(
                name="Student: Edited",
                user=request.user,
                text=f'{event_text}',
            )
            new_student.event_history.add(event)
            new_student.save()
            print(student_id)
            return redirect(request.META.get('HTTP_REFERER', reverse('student_details', args=[student_id])))
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/edit_student.html', {'form': form, 'student': student})

def export_all_students_for_selected_course(request):
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, id=course_id)
    students = course.enrolled_students.all()
    response = query_to_csv(students)
    return response

@require_POST
def import_students_csv(request):
    """
    Only for POST request; request should have request.FILES.file with a csv file.
    Students are linked to the currently selected course.
    """
    file_list = request.FILES.getlist('file')
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, id=course_id)
    # removed_fields = ['courses_enrolled', 'comments']
    # for csv_file in file_list:
    #     objects = import_any_model_csv(csv_file=csv_file, model=Student, remove_fields=removed_fields)
    #     for obj in objects:
    #         obj.courses_enrolled.add(course)
    load_class(file_list[0], course)
    return redirect(request.META.get('HTTP_REFERER', reverse('student_list')))

def show_student_timeline(request, student_id):
    """
    Render a timeline of events for a specific student. This function retrieves a 
    student object using the student_id parameter and renders a timeline of events.
    
    :param request: The HTTP request object.
    :type request: HttpRequest
    
    :param student_id: The ID of the student to display the timeline for.
    :type student_id: int
    """
    gs = GitlabService()
    student = get_object_or_404(Student, id=student_id)
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, pk=course_id)
    list_of_commits = gs.get_student_commits(student)
    event_history = student.event_history.all()
    return render(request, 'students/student_timeline.html',
                  {
                      'student_id': student_id,
                      'list_of_commits' : list_of_commits,
                      'event_history': event_history,
                   })


def send_summary_report_feedback(request, course_id):
    """
    Send a summary report to all students in the course. This report includes 
    feedback on their assignments and grades from all assignments within the course.

    :param request: The HTTP request object.
    :type request: HttpRequest
    """
    
    if request.method == 'GET':
        send_summary_report(course_id)
        course = get_object_or_404(Course, id=course_id)
        students = course.enrolled_students.all()
        #return render(request, 'students/students_list.html', {'students': students})
        return redirect(student_list)