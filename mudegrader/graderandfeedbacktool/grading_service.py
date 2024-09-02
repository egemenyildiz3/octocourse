import os
from .models import TaskGrades, Feedback, SubmissionUnits, Submissions
from assignment_manager.models import AssignmentUnit, Assignment, Tasks
from otter.api import grade_submission
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from .extrachecksUtils import validate_submission as validate_submission_utils



def get_submission_path(submission):
    """
    Returns the path to the submission directory.
    
    :param submission: The submission object.
    :type submission: Submissions
    
    :returns: The path to the submission directory.
    :rtype: str
    """
    return os.path.join(settings.MEDIA_ROOT, 'submissions', submission.assignment.course.course_code, str(submission.id))

def validate_submission(submission):
    """
    Validates the submission based on the extra checks provided.

    :param submission: The submission object.
    :type submission: Submissions

    :returns: Dictionary containing the results of the extra checks.
    :rtype: dict
    """
    submission_path = get_submission_path(submission)
    print(submission_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #following line can be used for debugging to construct a path yourself
    #submission_path = os.path.join(base_dir, 'project_files', 'submissions', 'coursss', '37')
    extra_checks = submission.assignment.extra_checks
    print(submission_path)

    return validate_submission_utils(submission_path, extra_checks)


def calculate_total_grade_for_submission(submission):
    """
    Calculates the total grade for a submission if and only if all the submission units for this submission are "Graded". 
    Returns submission grade if submission has a grade (added manually).
    Otherwise, calculates the grade by summing the grades of all submission units.

    :param submission: The submission object.
    :type submission: Submissions

    :returns: The total grade for the submission.
    :rtype: float
    """
    
    print(f"-> -> calculating total grade for submission id {submission.id}")

    print(f"-> -> grading at submission level : {submission.is_graded_at_this_level}")
    # check if grading is done at the submission level
    if (submission.is_graded_at_this_level):
        submission.is_graded = True
        submission.save()
        print(f"-> -> CHECK AFTER GRADING : {submission.is_graded_at_this_level}")
        return submission.total_grade

    # grading is either done at submission unit level or task grade level
    else:
        # fetch all the submission units in this submission
        submission_units = SubmissionUnits.objects.filter(submission=submission)
        
        # total grade of all submission units
        total_grade_over_submission_units = 0
        number_of_submission_units = 0
        submission.total_points = 0
        for submission_unit in submission_units:
            calculate_total_grade_for_submission_unit(submission_unit)
            submission.total_points += submission_unit.total_points
            total_grade_over_submission_units += submission_unit.total_grade
            number_of_submission_units += 1

        # there are no submission units
        if number_of_submission_units == 0:
            return 0

        # if any submission unit is not graded, then the whole submission is not graded
        submission.is_graded = True
        for submission_unit in SubmissionUnits.objects.filter(submission=submission):
            if not submission_unit.is_graded:
                submission.total_points = 0
                submission.total_grade = 0
                submission.is_graded = False
                submission.save()
                break

        if submission.is_graded:
            submission.total_grade = round(total_grade_over_submission_units/number_of_submission_units, 2)
            submission.save()
            return submission.total_grade
        else:
            return 0


def calculate_total_grade_for_submission_unit(submission_unit):
    """
    Calculates the total grade for a submission unit if and only if the grading status of all the tasks in this submission unit is "Graded". 
    Returns submission unit grade if submission unit has a grade(added manually).
    Otherwise, calculates the grade by summing the grades of all tasks in the submission unit.

    :param submission_unit: The submission unit object.
    :type submission_unit: SubmissionUnits

    :returns: The total grade for the submission unit.
    :rtype: float/home/ybkose/repos/mude/mude-grader/mudegrader/docs/build/html/index.html
    """

    print(f"-> -> calculating total grade for submission unit {submission_unit.id}")

    print(f"-> -> grading at submission unit level : {submission_unit.is_graded_at_this_level}")
    # check if grading is done at submission unit level
    if (submission_unit.is_graded_at_this_level):
        submission_unit.is_graded = True
        submission_unit.save()
        return submission_unit.total_grade

    # grading is done at the task grade level
    else:
        # fetch task grades for this submission unit
        task_grades = TaskGrades.objects.filter(submission_unit=submission_unit)

        submission_unit.is_graded = True
        # if any task in the submission unit is not Graded, then submission unit is not graded
        for task_grade in TaskGrades.objects.filter(submission_unit=submission_unit):
            if not task_grade.is_graded:
                submission_unit.total_points = 0
                submission_unit.total_grade = 0
                submission_unit.is_graded = False
                submission_unit.save()
                break

        # max score/points possible for this submission unit
        total_max_points_over_all_tasks = 0
        # reset total points to zero in case points_received by a task_grade is updated
        submission_unit.total_points = 0
        for task_grade in task_grades:
            total_max_points_over_all_tasks += task_grade.max_points
            submission_unit.total_points += task_grade.points_received

        if submission_unit.is_graded:
            submission_unit.total_grade = round((submission_unit.total_points/total_max_points_over_all_tasks) * 10, 2)
            submission_unit.save()
            return submission_unit.total_grade
        else:
            return 0


def grade_auto_graded_tasks(configuration_path, complete_notebook_path, submission_unit_id):
    """
    This method calculates the total grade for a given submission unit by looping over the tasks
    within that submission unit. The total grade is returned which is used later with its relevant
    weight in other calculations.

    :param configuration_path: The path to the configuration file.
    :type configuration_path: str

    :param complete_notebook_path: The path to the complete notebook.
    :type complete_notebook_path: str

    :param submission_unit_id: The id of the submission unit.
    :type submission_unit_id: int

    :returns: The total grade for the submission unit.
    :rtype: float
    """

    submission_unit = get_object_or_404(SubmissionUnits, id=submission_unit_id)
            
    # run otter grader which returns a result object
    result_object = grade_submission(complete_notebook_path, configuration_path)
    submission_unit.auto_graded_grade = round((result_object.total/result_object.possible) * 10, 2)
    print(f"-> -> submisison unit auto : {submission_unit.auto_graded_grade}")
    submission_unit.save()

    # fetch all the TaskGrade objects linked to this SubmissionUnit
    task_grades = TaskGrades.objects.filter(submission_unit=submission_unit).filter(is_auto_graded=True)

    print(f"size : {task_grades.__len__}")
    for task_grade in task_grades:
        # get the correct task number to be graded
        question_number = task_grade.question_id
        question_string = "q" + str(question_number)
        # get the points for the task
        task_grade.points_received = round(result_object.get_score(question_string) * task_grade.max_points, 2)
        # update the grading status
        task_grade.is_graded = True            
        task_grade.save()

    return result_object.total


def get_submission_auto_graded_grade(submission):
    """
    This method calculates the total grade for a given submission by looping 
    over the submission units within that submission. The total grade is returned
    which is used later with its relevant weight in other calculations.

    :param submission: The submission object.
    :type submission: Submissions

    :returns: The total grade for the submission.
    :rtype: float
    """
    submission_units = SubmissionUnits.objects.filter(submission=submission)

    number_of_master_submission_units = 0
    total_auto_graded_grade_over_submissions = 0

    for submission_unit in submission_units:
        if submission_unit.assignment_unit.type == "master":
            total_auto_graded_grade_over_submissions += submission_unit.auto_graded_grade
            number_of_master_submission_units += 1
    
    if (number_of_master_submission_units == 0):
        return 0
    else:
        submission_auto_graded_grade = round(total_auto_graded_grade_over_submissions/number_of_master_submission_units, 2)
        return submission_auto_graded_grade