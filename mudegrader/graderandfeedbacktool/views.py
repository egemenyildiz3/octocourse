from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.templatetags.static import static
from django.db.models import Max
import os

from django.contrib import messages
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from assignment_manager.models import Course
from .feedback_utils import generate_html_from_markdown_template
from graderandfeedbacktool.forms import TaskGradeForm, SubmissionUnitGradeForm, SubmissionGradeForm
from graderandfeedbacktool.models import *
from .populations import convert_mark_down_to_html, convert_notebook_to_pdf
from .grading_service import calculate_total_grade_for_submission
from assignment_manager.models import Course, Assignment, Student, Group, StudentRepo, GroupRepo
from .populations import populate_database_for_one_assignment
from .grading_service import calculate_total_grade_for_submission, validate_submission
from assignment_manager.models import Course, Assignment, Student, Group
from graderandfeedbacktool.models import Submissions, Feedback
from gitlabmanager.distribution_service import DistributionService
from django.core.exceptions import MultipleObjectsReturned


# list all the assignments related to this course
def grading_assignment_list(request):
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course_id=course).filter(is_published=True)
    return render(request, 'assignment_list.html', {'assignments': assignments})


# get all the students or groups who are related to the given assignment
def get_student_or_group_list(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, id=course_id)

    if assignment.is_individual:
        # return a list of reposities for this assignment which are all student repos
        student_repos = StudentRepo.objects.filter(assignment=assignment)
        # return a list of students associated with this repository
        temp_students = student_repos.values_list('student', flat=True).distinct()
        students = Student.objects.filter(id__in=temp_students)

        return render(request, 'student_list.html',
                      {'students': students, 'assignment': assignment, 'course': course_id})
    else:
        # return a list of repositories for this assignment which are all group repos
        group_repos = GroupRepo.objects.filter(assignment=assignment)
        # return a list of groups associated with this repository
        temp_groups = group_repos.values_list('group', flat=True).distinct()
        groups = Group.objects.filter(id__in=temp_groups)

        return render(request, 'group_list.html', {'groups': groups, 'assignment': assignment, 'course': course_id})


