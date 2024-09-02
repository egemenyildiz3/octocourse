import json
import logging
import os
import shutil
import subprocess
import time
import zipfile
from django.http import FileResponse, Http404
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from assignment_manager.views.comments import CommentMixin
from assignment_manager.models import AssignmentUnit, Assignment, Course, Group, Tasks, Student, StudentRepo, GroupRepo # Updated import
from assignment_manager.forms import AssignmentForm
from django.contrib import messages
from services.gitlab_services import GitlabService

from assignment_manager.services.import_export import query_to_csv, import_any_model_csv
from assignment_manager.services.url_params import add_query_params
from services.path_utils import get_assignment_otter_generated_path


# Functions related to managing assignments

class AssignmentDetailView(CommentMixin, DetailView):
    """Render details of a specific assignment"""
    model = Assignment
    template_name = 'assignments/assignment_details.html'
    context_object_name = 'assignment'


def publish_assignment(request, assignment_id):
    """Publish an assignment.
    
    This function gets an assignment that is stored in the database and run otter assign method in all of its master units.
    it does that by filtering the unit assignments that are master, and it does this as a pre-step before publishing the 
    assignment to the students because then the students get the student notebook, not the master notebook.

    :param request: The HTTP request object
    :type request: HttpRequest

    :param assignment_id: The ID of the assignment to publish
    :type assignment_id: int

    :return: A redirect response to the assignment details page
    :rtype: HttpResponseRedirect
    """

    assignment = get_object_or_404(Assignment, id=assignment_id)

    if(assignment.is_published):
        messages.warning(request, f'Failed to publish assignment {assignment.title}! This assignment is already published! Try refreshing the page')
        return redirect(reverse('assignment_details', args=[assignment_id]))
        # Get file paths and names for the assignment
    current_dt = timezone.now()
    if assignment.due_date <= current_dt:
        messages.error(request, 'Cannot publish assignment after due date.')
        return redirect(reverse('assignment_details', args=[assignment_id]))
        #TODO popup needed here as well @jasper
  
    if assignment.is_individual:
        #TODO: fix error popup, not visible and also the loading screen should be removed
        student_list = Student.objects.filter(courses_enrolled = get_object_or_404(Course, pk=request.session['selected_course_id']))
        if len(student_list) < 1:
            messages.error(request, 'No students enrolled in the course. Cannot publish assignment.')
            return redirect(reverse('assignment_details', args=[assignment_id]))
    else:
        group_list = Group.objects.filter(course = get_object_or_404(Course, pk=request.session['selected_course_id']))
        if len(group_list) < 1:
            messages.error(request, 'No groups in the course. Cannot publish assignment.')
            return redirect(reverse('assignment_details', args=[assignment_id]))
        
    assignment_units = AssignmentUnit.objects.filter(assignment=assignment)
    for unit in assignment_units:
        if unit.type == 'master':
            run_otter_on_assignment_unit_master(unit)
            copy_and_override_files(unit)

    if assignment.extra_checks:
        copy_validation_package(assignment)

    time.sleep(5)

    gs = GitlabService()
    course = get_object_or_404(Course, pk=request.session['selected_course_id'])
    if(assignment.gitlab_subgroup_id is None): #This checks if the assignment was created before
        gs.add_assignment(assignment)

    
    gs.publish_assignment_existing_groups(assignment)
    messages.success(request, f"Succesfully published assignment {assignment.title}!")


    # remove old one before publishing (TEMP)
    gs.remove_periodic_check_routine(assignment)
    gs.setup_periodic_check_routine(assignment)

    assignment.is_published = True
    assignment.save()

    return redirect(reverse('assignment_details', args=[assignment_id]))

