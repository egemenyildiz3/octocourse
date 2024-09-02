import os

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.utils import timezone
from assignment_manager.models import Group, Assignment, AssignmentUnit, Student
from graderandfeedbacktool.models import SubmissionUnits, Submissions, TaskGrades
from .grading_service import grade_auto_graded_tasks, get_submission_auto_graded_grade
from .file_conversion_util import *
from services.path_utils import get_submission_path, get_assignment_otter_generated_path


def populate_database_for_one_assignment(ass_id, stu_id=None, grp_id=None):
    """
    Populate the database with submission data for a given assignment.

    This function iterates over all assignment units for a given assignment, checks if they are of type 'master',
    and performs necessary actions such as creating submission units, generating file paths, grading, and converting
    notebook files to PDF.

    :param ass_id: The ID of the assignment for which the database is being populated.
    :type ass_id: int
    :param stu_id: The ID of the student (optional). Default is None.
    :type stu_id: int, optional
    :param grp_id: The ID of the group (optional). Default is None.
    :type grp_id: int, optional
    """
    print(f"Starting database population for assignment ID : {ass_id}, student ID {stu_id}, group ID {grp_id}")

    # Determine if it's an individual or group assignment
    if stu_id is not None:
        student_or_group = Student.objects.get(id=stu_id)  
        submission = create_submission_from_assignment(assignment_id=ass_id, student_id=stu_id,group_id=None)
    elif grp_id is not None:
        print(f"its a group submission")
        student_or_group = Group.objects.get(id=grp_id)
        submission = create_submission_from_assignment(assignment_id=ass_id, student_id=None , group_id=grp_id)
    else:
        raise ValueError("Either stu_id or grp_id must be provided")

    # Fetch the assignment
    assignment = submission.assignment
    print(f"Fetched assignment: {assignment.title}")

    # Fetch the list of assignment units related to the assignment 
    units = AssignmentUnit.objects.filter(assignment=assignment)
    print(f"Found {units.count()} assignment units for assignment {assignment.title}")

    for unit in units:        
        # Create submission unit and task grades
        submission_unit = create_submission_unit_and_task_grades(submission.id, unit)

        if unit.type == 'master':
            print(f"-> -> Processing unit {unit.name} of type '{unit.type}'")
            
            # generate file path for notebook unit
            unit_path = generate_file_path_master(submission_unit.id)
            submission_unit.file_path = unit_path
            submission_unit.save()

            # grade the submission unit
            configuration_path = generate_configuration_path(submission_unit.id)
            grade_auto_graded_tasks(configuration_path, unit_path, submission_unit.id)
            print(f" successfully graded auto-graded tasks for submission unit: {submission_unit.id}")

            # convert notebook to PDF
            # submission_unit.converted_file_path = convert_notebook_to_pdf(unit_path)
            # submission_unit.save()
        
        else:
            print(f"-> -> Processing unit {unit.name} of type '{unit.type}'")
            
            # generate file path for the markdown file
            unit_path = generate_file_path_non_master(submission_unit.id)
            submission_unit.file_path = unit_path
            submission_unit.save()

            # convert the markdown file to html
            # submission_unit.converted_file_path = convert_mark_down_to_html(unit_path)
            # submission_unit.save()
    
    submission.auto_graded_grade = get_submission_auto_graded_grade(submission)
    submission.save()

    print(f"Finished database population for assignment ID : {ass_id}")


def create_submission_from_assignment(assignment_id, student_id=None, group_id=None):
    """
    Create a submission, submission units, and task grades for a specific 
    assignment and student or group.

    :param assignment_id: The ID of the assignment
    :type assignment_id: int

    """


    assignment = get_object_or_404(Assignment, pk=assignment_id)
    student = get_object_or_404(Student, pk=student_id) if student_id else None
    group = get_object_or_404(Group, pk=group_id) if group_id else None

    # Create the submission
    submission = Submissions.objects.create(
        assignment=assignment,
        student=student,
        group=group,
        file_path="",  # Default file path, can be updated later
        feedback="",
        total_grade=0,
        total_points=0
    )

    submission.save()
    print(f"Submission object created successfully : {submission.id}")
    return submission

def create_submission_unit_and_task_grades(submission_id, ass_unit):

    """
    Creates submission units, and task grades for a specific submission
    """
    
    # fetch the submission
    submission = Submissions.objects.get(id = submission_id)

    submission_unit = SubmissionUnits.objects.create(
        submission=submission,
        assignment_unit=ass_unit,
        file_path="",
        feedback="",
        total_grade=0,
        total_points=0,
        number_of_tasks=ass_unit.number_of_tasks
    )
    
    # need a task_number in the Task Model to match with the question_id (which should be renamed to task_grade_number)
    for task in ass_unit.tasks_set.all():
        print("creating task grade")
        task_grade = TaskGrades.objects.create(
            question_id=task.task_number,
            task=task,
            submission_unit=submission_unit,
            graded_by_teacher_id=None,
            date_graded=timezone.now(),
            max_points=task.max_score,
            points_received=0,
            is_auto_graded=task.is_auto_graded
        )
        task_grade.save()

    submission_unit.save()
    print(f"Submission unit object created successfully : {submission_unit.id}")
    return submission_unit


