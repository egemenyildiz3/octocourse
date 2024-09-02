import os
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Max
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from graderandfeedbacktool.feedback_utils import generate_html_from_markdown_template
from graderandfeedbacktool.models import *
from assignment_manager.models import Assignment, Student, Group, Course
from graderandfeedbacktool.models import Submissions, Feedback
from gitlabmanager.distribution_service import DistributionService
from analytics.models import BuddyCheck


# Define a consistent base directory
BASE_DIR = "/app/project_files/feedback"

def construct_file_path_auto_graded(base_path, is_group, identifier, submission_time):
    """
    Make a file path for the auto-graded feedback report based on assignment properties.

    :param base_path: The base path for the feedback reports.
    :type base_path: str

    :param is_group: Whether the feedback is for a group or an individual.
    :type is_group: bool

    :param identifier: The identifier for the group or individual.
    :type identifier: str

    :param submission_time: The time of the submission.
    :type submission_time: datetime

    :returns: The file path for the feedback report.
    :rtype: str
    """
    if is_group:
        return os.path.join(base_path, f"Group_{identifier}", "auto_graded",f"{submission_time.strftime('%Y%m%d%H')}_submission_report.md")
    else:
        return os.path.join(base_path, "student_feedback", str(identifier), "auto_graded", f"{submission_time.strftime('%Y%m%d%H%M')}_submission_report.md")

# def create_filename_for_feedback_report()

def create_report_for_master_units_in_a_submission(submission, is_group, name_identifier):
    """
    Create a feedback report for the master units in a submission.
    
    :param submission: The submission object.
    :type submission: Submissions
        
    :param is_group: Whether the submission is for a group or an individual.
    :type is_group: bool
    
    :param name_identifier: The name or identifier of the group or individual.
    :type name_identifier: str
    
    :returns: The markdown text for the feedback report.
    :rtype: str
    """
    print(f"-> -> Creating auto-graded feedback")
    
    if is_group:
        md_text = f"# Automated Submission Report for Group: {name_identifier}\n"
    else:
        md_text = f"# Automated Submission Report for {name_identifier}\n"

    # fetch all the submission units
    submission_units = SubmissionUnits.objects.filter(submission=submission, assignment_unit__is_gradable=True)
    for submission_unit in submission_units:
        # submission unit must be of type 'master'
        if (submission_unit.assignment_unit.type == "master"):
            md_text += f"## Assignment File : {submission_unit.assignment_unit.name}\n"
            task_grades = TaskGrades.objects.filter(submission_unit=submission_unit)
            for task_grade in task_grades:
                if task_grade.is_auto_graded:
                    feedback = Feedback.objects.filter(grade_id=task_grade.id).first()
                    md_text += f"### Task Number : {task_grade.task.task_number}\n"
                    md_text += f"#### Grade : {task_grade.points_received}\n"
                    md_text += f"#### Feedback : {feedback.feedback_text if feedback else 'No feedback'}\n"
            md_text += f"--- \n"

    return md_text