def publish_manually(request, assignment_id):
    """
    Goes to view of manually publishing an assignment. Details of the page
    changes whether the assignment was a group or indivdual based one.

    :param assignment_id: ID of the assignment that is going to be published via this method
    :type assignment_id: int

    :return: A render of the page that is going to be used for manual publishing
    :rtype: HttpResponse
    """

    assignment = get_object_or_404(Assignment, id=assignment_id)
    is_indi = assignment.is_individual
    page_name = None
    name_var = None
    missing_objects = None
    if is_indi:
        page_name = "Manual distribution for this Individual Assignment!"
        student_repos = StudentRepo.objects.filter(assignment=assignment)
        if(student_repos.exists()):
            student_ids = student_repos.values_list('student', flat=True).distinct()
            name_var = "Student"
            missing_objects = Student.objects.exclude(
                    id__in=student_ids
                ).distinct()
        else:
            missing_objects = Student.objects.filter(courses_enrolled = get_object_or_404(Course, pk=request.session['selected_course_id']))
    else: 
        page_name = "Manual distribution for this Group Assignment!"
        group_repos = GroupRepo.objects.filter(assignment=assignment)
        if(group_repos.exists()):
            group_ids = group_repos.values_list('group', flat=True).distinct()
            name_var = "Group"
            missing_objects = Group.objects.exclude(
                id__in=group_ids
            ).distinct()
        else:
            missing_objects = Group.objects.all()
        

    return render(request, 'assignments/publish_manually.html', {
        'assignment' : assignment,
        'page_name' : page_name,
        'name_var' : name_var,
        'missing_objects' : missing_objects,
        'is_indi' : is_indi
        })

def publish_manually_individual(request, assignment_id, student_id):
    """
    Publishes an assignment to a specific student. This function is called when the user
    clicks the publish button on the manual publish page for individual assignments. 

    :param request: The HTTP request object
    :type request: HttpRequest

    :param assignment_id: The ID of the assignment to publish
    :type assignment_id: int

    :param student_id: The ID of the student to publish the assignment to
    :type student_id: int

    :return: A redirect response to the manual publish page
    :rtype: HttpResponseRedirect
    """
    student = get_object_or_404(Student, id=student_id)
    assignment = get_object_or_404(Assignment, id=assignment_id)
    gs = GitlabService()
    if(assignment.gitlab_subgroup_id is None):
        gs.add_assignment(assignment)
    success, error_messages = gs.publish_manually_individual_assignment(assignment, student)
    if success:
        messages.success(request, f'Successfully published assignment {assignment.title} to {student.first_name} {student.last_name}.')
    else:
        messages.error(request, f'Failed to publish assignment {assignment.title} to {student.first_name} {student.last_name}. {error_messages}')
    return publish_manually(request, assignment.id)

def publish_manually_group(request, assignment_id, group_id):
    """
    Publishes an assignment to a specific group. This function is called when the user
    clicks the publish button on the manual publish page for group assignments.

    :param request: The HTTP request object
    :type request: HttpRequest

    :param assignment_id: The ID of the assignment to publish
    :type assignment_id: int

    :param group_id: The ID of the group to publish the assignment to
    :type group_id: int

    :return: A redirect response to the manual publish page
    :rtype: HttpResponseRedirect
    """
    group = get_object_or_404(Group, id=group_id)
    assignment = get_object_or_404(Assignment, id=assignment_id)
    gs = GitlabService()
    if(assignment.gitlab_subgroup_id is None):
        gs.add_assignment(assignment)
    success, error_messages = gs.publish_manually_group_assignment(assignment, group)
    if success:
        messages.success(request, f'Successfully published assignment {assignment.title} to {group.name}.')
        if error_messages:
            messages.warning(request, f'{error_messages}')
    else:
        messages.error(request, f'Failed to publish assignment {assignment.title} to {group.name}. {error_messages}')
    return publish_manually(request, assignment_id)


