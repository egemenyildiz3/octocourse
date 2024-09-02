from django.conf import settings

from assignment_manager.models import AssignmentUnit, Assignment


def get_assignment_path(assignment: Assignment) -> str:
    """
    Get path where an assignment should be placed in the filesystem
    """
    assignment_name = assignment.title
    course_name = assignment.course.course_code
    return settings.ASSIGNMENTS_ROOT + f'/{course_name}/{assignment_name}'

def get_assignment_otter_generated_path(unit: AssignmentUnit) -> str:
    """
    Get path where an assignment should be placed in the filesystem
    """
    assignment_name = unit.assignment.title
    course_name = unit.assignment.course.course_code
    unit_name = unit.name
    return settings.ASSIGNMENTS_OTTER_GENERATED_ROOT + f'/{course_name}/{assignment_name}/{unit_name}'

def get_submission_path(assignment: Assignment) -> str:
    """
    Get path where a submission should be placed in the filesystem
    """
    assignment_name = assignment.title
    course_name = assignment.course.course_code
    return settings.SUBMISSIONS_ROOT + f'/{course_name}/{assignment_name}'

def get_feedback_path(course_name: str, assignment_name: str) -> str:
    """
    Get path where feedback should be placed in the filesystem
    """
    return settings.SUBMISSIONS_ROOT + f'/{course_name}/{assignment_name}'