# HELPER METHOD
def search_student(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    total_students = Student.objects.filter(courses_enrolled=assignment.course_id)
    search_query = request.GET.get('search_query', '')
    if search_query:
        students = total_students.filter(first_name__icontains=search_query)
    else:
        students = total_students

    for student in students:
        try:
            student.latest_submission = student.submissions_set.latest('submission_time')
        except ObjectDoesNotExist:
            student.latest_submission = None

    return render(request, 'student_list.html',
                  {'students': students, 'search_query': search_query, 'assignment': assignment,
                   'is_search': bool(search_query)})


# HELPER METHOD
def filter_student(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    filter_param = request.GET.get('filter', '')
    value = request.GET.get('value', '')

    if filter_param and value:
        filter_expr = f"{filter_param}__icontains"
        students = Student.objects.filter(courses_enrolled=assignment.course_id, **{filter_expr: value})
    else:
        students = Student.objects.filter(courses_enrolled=assignment.course_id)

    for student in students:
        try:
            student.latest_submission = student.submissions_set.latest('submission_time')
        except ObjectDoesNotExist:
            student.latest_submission = None

    student_fields = {field.name: field.verbose_name for field in Student._meta.fields}

    return render(request, 'student_list.html',
                  {'students': students, 'student_fields': student_fields, 'filter_param': filter_param,
                   'filter_value': value, 'assignment': assignment, 'is_filter': bool(filter_param and value)})


# HELPER METHOD
def search_group(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    total_groups = Group.objects.filter(assignments=assignment)
    search_query = request.GET.get('search_query', 'rip')
    if search_query:
        groups = total_groups.filter(name__icontains=search_query)
    else:
        groups = total_groups

    for group in groups:
        try:
            group.latest_submission = group.submissions_set.latest('submission_time')
        except ObjectDoesNotExist:
            group.latest_submission = None

    return render(request, 'group_list.html',
                  {'groups': groups, 'search_query': search_query, 'assignment': assignment,
                   'is_search': bool(search_query)})


# HELPER METHOD
def filter_group(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    filter_param = request.GET.get('filter', '')
    value = request.GET.get('value', '')

    if filter_param and value:
        filter_expr = f"{filter_param}__icontains"
        groups = Group.objects.filter(assignments=assignment, **{filter_expr: value})
    else:
        groups = Group.objects.filter(assignments=assignment)

    for group in groups:
        try:
            group.latest_submission = group.submissions_set.latest('submission_time')
        except ObjectDoesNotExist:
            group.latest_submission = None

    group_fields = {field.name: field.verbose_name for field in Group._meta.fields}

    return render(request, 'group_list.html',
                  {'groups': groups, 'group_fields': group_fields, 'filter_param': filter_param,
                   'filter_value': value, 'assignment': assignment, 'is_filter': bool(filter_param and value)})


# HELPER METHOD
def collect_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course_id = assignment.course.id
    assignment_title = assignment.title
    assignment_gitlab_id = assignment.gitlab_subgroup_id

    distribution_service = DistributionService()

    # Gather submissions
    repository_list = distribution_service.gather_submissions(course_id, assignment_gitlab_id, assignment.course.course_code, assignment_title)

    if isinstance(repository_list, Exception):
        return JsonResponse({'status': 'error', 'message': f"Error gathering submissions: {repository_list}"})

    # Clone submissions
    failed_repositories = distribution_service.clone_submissions(repository_list, course_id, assignment_title)

    if failed_repositories:
        messages = [{'type': 'warning', 'message': 'Some repositories failed to clone'}]
        messages.extend([{'type': 'warning', 'message': f"Failed to clone repository: {repo['name']} ({repo['url']})"} for repo in failed_repositories])
        return JsonResponse({'status': 'warning', 'messages': messages})
    else:
        return JsonResponse({'status': 'success', 'message': 'All repositories cloned successfully'})


def student_submissions_list(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # Get the latest submission per assignment for the student
    latest_submissions = Submissions.objects.filter(student=student)\
                                            .values('assignment')\
                                            .annotate(latest_time=Max('submission_time'))\
                                            .order_by('-latest_time')
    
    submissions = []
    for entry in latest_submissions:
        submission = Submissions.objects.get(student=student, assignment=entry['assignment'], submission_time=entry['latest_time'])
        submissions.append(submission)
    
    context = {
        'student': student,
        'submissions': submissions,
    }
    
    return render(request, 'student_submissions_list.html', context)


def group_submissions_list(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    # Get the latest submission per assignment for the group
    latest_submissions = Submissions.objects.filter(group=group)\
                                            .values('assignment')\
                                            .annotate(latest_time=Max('submission_time'))\
                                            .order_by('-latest_time')
    
    submissions = []
    for entry in latest_submissions:
        submission = Submissions.objects.get(group=group, assignment=entry['assignment'], submission_time=entry['latest_time'])
        submissions.append(submission)
    
    context = {
        'group': group,
        'submissions': submissions,
    }
    
    return render(request, 'group_submissions_list.html', context)


# lists all the submissions by the given student (second argument: id) for the given assignment_id
def submission_list(request, assignment_id, stu_id: int):

    assignment = get_object_or_404(Assignment, id=assignment_id)
    # if the assignment is individual, fetch all the submission objects related to (this assignment_id, student_id)
    if assignment.is_individual:
        student = get_object_or_404(Student, id=stu_id)
        submissions = (Submissions.objects.filter(assignment=assignment, student=student)
                       .order_by('-submission_time'))
    else:
        group = get_object_or_404(Group, id=stu_id)      
        submissions = Submissions.objects.filter(assignment=assignment, group=group).order_by('-submission_time')
    
    first_submission = submissions.first()
    context = {
        'submissions': submissions,
        'assignment': assignment,
        'first_submission': first_submission
    }
    # all the generated submissions are given as a list `submissions` in the html context
    return render(request, 'submission_list.html', context)


def is_latest_submission(submission, submissions_list):
    # Find the submission with the latest submission_time
    latest_submission = max(submissions_list, key=lambda s: s.submission_time)
    # Check if the given submission is the latest one
    return latest_submission == submission

def submission_view(request, submission_id):

    submission = get_object_or_404(Submissions, id=submission_id)
    assignment = submission.assignment
    assignment_id = submission.assignment.id
    student_id = submission.student.id if submission.student else None
    group_id = submission.group.id if submission.group else None

    # Retrieve all submission units for the given submission
    submission_units = SubmissionUnits.objects.filter(submission=submission)
    # Determine the back URL which takes to the list of submissions by a student for an assignment
    back_url = reverse('submission_list', args=[assignment_id, student_id or group_id])

    if request.method == 'POST':
        # to handle the submission level grading
        toggle_state = request.POST.get('toggle_submission_form_state')
        print(f"-> -> submission level toggle state : {toggle_state}")
        if (toggle_state == '1'):
            submission_form = SubmissionGradeForm(request.POST, instance=submission)
            if submission_form.is_valid():
                # save the form
                submission_form.save()
                # update the toggle states
                submission.is_graded_at_this_level = True
                for submission_unit in submission_units:
                    submission_unit.is_graded_at_this_level = False
                    submission_unit.save()
                submission.save()
                # calculate the grade for the submission
                calculate_total_grade_for_submission(submission)
                return redirect('submission_view', submission_id=submission_id)
    else:
        submission_form = SubmissionGradeForm(instance=submission)

    context = {
        'submission': submission,
        'submission_id': submission_id,
        'submission_units': submission_units,
        'submission_form': submission_form,
        'back_url': back_url,
    }

    return render(request, 'submission_view.html', context)


def submission_unit_detail(request, unit_id):

    # fetch the submission unit
    submission_unit = get_object_or_404(SubmissionUnits, id=unit_id)
    submission = submission_unit.submission
    
    # converting file types to appropriate file paths
    if(submission_unit.converted_file_path is None):
        # if submission unit is a master type, convert to pdf
        if submission_unit.assignment_unit.type == "master":
            submission_unit.converted_file_path = convert_notebook_to_pdf(submission_unit.file_path)
            submission_unit.save()
        # if submission unit is not a master type
        else:
            submission_unit.converted_file_path = convert_mark_down_to_html(submission_unit.file_path)
            submission_unit.save()

    preview_file_path = submission_unit.converted_file_path

    # fetch all the task grade objects linked to this submission_unit
    task_grades = TaskGrades.objects.filter(submission_unit=submission_unit)

    # fetch the latest feedback by .first()
    # NOTE : There is only one feedback object per TaskGrade object
    for task_grade in task_grades:
        task_grade.feedback = Feedback.objects.filter(grade_id=task_grade.id).first()

    # Handle overall submission unit grade and feedback
    if request.method == 'POST':

        submission_unit_form_enabled = request.POST.get('submission_unit_form_enabled')
        print(f"-> -> submission unit level toggle state : {submission_unit_form_enabled}")
        if (submission_unit_form_enabled == '1'):
            submission_unit_form = SubmissionUnitGradeForm(request.POST, instance=submission_unit)
            if submission_unit_form.is_valid():
                # save the form 
                submission_unit_form.save()
                # update the toggle states
                submission_unit.is_graded_at_this_level = True
                submission.is_graded_at_this_level = False
                submission.save()
                submission_unit.save()
                # grade the submission
                calculate_total_grade_for_submission(submission)
                return redirect('submission_unit_detail', unit_id=unit_id)
        
        else:
            submission_unit.is_graded_at_this_level = False
            submission_unit.save()
            for task_grade in task_grades:
                feedback_text = request.POST.get(f'feedback_{task_grade.id}', '')
                
                # handle the manual grade given
                # persist the grade in the database
                # if the grade already exists, then update the grade
                if not task_grade.is_auto_graded:
                    grade = request.POST.get(f'grade_{task_grade.id}')
                    task_grade.points_received = grade
                    task_grade.is_graded = True
                task_grade.date_graded = datetime.now()
                task_grade.save()
                
                # handle the manual feedback given
                # if the feedback object already exists for this taskgrade,s
                # then update it else create a new Feedback object
                # Check if any feedback object exists related to this task_grade
                feedback_obj = Feedback.objects.filter(grade_id=task_grade.id).first()

                if feedback_obj:
                    ## If a feedback object exists
                    # Update the feedback_text attribute
                    feedback_obj.feedback_text = feedback_text
                    # Update the date_provided attribute
                    feedback_obj.date_provided = datetime.now()
                    feedback_obj.save()
                else:
                    ## If no feedback object exists
                    # Create a new Feedback object for this task_grade
                    Feedback.objects.create(
                        submission_id=submission_unit.submission,
                        grade_id=task_grade,
                        feedback_text=feedback_text,
                        feedback_file_path='',
                        date_provided=datetime.now()
                    )

            calculate_total_grade_for_submission(submission)
            return redirect('submission_unit_detail', unit_id=unit_id)
    else:
        submission_unit_form = SubmissionUnitGradeForm(instance=submission_unit)

    # Query for the next submission unit ID
    next_submission_unit = SubmissionUnits.objects.filter(
        submission=submission_unit.submission,
        id__gt=unit_id
    ).order_by('id').first()
    next_submission_unit_id = next_submission_unit.id if next_submission_unit else None

    # Query for the previous submission unit ID
    previous_submission_unit = SubmissionUnits.objects.filter(
        submission=submission_unit.submission,
        id__lt=unit_id
    ).order_by('-id').first()
    previous_submission_unit_id = previous_submission_unit.id if previous_submission_unit else None

    print(f"-> -> PREVIEW PATH : {preview_file_path}")

    context = {
        'submission_unit': submission_unit,
        'submission_unit_id': unit_id,
        'task_grades': task_grades,
        'submission_unit_form': submission_unit_form,
        'preview_file_path' : preview_file_path,
        'next_submission_unit_id': next_submission_unit_id,
        'previous_submission_unit_id': previous_submission_unit_id
    }

    return render(request, 'submission_unit_detail.html', context)


def reset_task_grade_values(request, submission_unit_id):
    pass


def reset_submission_unit_level_grades(request, submission_unit_id):
    pass

def reset_submission_level_grade(request, submission_id):
    pass