def run_otter_on_assignment_unit_master(unit):
    """Run Otter on the given assignment unit.

    This function runs otter assign on the master notebook to generate a student notebook file for a specified assignment unit. 
    It creates a requirements.txt file in the assignment unit's directory so that otter can operate, 
    then runs the `otter assign` command to produce the output files.

    TODO: Improve error handling to properly log or handle subprocess.CalledProcessError.

    :param unit: The assignment unit to run Otter on
    :type unit: AssignmentUnit

    :return: The output of the otter assign command
    :rtype: str
    """
    # make the output directory path
    output_directory = get_assignment_otter_generated_path(unit)

    # Get the directory containing the assignment unit's file
    assignment_unit_dir = os.path.dirname(unit.file.path)

    # Create a requirements.txt file in the same directory as the assignment unit's file
    requirements_file_path = os.path.join(assignment_unit_dir, "requirements.txt")
    with open(requirements_file_path, 'w', encoding='utf-8') as requirements_file:
        requirements_file.write("tqdm")

    # prepare the command
    command = ["otter", "assign"]
    # Add the assignment file path as an argument
    command.append(unit.file.path)
    # Add the output directory as the last argument
    command.append(output_directory)

    try:
        otter_output = subprocess.run(command, check=True, capture_output=True, text=True)
        otter_output_text = otter_output.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running otter assign: {e}")
        otter_output_text = e.stdout + "\n" + e.stderr

    return otter_output_text


def assignment_list(request, course_id):
    """
    Render a list of assignments for a specific course.
    
    :param request: The HTTP request object
    :type request: HttpRequest

    :param course_id: The ID of the course to list assignments for
    :type course_id: int

    :return: A response with the assignment list
    :rtype: HttpResponse
    """
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course)

    # Set the selected course in session
    request.session['selected_course_id'] = course_id
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments, 'course': course})




def add_assignment_units(request, assignment):
    """
    Add assignment units to an assignment. This function retrieves the POST data for 
    the assignment units, creates the units, and adds tasks to each unit.

    :param request: The HTTP request object
    :type request: HttpRequest

    :param assignment: The assignment to add units to
    :type assignment: Assignment
    """
    unit_prefix = 'units-'
    units_data = []
    unit_keys = [key for key in request.POST if key.startswith(unit_prefix) and key.endswith('-name')]

    print("unit_keys:", unit_keys)  # Debug: List of unit keys found in POST data

    for key in unit_keys:
        index = key[len(unit_prefix):-len('-name')]
        units_data.append({
            'index': index,
            'name': request.FILES.get(f'units-{index}-file').name if request.FILES.get(f'units-{index}-file') else request.POST.get(f'units-{index}-name'),
            'file': request.FILES.get(f'units-{index}-file'),
            'type': request.POST.get(f'units-{index}-type'),
            'total_points': request.POST.get(f'units-{index}-total_points'),
            'number_of_tasks': request.POST.get(f'units-{index}-number_of_tasks'),
            'is_graded': request.POST.get(f'units-{index}-is_graded') == 'true',
        })

    print("units_data:", units_data)  # Debug: Data collected for each unit

    for unit_data in units_data:
        print("Processing unit_data:", unit_data)  # Debug: Data for the current unit being processed
        if unit_data['name']:
            unit = AssignmentUnit.objects.create(
                assignment=assignment,
                name=unit_data['name'],
                file=unit_data['file'],
                type=unit_data['type'],
                total_points=unit_data['total_points'],
                number_of_tasks=unit_data['number_of_tasks'],
                is_graded=unit_data['is_graded'],
            )
            print("Created unit:", unit)  # Debug: Confirm the unit creation
            add_tasks(request, unit, unit_data['index'])