def generate_file_path_master(unit_id):

    print(f"-> -> generating file path for notebook submission...")

    # get path to the project_files directory
    project_files_url = settings.MEDIA_ROOT
    # fetch the submission unit
    submission_unit = get_object_or_404(SubmissionUnits, id=unit_id)
    # fetch the submission
    submission = submission_unit.submission
    # fetch the assignment title
    assignment_name = submission.assignment.title
    # fetch the course code
    course_id = str(submission.assignment.course.id)

    # create file paths for the submission files
    path_till_assignment_name = get_submission_path(submission.assignment)
    complete_notebook_path = ""
    master = "master"
    
    if submission.assignment.is_individual:
        # netid
        net_id = submission.student.net_id
        # netid-main
        net_id_main = str(net_id + "-main")
        submission_folder_path = os.path.join(path_till_assignment_name, net_id, net_id_main)
        # list all the files inside the submission folder and get the name for file of type .ipynb
        notebook_files = list_files_with_extension(submission_folder_path, ".ipynb")
        print(f"files in project_files : {notebook_files}")
        try :
            complete_notebook_path = os.path.join(submission_folder_path, notebook_files[0])
            print(f"generated notebook path : {complete_notebook_path}")
        except FileNotFoundError:
            print("FileNotFoundError: One of the directories or the file doesn't exist.")
    else:
        group_id = submission.group.id
        group_name = submission.group.name
        group_name_main = group_name + "-main"
        submission_folder_path = os.path.join(path_till_assignment_name, group_name, group_name_main)
        # list all the files inside the submission folder and get the name for file of type .ipynb
        notebook_files = list_files_with_extension(submission_folder_path, ".ipynb")
        print(f"files in project_files : {notebook_files}")
        try :
            complete_notebook_path = os.path.join(submission_folder_path, notebook_files[0])
            print(f"generated notebook path : {complete_notebook_path}")
        except FileNotFoundError:
            print("FileNotFoundError: One of the directories or the file doesn't exist.")

    return complete_notebook_path


def generate_file_path_non_master(unit_id):

    print(f"-> -> generating file path for markdown submission...")

    # get path to the project_files directory
    project_files_url = settings.MEDIA_ROOT
    # fetch the submission unit
    submission_unit = get_object_or_404(SubmissionUnits, id=unit_id)
    # fetch the submission
    submission = submission_unit.submission
    # fetch the assignment title
    assignment_name = submission.assignment.title
    # fetch the course code
    course_id = submission.assignment.course.id

    # create file paths for the submission files
    path_till_assignment_name = get_submission_path(submission.assignment)
    complete_non_master_file_path = ""

    if submission.assignment.is_individual:
        # netid
        net_id = submission.student.net_id
        # netid-main
        net_id_main = str(net_id + "-main")
        # non-master or master
        non_master = "non_master"
        submission_folder_path = os.path.join(path_till_assignment_name, net_id, net_id_main, non_master)
         # list all the files inside the submission folder andget the name for file of type .ipynb
        notebook_files = list_files_with_extension(submission_folder_path, ".md")
        print(f"files in project_files : {notebook_files}")
        try:
            complete_non_master_file_path = os.path.join(submission_folder_path, notebook_files[0])
            print(f"generated markdown file path : {complete_non_master_file_path}")
        except FileNotFoundError:
            print("FileNotFoundError: One of the directories or the file doesn't exist.")
    else:
        group_id = submission.group.id
        group_name = submission.group.name
        group_name_main = group_name + "-main"
        non_master = "non_master"
        submission_folder_path = os.path.join(path_till_assignment_name, group_name, group_name_main, non_master)
        # list all the files inside the submission folder and get the name for file of type .ipynb
        notebook_files = list_files_with_extension(submission_folder_path, ".md")
        print(f"files in project_files : {notebook_files}")
        try :
            complete_non_master_file_path = os.path.join(submission_folder_path, notebook_files[0])
            print(f"generated markdown file path : {complete_non_master_file_path}")
        except FileNotFoundError:
            print("FileNotFoundError: One of the directories or the file doesn't exist.")
    
    return complete_non_master_file_path


def generate_configuration_path(unit_id):
    
    print(f"-> -> generating file path for the configuration zip file")

    # fetch the submission unit
    submission_unit = get_object_or_404(SubmissionUnits, id=unit_id)
    # fetch the configuration zip file
    otter_generated_files = os.path.join(get_assignment_otter_generated_path(submission_unit.assignment_unit),"autograder")
    
    zip_file = list_files_with_extension(otter_generated_files, ".zip")[0]
    configuration_file_path = os.path.join(otter_generated_files, zip_file)

    print(f"configuration_file_path : {configuration_file_path}")
    return configuration_file_path