def send_autograded_feedback(assignment_id):
    """
    Send auto-graded feedback for an assignment.
    
    :param assignment_id: The ID of the assignment.
    :type assignment_id: int
    
    :returns: A JSON response indicating the status of the feedback distribution.
    :rtype: JsonResponse
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    base_path = os.path.join(BASE_DIR, str(assignment.course.id), assignment.title)
    distribution_service = DistributionService()
    reports = []

    if assignment.is_individual:
        individual_path = os.path.join(base_path, "student_feedback")
        students = Student.objects.filter(courses_enrolled=assignment.course_id)
        for student in students:
            try:
                latest_submission = Submissions.objects.filter(assignment=assignment, student=student).latest('submission_time')
                name_identifier = f"{student.first_name} {student.last_name}"
                
                md_text = create_report_for_master_units_in_a_submission(latest_submission, is_group=False, name_identifier=name_identifier)
                file_path = construct_file_path_auto_graded(individual_path, is_group=False, identifier=student.id, submission_time=datetime.now())
                save_report(file_path, md_text)
                
                reports.append(file_path)
                
                latest_submission.file_path = file_path
                latest_submission.save()
            except ObjectDoesNotExist:
                continue
    else:
        group_path = os.path.join(base_path, "group_feedback")
        groups = Group.objects.filter(assignments__in=[assignment])
        for group in groups:
            try:
                latest_submission = Submissions.objects.filter(assignment=assignment, group=group).latest('submission_time')
                group_name_identifier = group.name
                
                md_text = create_report_for_master_units_in_a_submission(latest_submission, is_group=True, group_name_identifier=group_name_identifier)
                file_path = construct_file_path_auto_graded(group_path, is_group=True, identifier=group.name, submission_time=datetime.now())
                save_report(file_path, md_text)
                
                reports.append(file_path)
                
                latest_submission.file_path = file_path
                latest_submission.save()
            except ObjectDoesNotExist:
                continue

    failed_feedback = distribution_service.distribute_feedback(assignment_id, True)

    if failed_feedback:
        failed_feedback_ids = [submission.id for submission in failed_feedback]
        return JsonResponse({'status': 'warning', 'message': 'Some feedback distributions failed', 'failed_feedback': failed_feedback_ids})
    else:
        return JsonResponse({'status': 'success', 'message': 'Feedback distributed successfully'})


def construct_file_path_manual_feedback(base_path, is_group, identifier, submission_time):
    """
    Make a file path for the manual feedback report based on assignment properties.
    
    :param base_path: The base path for the feedback reports.
    :type base_path: str
    
    :param is_group: Whether the feedback is for a group or an individual.
    :type is_group: bool

    :param identifier: The identifier for the group or individual.
    :type identifier: str

    :param submission_time: The time of the submission.
    :type submission_time: datetime

    :returns: The file path for the feedback report.
    :rtype: str
    """
    if is_group:
        return os.path.join(base_path, f"Group_{identifier}", f"{submission_time.strftime('%Y%m%d%H')}_submission_report.md")
    else:
        return os.path.join(base_path, "student_feedback", str(identifier), f"{submission_time.strftime('%Y%m%d%H%M')}_submission_report.md")

def create_report_selected(submission, is_group: bool, identifier) -> str:
    """
    Create a feedback report using a selected feedback template.

    :param submission: The submission object.
    :type submission: Submissions

    :param is_group: Whether the submission is for a group or an individual.
    :type is_group: bool

    :param identifier: The name or identifier of the group or individual.
    :type identifier: str

    :returns: The markdown text for the feedback report.
    :rtype: str
    """
    course = submission.assignment.course
    if course.selected_feedback_template is None:
        # if no template is selected at the course level, use the old method
        return create_report(submission, is_group, identifier)

    context = {
        'course': course,
        'submission': submission,
    }
    template = course.selected_feedback_template.text
    result = generate_html_from_markdown_template(template, context)
    return result

def create_report(submission, is_group, identifier):
    """
    Create a feedback report for a submission.

    :param submission: The submission object.
    :type submission: Submissions

    :param is_group: Whether the submission is for a group or an individual.
    :type is_group: bool

    :param identifier: The name or identifier of the group or individual.
    :type identifier: str

    :returns: The markdown text for the feedback report.
    :rtype: str
    """
    course = submission.assignment.course
    if course.selected_feedback_template is not None:
        return create_report_selected(submission, is_group, identifier)

    print(f"-> > Creating manual feedback report")
    if is_group:
        md_text = f"# Manual Submission Report for Group: {identifier}\n"
    else:
        md_text = f"# Manual Submission Report for {identifier}\n"

    # check if graded and feedback given at submission level
    if (submission.is_graded_at_this_level):
        md_text += f"## Assignment : {submission.assignment.title}\n"
        md_text += f"### Grade for the whole assignment : {submission.total_grade}\n"
        md_text += f"### Feedback for the whole assignment: {submission.feedback}\n"

        submission_units = SubmissionUnits.objects.filter(submission=submission, assignment_unit__is_gradable=True)
        for submission_unit in submission_units:
            md_text += f"## Assignment Unit : {submission_unit.assignment_unit.name}\n"
            task_grades = TaskGrades.objects.filter(submission_unit=submission_unit)
            for task_grade in task_grades:
                feedback = Feedback.objects.filter(grade_id=task_grade.id).first()
                md_text += f"#### Task Number : {task_grade.task.task_number}\n"
                # md_text += f"##### Task Grade : {task_grade.points_received}\n"
                md_text += f"##### Task Feedback : {feedback.feedback_text if feedback else 'No feedback'}\n"
            md_text += f"--- \n"

        return md_text
    
    # else iterate over the submission units
    else:
        md_text += f"## Assignment : {submission.assignment.title}\n"
        # fetch all submission units for this submission
        submission_units = SubmissionUnits.objects.filter(submission=submission, assignment_unit__is_gradable=True)
        for submission_unit in submission_units:
            md_text += f"### Assignment Unit : {submission_unit.assignment_unit.name}\n"
            # check if graded and feedback given at the submission_unit level
            if (submission_unit.is_graded_at_this_level):
                md_text += f"#### Assignment Unit Grade : {submission_unit.total_grade}\n"
                md_text += f"#### Assignment Unit Feedback : {submission_unit.feedback}\n"
                md_text += f"####\n"

                task_grades = TaskGrades.objects.filter(submission_unit=submission_unit)
                for task_grade in task_grades:
                    feedback = Feedback.objects.filter(grade_id=task_grade.id).first()
                    md_text += f"#### Task Number : {task_grade.task.task_number}\n"
                    # md_text += f"##### Task Grade : {task_grade.points_received}\n"
                    md_text += f"##### Task Feedback : {feedback.feedback_text if feedback else 'No feedback'}\n"
                md_text += f"--- \n"

            # else grading and feedback is given at task level
            else:
                task_grades = TaskGrades.objects.filter(submission_unit=submission_unit)
                for task_grade in task_grades:
                    feedback = Feedback.objects.filter(grade_id=task_grade.id).first()
                    md_text += f"#### Task Number : {task_grade.task.task_number}\n"
                    md_text += f"##### Task Grade : {task_grade.points_received}\n"
                    md_text += f"##### Task Feedback : {feedback.feedback_text if feedback else 'No feedback'}\n"
                md_text += f"--- \n"
        return md_text


def send_feedback(request, assignment_id):
    """
    Send manual feedback for an assignment.
    
    :param request: The HTTP request object.
    :type request: HttpRequest

    :param assignment_id: The ID of the assignment.
    :type assignment_id: int

    :returns: A JSON response indicating the status of the feedback distribution.
    :rtype: JsonResponse
    """
    print("MANUAL FEEDBACK RUNNING")
    assignment = get_object_or_404(Assignment, id=assignment_id)
    base_path = os.path.join(BASE_DIR, str(assignment.course.id), assignment.title)
    distribution_service = DistributionService()
    reports = []

    if assignment.is_individual:
        individual_path = os.path.join(base_path, "student_feedback")
        students = Student.objects.filter(courses_enrolled=assignment.course_id)
        for student in students:
            try:
                latest_submission = Submissions.objects.filter(assignment=assignment, student=student).latest('submission_time')
                identifier = f"{student.first_name} {student.last_name}"
                md_text = create_report(latest_submission, is_group=False, identifier=identifier)
                file_path = construct_file_path_manual_feedback(individual_path, is_group=False, identifier=student.id, submission_time=datetime.now())
                print(f"FILE PATH CREATED IN FEEDBACK = {file_path}")
                save_report(file_path, md_text)
                reports.append(file_path)
                latest_submission.file_path = file_path
                latest_submission.save()
            except ObjectDoesNotExist:
                print("MANUAL FEEDBACK EXCEPTION")
                continue
    else:
        group_path = os.path.join(base_path, "group_feedback")
        groups = Group.objects.filter(assignments__in=[assignment])
        for group in groups:
            try:
                latest_submission = Submissions.objects.filter(assignment=assignment, group=group).latest('submission_time')
                identifier = group.name
                md_text = create_report(latest_submission, is_group=True, identifier=identifier)
                file_path = construct_file_path_manual_feedback(group_path, is_group=True, identifier=group.name, submission_time=datetime.now())
                save_report(file_path, md_text)
                reports.append(file_path)
                latest_submission.file_path = file_path
                latest_submission.save()
            except ObjectDoesNotExist:
                continue

    failed_feedback = distribution_service.distribute_feedback(assignment_id, False)

    if failed_feedback:
        failed_feedback_ids = [submission.id for submission in failed_feedback]
        return JsonResponse({'status': 'warning', 'message': 'Some feedback distributions failed', 'failed_feedback': failed_feedback_ids})
    else:
        return JsonResponse({'status': 'success', 'message': 'Feedback distributed successfully'})


def create_summary_report(student):
    """
    Create a summary report for a student.

    :param student: The student object.
    :type student: Student

    :returns: The markdown text for the summary report.
    :rtype: str
    """
    print(f"-> -> Creating summary feedback")

    md_text = f"# Personal Report for {student.first_name} {student.last_name}\n"
    md_text += f"This is a draft report format to give you a summary of how your Project Portfolio is progressing."
    
    # Submissions related to the student (individual submissions)
    student_submissions = Submissions.objects.filter(student=student)

    # Submissions related to the groups the student is a member of
    group_submissions = Submissions.objects.filter(group__group_members__student_id=student)
    
    # Combine both querysets
    all_submissions = student_submissions | group_submissions
    # Get the latest submission for each assignment
    latest_submissions = all_submissions.values('assignment').annotate(latest_time=Max('submission_time'))
    # Fetch the actual submission objects
    latest_submission_objects = []
    for latest_submission in latest_submissions:
        assignment_id = latest_submission['assignment']
        latest_time = latest_submission['latest_time']
        latest_submission_object = all_submissions.filter(assignment_id=assignment_id, submission_time=latest_time).first()
        if latest_submission_object:
            latest_submission_objects.append(latest_submission_object)

    # Separate the submissions into individual and group
    individual_submissions = []
    group_submissions = []

    for submission in latest_submission_objects:
        if submission.assignment.is_individual:
            individual_submissions.append(submission)
        else:
            group_submissions.append(submission)


    md_text += f"## Programming Assignments\n"
    md_text += f"| Programming Assignment | Status   |\n"
    md_text += f"| ---------------------- | -------- |\n"
    ind_points_possible = 0
    ind_points_earned = 0
    for submission in individual_submissions:
        submission_units = SubmissionUnits.objects.filter(submission=submission)
        for submission_unit in submission_units:
            md_text += f"| {submission_unit.assignment_unit.name} | {submission_unit.total_points} |\n"
            ind_points_possible += submission_unit.assignment_unit.total_points
            ind_points_earned += submission_unit.total_points
    md_text += f"points possible as of this report : {ind_points_possible} \n"
    md_text += f"points earned : {ind_points_earned}\n"
    md_text += "\n\n"


    md_text += f"## Group Projects\n"
    md_text += f"| Group Project Assignment | Status   |\n"
    md_text += f"| ------------------------ | -------- |\n"
    grp_points_possible = 0
    grp_points_earned = 0
    for submission in group_submissions:
        submission_units = SubmissionUnits.objects.filter(submission=submission)
        for submission_unit in submission_units:
            md_text += f"| {submission_unit.assignment_unit.name} | {submission_unit.total_points} |\n"
            grp_points_possible += submission_unit.assignment_unit.total_points
            grp_points_earned += submission_unit.total_points
    md_text += f"points possible as of this report : {grp_points_possible}\n"
    md_text += f"points earned : {grp_points_earned}\n"
    md_text += "\n\n"


    buddy_checks = BuddyCheck.objects.filter(student=student)
    md_text += f"## Buddy Checks\n"
    md_text += f"| BuddyCheck | Status   |\n"
    md_text += f"| ---------- | -------- |\n"
    buddy_check_points_earned = 0
    for buddy_check in buddy_checks:
        md_text += f"| {buddy_check.id} | {buddy_check.overall_performance} |\n"
        buddy_check_points_earned += buddy_check.overall_performance
    md_text += f"points possible as of this report : \n"
    md_text += f"points earned : {buddy_check_points_earned}\n"
    md_text += "\n\n"


    md_text += f"TOTAL points possible as of this report : {ind_points_possible + grp_points_possible}\n"
    md_text += f"TOTAL points earned : {ind_points_earned + grp_points_earned + buddy_check_points_earned}\n"
    return md_text


def send_summary_report(course_id):
    """
    Send summary feedback for all students in a course.
    
    :param course_id: The ID of the course.
    :type course_id: int
    """
    distribution_service = DistributionService()
    reports = []
    
    # get all the students in enrolled in this course
    course = get_object_or_404(Course, id=course_id)
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return []

    students = course.enrolled_students.all()

    for student in students:

        # create the summary report
        md_text = create_summary_report(student)
        # output file path
        individual_path = os.path.join(BASE_DIR, str(course_id), "summary_feedback", str(student.id), f"{datetime.now().strftime('%Y%m%d%H%M')}_summary_report.md")
        save_report(individual_path, md_text)
        reports.append(individual_path)
        student.summary_report_url = individual_path
        student.save()

        ########## todo : need the correct distribution_service 
        # failed_feedback = distribution_service.distribute_feedback()
        # if failed_feedback:
        #     failed_feedback_ids = [submission.id for submission in failed_feedback]
        #     return JsonResponse({'status': 'warning', 'message': 'Some feedback distributions failed', 'failed_feedback': failed_feedback_ids})
        # else:
        #     return JsonResponse({'status': 'success', 'message': 'Feedback distributed successfully'})


def save_report(file_path, md_text):
    """
    Save the feedback report to a file.

    :param file_path: The path to the file.
    :type file_path: str

    :param md_text: The markdown text to save.
    :type md_text: str
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(md_text)
    print(f"Report saved at: {file_path}")