def save_or_update_assignment_units(request, assignment):
    """
    Save or update assignment units for an assignment. This function retrieves the POST data for
    the assignment units, updates existing units, creates new units, and updates tasks 
    for each unit.

    :param request: The HTTP request object
    :type request: HttpRequest

    :param assignment: The assignment to save or update units for
    :type assignment: Assignment
    """
    unit_prefix = 'units-'
    units_data = []
    unit_keys = [key for key in request.POST if key.startswith(unit_prefix) and key.endswith('-name')]

    for key in unit_keys:
        index = key[len(unit_prefix):-len('-name')]
        units_data.append({
            'index': index,
            'name': request.FILES.get(f'units-{index}-file').name if request.FILES.get(f'units-{index}-file') else request.POST.get(f'units-{index}-name'),
            'file': request.FILES.get(f'units-{index}-file'),
            'type': request.POST.get(f'units-{index}-type'),
            'total_points': request.POST.get(f'units-{index}-total_points'),
            'number_of_tasks': request.POST.get(f'units-{index}-number_of_tasks'),
            'is_graded': request.POST.get(f'units-{index}-is_graded') == 'true',
            'id': request.POST.get(f'units-{index}-id'),  # Get the unit ID if it exists
        })

    for unit_data in units_data:
        if unit_data['id']:  # Update existing unit
            unit = AssignmentUnit.objects.get(id=unit_data['id'])
            unit.name = unit_data['name']
            unit.type = unit_data['type']
            unit.total_points = unit_data['total_points']
            unit.number_of_tasks = unit_data['number_of_tasks']
            unit.is_graded = unit_data['is_graded']
            if unit_data['file']:
                unit.file = unit_data['file']
            unit.save()
        else:  # Create new unit
            unit = AssignmentUnit.objects.create(
                assignment=assignment,
                name=unit_data['name'],
                file=unit_data['file'],
                type=unit_data['type'],
                total_points=unit_data['total_points'],
                number_of_tasks=unit_data['number_of_tasks'],
                is_graded=unit_data['is_graded'],
            )
        update_tasks(request, unit, unit_data['index'])



def add_tasks(request, unit, unit_index):
    """
    Add tasks to an assignment unit. This function retrieves the POST data for the tasks,
    creates the tasks, and adds them to the unit.

    :param request: The HTTP request object
    :type request: HttpRequest

    :param unit: The assignment unit to add tasks to
    :type unit: AssignmentUnit

    :param unit_index: The index of the unit in the POST data
    :type unit_index: int
    """
    
    number_of_tasks = int(request.POST.get(f'units-{unit_index}-number_of_tasks', 0))
    tasks_data = [
        {
            'task_number': i + 1,
            'max_score': request.POST.get(f'units-{unit_index}-tasks-{i}-max_score'),
            'question_text': request.POST.get(f'units-{unit_index}-tasks-{i}-question_text'),
            'question_path': request.POST.get(f'units-{unit_index}-tasks-{i}-question_path'),
            'is_auto_graded': request.POST.get(f'units-{unit_index}-tasks-{i}-is_auto_graded') == 'true'
        }
        for i in range(number_of_tasks)
    ]
    print(tasks_data)
    for task_data in tasks_data:
        if task_data['max_score']:
            Tasks.objects.create(
                assignment_unit=unit,
                task_number=task_data['task_number'],
                max_score=task_data['max_score'],
                question_text=task_data.get('question_text'),
                question_path=task_data.get('question_path'),
                is_auto_graded=task_data['is_auto_graded']
            )


def edit_assignment(request, pk):
    """
    Edit an assignment. This function retrieves the assignment by ID, retrieves the assignment
    units associated with the assignment, and renders the assignment edit form.

    :param request: The HTTP request object
    :type request: HttpRequest

    :param pk: The ID of the assignment to edit
    :type pk: int

    :return: A response with the assignment edit form
    :rtype: HttpResponse 
    """
    assignment = get_object_or_404(Assignment, pk=pk)
    assignment_units = AssignmentUnit.objects.filter(assignment=assignment)
    course_id = request.session.get('selected_course_id')

    # Get folder structure for rendering
    folder_tree = get_folder_structure(assignment.path_in_filesystem)
    rendered_folder_tree = render_tree(folder_tree, assignment.path_in_filesystem)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            edited_assignment = form.save(commit=False)
            form.save_m2m()  # Save the tags
            save_or_update_assignment_units(request, edited_assignment)
            edited_assignment.save()

            # Handle uploaded files
            handle_uploaded_files(request, edited_assignment)
            
            if is_ajax(request):
                return JsonResponse({'assignment_id': edited_assignment.id}, status=200)
            else:
                referer_url = request.META.get('HTTP_REFERER', reverse('assignment_list', args=[course_id]))
                url = redirect(add_query_params(referer_url, {'saved': 'true'}))
                return url
    else:
        form = AssignmentForm(instance=assignment)
        # Populate the tag dropdown
        course = get_object_or_404(Course, pk=course_id)
        form.fields['tags'].queryset = course.tags.all()

    context = {
        'form': form,
        'assignment_units': assignment_units,
        'assignment': assignment,
        'rendered_folder_tree': rendered_folder_tree,
    }
    return render(request, 'assignments/edit_assignment.html', context)


    


def update_tasks(request, unit, unit_index):
    """
    Update tasks for an assignment unit. This function retrieves the existing tasks for the unit,
    updates the existing tasks, creates new tasks, and deletes any tasks that were not included
    in the update.

    :param request: The HTTP request object
    :type request: HttpRequest

    :param unit: The assignment unit to update tasks for
    :type unit: AssignmentUnit

    :param unit_index: The index of the unit in the POST data
    :type unit_index: int

    :return: None
    :rtype: None
    """
    existing_tasks = {task.id: task for task in Tasks.objects.filter(assignment_unit=unit)}
    number_of_tasks = int(request.POST.get(f'units-{unit_index}-number_of_tasks', 0))
    tasks_data = [
        {
            'task_number': i + 1,
            'max_score': request.POST.get(f'units-{unit_index}-tasks-{i}-max_score'),
            'question_text': request.POST.get(f'units-{unit_index}-tasks-{i}-question_text'),
            'question_path': request.POST.get(f'units-{unit_index}-tasks-{i}-question_path'),
            'is_auto_graded': request.POST.get(f'units-{unit_index}-tasks-{i}-is_auto_graded') == 'true',
            'id': request.POST.get(f'units-{unit_index}-tasks-{i}-id'),  # Get the task ID if it exists
        }
        for i in range(number_of_tasks)
    ]

    for task_data in tasks_data:
        if task_data['id']:  # Update existing task
            task = existing_tasks.pop(int(task_data['id']))
            task.task_number = task_data['task_number']
            task.max_score = task_data['max_score']
            task.question_text = task_data.get('question_text')
            task.question_path = task_data.get('question_path')
            task.is_auto_graded = task_data['is_auto_graded']
            task.save()
        else:  # Create new task
            Tasks.objects.create(
                assignment_unit=unit,
                task_number=task_data['task_number'],
                max_score=task_data['max_score'],
                question_text=task_data.get('question_text'),
                question_path=task_data.get('question_path'),
                is_auto_graded=task_data['is_auto_graded']
            )
    # Delete any tasks that were not included in the update
    for task in existing_tasks.values():
        task.delete()





def get_folder_structure(assignment_path):
    """
    Generate a nested dictionary representing the folder structure for an assignment. It walks 
    through the directory starting from the specified root directory and constructs 
    the hierarchy of folders and files.

    :param assignment_path: The path to the assignment in the filesystem
    :type assignment_path: str

    :return: A nested dictionary representing the folder structure
    :rtype: dict
    """
    folder_tree = {}
    rootdir = assignment_path
    
    for dirpath, dirnames, filenames in os.walk(rootdir):
        # Build the path structure
        folder = folder_tree
        path = dirpath.replace(rootdir, '').strip(os.sep).split(os.sep)
        for subdir in path:
            folder = folder.setdefault(subdir, {'files': []})
        
        # Add files
        folder['files'].extend(filenames)
    
    return folder_tree


def render_tree(tree, assignment_path):
    """
    Convert a nested dictionary representing the folder structure into an HTML unordered list.
    This function recursively processes the dictionary to generate the HTML structure for web display.
    
    :param tree: The nested dictionary representing the folder structure
    :type tree: dict

    :param assignment_path: The path to the assignment in the filesystem
    :type assignment_path: str

    :return: The HTML representation of the folder structure
    :rtype: str
    """
    def render_node(tree, path='', level=0):
        html = '<ul>'
        for key, value in tree.items():
            if key == 'files':
                for file in value:
                    # this stuff is hardcoded which is not great
                    file_url = ((os.path.join(assignment_path, path, file)
                                .replace('\\', '/'))
                                .replace('/app/project_files', ''))
                    extension = file.split('.')[-1]
                    html += f"""
                    <li style="margin-left: {20 * level}px;">
                        <a href="#" class="file-link" data-url="{file_url}" data-extension="{extension}">{file}</a>
                        <a href="#" class="view-icon" data-url="{file_url}" data-extension="{extension}"><i class="fa-solid fa-eye"></i></a>
                        <a href="#" class="edit-icon" data-url="{file_url}" data-extension="{extension}"><i class="fa-solid fa-pen-to-square"></i></a>
                        <a href="#" class="download-icon" data-url="{file_url}"><i class="fa-regular fa-circle-down"></i></a>
                    </li>
                    """
            else:
                html += f'<li style="margin-left: {20 * level}px;">{key}/'
                html += render_node(value, os.path.join(path, key), level + 1)
                html += '</li>'
        html += '</ul>'
        return html

    return render_node(tree)

def delete_assignment(request, assignment_id):
    """
    Delete an assignment and redirect to the assignment list. Retrieves the assignment by ID,
    deletes it, and redirects to the list of assignments for the relevant course.
    
    :param request: The HTTP request object
    :type request: HttpRequest

    :param assignment_id: The ID of the assignment to delete
    :type assignment_id: int
    
    :return: A redirect response to the assignment list
    :rtype: HttpResponseRedirect
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course_id = assignment.course.id
    gs = GitlabService()
    gs.delete_assignment(assignment=assignment)
    gs.remove_periodic_check_routine(assignment)
    assignment.delete()
    return redirect(request.META.get('HTTP_REFERER', reverse('assignment_list', args=[course_id])))


@require_http_methods(["DELETE"])
def delete_assignment_unit(request, unit_id):
    """
    Delete an assignment unit and its associated file if it exists. 
    retrieves the unit by ID, deletes it and the associated file,
    and returns a JSON response indicating success or failure.
    
    :param request: The HTTP request object
    :type request: HttpRequest

    :param unit_id: The ID of the assignment unit to delete
    :type unit_id: int

    :return: A JSON response indicating success or failure
    :rtype: JsonResponse
    """
    # todo make delete assignment from filesystem
    unit = get_object_or_404(AssignmentUnit, id=unit_id)
    file_path = unit.file.path
    try:
        unit.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
        return JsonResponse({'message': 'Unit deleted successfully'})
    except Exception as e:
        return JsonResponse({'message': 'Failed to delete the unit'}, status=500)


def export_all_assignments_for_selected_course(request):
    """
    Export all assignments for the selected course as a CSV file.

    :param request: The HTTP request object
    :type request: HttpRequest

    :return: A CSV file response
    :rtype: HttpResponse
    """
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, id=course_id)
    assignments = course.assignments.all()  # Updated to include all assignments
    response = query_to_csv(assignments)
    return response


@require_POST
def import_assignments_csv(request):
    """
    Only for POST request; request should have request.FILES.file with a csv file.
    Students are linked to the currently selected course.

    :param request: The HTTP request object
    :type request: HttpRequest

    :return: A redirect response to the assignment list
    :rtype: HttpResponseRedirect
    """
    file_list = request.FILES.getlist('file')
    course_id = request.session['selected_course_id']
    for csv_file in file_list:
        remove_fields = ['course', 'tags', 'group', 'comments']
        course = get_object_or_404(Course, id=course_id)
        defaults = dict(course=course)
        import_any_model_csv(csv_file=csv_file, model=Assignment, remove_fields=remove_fields, defaults=defaults)
    return redirect(request.META.get('HTTP_REFERER', reverse('assignment_list', args=[course_id])))






def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def add_assignment(request, assignment_id=None):
    if request.method == 'POST':
        print("Received POST request")  # Debug: Log when a POST request is received
        print("POST data:", request.POST)  # Debug: Log all POST data

        if assignment_id:
            # Update existing assignment
            assignment = get_object_or_404(Assignment, pk=assignment_id)
            form = AssignmentForm(request.POST, request.FILES, instance=assignment)

            # Remove existing assignment units if updating via AJAX
            if is_ajax(request):
                AssignmentUnit.objects.filter(assignment=assignment).delete()
                print(f"Removed existing assignment units for assignment ID {assignment_id}")
        else:
            # Create new assignment
            form = AssignmentForm(request.POST, request.FILES)

        if form.is_valid():
            print("Form is valid")  # Debug: Log when form is valid
            new_assignment = form.save(commit=False)
            course_id = request.session.get('selected_course_id')
            print("Course ID from session:", course_id)  # Debug: Log the course ID

            if course_id:
                selected_course = get_object_or_404(Course, pk=course_id)
                new_assignment.course = selected_course

                # Extract and save extra checks
                check_types = request.POST.getlist('checkType[]')
                check_values = request.POST.getlist('checkValue[]')
                check_extras = request.POST.getlist('checkExtra[]')

                # Handle the case where the extra field might be "null" for naming convention checks
                extra_checks = [
                    {'type': t, 'value': v, 'extra': (e if e != "null" else None)}
                    for t, v, e in zip(check_types, check_values, check_extras)
                ]

                new_assignment.extra_checks = extra_checks
                print(extra_checks)
                new_assignment.save()
                
                form.save_m2m()
                handle_uploaded_files(request, new_assignment)
                add_assignment_units(request, new_assignment)

                # Add the new assignment to all existing groups
                groups = Group.objects.filter(course=selected_course)
                print("Groups found for course:", groups)  # Debug: Log the groups found

                for group in groups:
                    group.assignments.add(new_assignment)
                    print(f"Added assignment {new_assignment.id} to group {group.id}")  # Debug: Log the group update

                # Check if the request is AJAX
                if is_ajax(request):
                    print("AJAX request detected")  # Debug: Log if it's an AJAX request
                    return JsonResponse({'assignment_id': new_assignment.id})
                else:
                    print("Non-AJAX request, redirecting")  # Debug: Log non-AJAX redirection
                    return HttpResponseRedirect(reverse('edit_assignment', args=[new_assignment.id]))

            else:
                print("Course ID not found in session")  # Debug: Log if course ID is not found
                return JsonResponse({'error': 'Course not selected'}, status=400)
        else:
            print("Form is invalid")  # Debug: Log when form is invalid
            print("Errors:", form.errors)  # Debug: Log the form errors
            return JsonResponse({'error': 'Invalid form'}, status=400)
    else:
        print("Received GET request")  # Debug: Log when a GET request is received
        form = AssignmentForm()
    return render(request, 'assignments/add_assignment.html', {'form': form})

@csrf_exempt
@require_POST
def import_zip_assignment_units(request, assignment_id):
    print("Received request to import ZIP")
    assignment = get_object_or_404(Assignment, id=assignment_id)
    zip_file = request.FILES.get('file')

    if not zip_file:
        print("No file uploaded")
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    # Path to store assignment files
    assignment_path = assignment.path_in_filesystem
    if not os.path.exists(assignment_path):
        os.makedirs(assignment_path)
    else:
        shutil.rmtree(assignment_path)
        os.makedirs(assignment_path)
    
    # Extract ZIP file
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        print("Extracting ZIP file")
        zip_ref.extractall(assignment_path)

    # Walk through the directory tree to find all files
    assignment_units = []
    for root, dirs, files in os.walk(assignment_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            print(f"Processing file: {file_path}")
            with open(file_path, 'rb') as f:
                file_content = ContentFile(f.read(), name=file_name)
                unit = AssignmentUnit.objects.create(
                    assignment=assignment,
                    name=file_name,
                    file=file_content,
                    type='non_master',  # Default type
                    total_points=0,  # Default value
                    number_of_tasks=0,  # Default value
                    is_graded=False  # Default value
                )
                print(f"Created AssignmentUnit: {unit}")
                assignment_units.append(unit)

    return HttpResponseRedirect(reverse('edit_assignment', args=[assignment_id]))


def handle_uploaded_files(request, assignment):
    """
    Handle uploaded files for an assignment.
    """
    for field_name, files in request.FILES.lists():
        if field_name.startswith('units-') and field_name.endswith('-file'):
            index = field_name.split('-')[1]
            file_type = request.POST.get(f'units-{index}-type')
            file_folder = os.path.join(assignment.path_in_filesystem, file_type)
            os.makedirs(file_folder, exist_ok=True)
            for file in files:
                with open(os.path.join(file_folder, file.name), 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)




def download_assignment_as_zip(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    assignment_path = assignment.path_in_filesystem

    if not os.path.exists(assignment_path):
        raise Http404("Assignment files not found.")

    # Create a zip file in memory
    zip_filename = f"{assignment.title}.zip"
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(assignment_path):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, assignment_path))

    zip_buffer.seek(0)

    # Serve the zip file
    response = FileResponse(zip_buffer, as_attachment=True, filename=zip_filename)
    return response



def copy_and_override_files(unit):
    source_directory = os.path.join(get_assignment_otter_generated_path(unit), "student")
    destination_directory = unit.assignment.path_in_filesystem

    if not os.path.exists(source_directory):
        print(f"Source directory {source_directory} does not exist.")
        return

    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    # Remove the file in the destination that has the same name as unit.name
    remove_file_or_directory_recursively(destination_directory, unit.name)

    for item in os.listdir(source_directory):
        source_item = os.path.join(source_directory, item)
        destination_item = os.path.join(destination_directory, item)
        
        if os.path.isdir(source_item):
            if os.path.exists(destination_item):
                copy_and_override_files_recursive(source_item, destination_item)
            else:
                shutil.copytree(source_item, destination_item)
        else:
            shutil.copy2(source_item, destination_item)
        
        print(f"Copied {source_item} to {destination_item}")

def remove_file_or_directory_recursively(root_directory, name):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        if name in dirnames:
            dir_to_remove = os.path.join(dirpath, name)
            shutil.rmtree(dir_to_remove)
            print(f"Removed directory {dir_to_remove}")
            dirnames.remove(name)  # Remove from list to prevent further recursion into this directory
        if name in filenames:
            file_to_remove = os.path.join(dirpath, name)
            os.remove(file_to_remove)
            print(f"Removed file {file_to_remove}")

def copy_and_override_files_recursive(source_directory, destination_directory):
    for item in os.listdir(source_directory):
        source_item = os.path.join(source_directory, item)
        destination_item = os.path.join(destination_directory, item)
        
        if os.path.isdir(source_item):
            if not os.path.exists(destination_item):
                shutil.copytree(source_item, destination_item)
            else:
                copy_and_override_files_recursive(source_item, destination_item)
        else:
            shutil.copy2(source_item, destination_item)




def copy_validation_package(assignment):
    """Copy the validation package and write extra checks."""
    validation_package_src = 'validation_package'
    
    # Generate assignment path
    assignment_directory = assignment.path_in_filesystem
    print(f"Assignment directory: {assignment_directory}")
    
    validation_package_dst = os.path.join(assignment_directory, 'validation_package')
    print(f"Validation package destination: {validation_package_dst}")
    
    # Copy the validation_package folder
    try:
        print(f"Copying from {validation_package_src} to {validation_package_dst}")
        shutil.copytree(validation_package_src, validation_package_dst, dirs_exist_ok=True)
        print("Copy successful")
    except Exception as e:
        print(f"Error copying validation package: {e}")
    
    # Create extra_checks.json in the validator folder
    validator_path = os.path.join(validation_package_dst, 'validator')
    print(f"Validator path: {validator_path}")
    
    try:
        os.makedirs(validator_path, exist_ok=True)
        print("Validator directory created")
    except Exception as e:
        print(f"Error creating validator directory: {e}")

    extra_checks_path = os.path.join(validator_path, 'extra_checks.json')
    print(f"Extra checks path: {extra_checks_path}")
    
    try:
        with open(extra_checks_path, 'w') as f:
            json.dump(assignment.extra_checks, f)
        print("Extra checks written successfully")
    except Exception as e:
        print(f"Error writing extra checks: {e}")