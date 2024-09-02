from django.utils import timezone
from assignment_manager.models import Assignment, Student, Group, AssignmentUnit, GroupMember
from graderandfeedbacktool.models import Submissions, TaskGrades, Teachers
from .models import StudentExams, ExamMetadata, BuddyCheck
import statistics

def get_exam_grades():
    """
    Retrieve grades for all exams.
    """
    exams = ExamMetadata.objects.all()
    exam_grades = {exam.name: list(StudentExams.objects.filter(exam_metadata=exam).values_list('grade', flat=True)) for exam in exams}
    return exam_grades

def get_time_left():
    """
    Calculate time left until the due date for all published assignments.
    """
    assignments = Assignment.objects.filter(is_published=True)
    current_time = timezone.now()
    time_left = {
        assignment.title: calculate_time_remaining(assignment.due_date, current_time) 
        for assignment in assignments if assignment.due_date
    }
    return time_left

def calculate_time_remaining(due_date, current_time):
    """
    Calculate days and hours left from current time to due date.

    :param due_date: The due date of the assignment.
    :type due_date: datetime

    :param current_time: The current time.
    :type current_time: datetime

    :return: A dictionary containing the days and hours left.
    :rtype: dict
    """
    time_remaining = due_date - current_time
    return {'days': time_remaining.days, 'hours': time_remaining.seconds // 3600}

def get_pass_rate():
    """ 
    Calculate the pass rate for all published assignments.

    :return: A dictionary containing the pass rate for each assignment.
    :rtype: dict
    """
    assignments = Assignment.objects.filter(is_published=True)
    pass_rate = {
        assignment.title: calculate_pass_rate(assignment) for assignment in assignments
    }
    return pass_rate

def calculate_pass_rate(assignment):
    """
    Calculate pass rate for a single assignment.

    :param assignment: The assignment to calculate the pass rate for.
    :type assignment: Assignment

    :return: The pass rate for the assignment.
    :rtype: float
    """
    total_submissions = Submissions.objects.filter(assignment=assignment).count()
    passed_submissions = Submissions.objects.filter(assignment=assignment, is_passed=True).count()
    return (passed_submissions / total_submissions) * 100 if total_submissions > 0 else 0

def get_average_grades():
    """
    Calculate the average grades for all published assignments.

    :return: A dictionary containing the average grades for each assignment.
    :rtype: dict
    """
    assignments = Assignment.objects.filter(is_published=True)
    average_grades = {
        assignment.title: calculate_average_grade(assignment) for assignment in assignments
    }
    return average_grades

def calculate_average_grade(assignment):
    """
    Calculate the average grade for a single assignment.

    :param assignment: The assignment to calculate the average grade for.
    :type assignment: Assignment
    """
    grades = Submissions.objects.filter(assignment=assignment).values_list('total_points', flat=True)
    grades = [grade for grade in grades if grade is not None]
    return sum(grades) / len(grades) if grades else 0

def get_grading_progress():
    """
    Calculate the submission progress for all published assignments.

    :return: A dictionary containing the submission progress for each assignment.
    :rtype: dict
    """
    assignments = Assignment.objects.filter(is_published=True)
    grading_progress = {
        assignment.title: calculate_grading_progress(assignment) for assignment in assignments
    }
    return grading_progress

def calculate_grading_progress(assignment):
    """
    Calculate submission progress for a single assignment.

    :param assignment: The assignment to calculate the submission progress for.
    :type assignment: Assignment

    :return: The submission progress for the assignment.
    :rtype: float
    """
    total_submissions = Submissions.objects.filter(assignment=assignment).count()
    graded_submissions = Submissions.objects.filter(assignment=assignment).exclude(grading_status='Not Graded').count()
    return (graded_submissions / total_submissions) * 100 if total_submissions > 0 else 0

def get_nationality_rates():
    """
    Calculate the percentage of students for each nationality.

    :return: A dictionary containing the nationality rates.
    :rtype: dict
    """
    students = Student.objects.all()
    total_students = students.count()
    nationality_rates = {
        nationality: calculate_nationality_rate(students, nationality, total_students) 
        for nationality in students.values_list('nationality_type', flat=True).distinct()
    }
    return nationality_rates

def calculate_master_track_rate(students, track, total_students):
    count = students.filter(msc_track=track).count()
    return (count / total_students) * 100
def get_master_tracks():
    students = Student.objects.all()
    total_students = students.count()

    tracks = {
        track: calculate_master_track_rate(students, track, total_students)
        for track in students.values_list('msc_track', flat=True).distinct()
    }
    return tracks
def calculate_nationality_rate(students, nationality, total_students):
    """
    Calculate nationality rate for a single nationality.

    :param students: The students to get the nationality rate from.
    :type students: QuerySet

    :param nationality: The nationality to calculate the rate for.
    :type nationality: str

    :param total_students: The total number of students.
    :type total_students: int
    """
    count = students.filter(nationality_type=nationality).count()
    return (count / total_students) * 100

def get_exam_participants():
    """
    Count the number of participants for each exam.

    :return: A dictionary containing the number of participants for each exam.
    :rtype: dict
    """
    exams = ExamMetadata.objects.all()
    participation_numbers = {
        exam.name: StudentExams.objects.filter(exam_metadata=exam).count() for exam in exams
    }
    return participation_numbers

def get_group_performance():
    """
    Calculate the average performance of each group.

    :return: A dictionary containing the average performance for each group.
    :rtype: dict
    """
    groups = Group.objects.all()
    group_performance = {
        group.name: calculate_group_performance(group) for group in groups
    }
    return group_performance

def calculate_group_performance(group):
    """
    Calculate the average performance for a single group.

    :param group: The group to calculate the performance for.
    :type group: Group

    :return: The average performance for the group.
    :rtype: float
    """
    submissions = Submissions.objects.filter(group_id=group.id).values_list('total_points', flat=True)
    return sum(submissions) / submissions.count() if submissions.exists() else 0

def get_group_grades():
    """
    Retrieve grades for all groups for each published assignment.

    :return: A dictionary containing the grades for each group.
    :rtype: dict
    """
    groups = Group.objects.all()
    group_grades = {
        group.name: calculate_group_grades(group) for group in groups
    }
    return group_grades

def calculate_group_grades(group):
    """
    Calculate grades for a single group for all published assignments.

    :param group: The group to calculate the grades for.
    :type group: Group

    :return: A dictionary containing the grades for each assignment.
    :rtype: dict
    """
    assignments = Assignment.objects.filter(is_published=True)
    group_grades = {
        assignment.title: calculate_group_assignment_grade(group, assignment) for assignment in assignments
    }
    return group_grades

def calculate_group_assignment_grade(group, assignment):
    """
    Calculate grade for a single group for a single assignment.

    :param group: The group to calculate the grade for.
    :type group: Group

    :param assignment: The assignment to calculate the grade for.
    :type assignment: Assignment

    :return: The grade for the group for the assignment.
    :rtype: float
    """
    submissions = Submissions.objects.filter(assignment=assignment, group_id=group.id).values_list('total_points', flat=True)
    return sum(submissions) / submissions.count() if submissions.exists() else 0


def get_student_performance():
    """
    Retrieve performance details for all students.

    :return: A list containing the performance details for each student.
    :rtype: list
    """
    students = Student.objects.all()
    student_performance = [calculate_student_performance(student) for student in students]
    return student_performance

def calculate_student_performance(student):
    """
    Calculate performance details for a single student.

    :param student: The student to calculate the performance for.
    :type student: Student

    :return: A dictionary containing the performance details for the student.
    :rtype: dict
    """
    assignments = filter_none_values(Submissions.objects.filter(student=student).values_list('total_points', flat=True))
    exams = filter_none_values(StudentExams.objects.filter(student=student).values_list('grade', flat=True))
    buddy_checks = filter_none_values(BuddyCheck.objects.filter(student=student).values_list('overall_performance', flat=True))
    group_members = GroupMember.objects.filter(student_id=student)

    group_names = ', '.join([member.group_id.name for member in group_members])
    comments_count = student.comments.count()

    return {
        'first_name': student.first_name,
        'percentage_points': calculate_average(assignments),
        'group_info': group_names,
        'assignment_scores': calculate_average(assignments),
        'exam_scores': calculate_average(exams),
        'buddy_check_scores': calculate_average(buddy_checks),
        'comments_count': comments_count
    }

def filter_none_values(values):
    """
    Filter out None values from a list of values.

    :param values: The values to filter.
    :type values: list

    :return: A list containing the values without None values.
    :rtype: list
    """
    return [value for value in values if value is not None]

def calculate_average(values):
    """
    Calculate the average of a list of values.
    
    :param values: The values to calculate the average for.
    :type values: list

    :return: The average of the values if values is not empty, otherwise 0.
    :rtype: float
    """
    return sum(values) / len(values) if values else 0

def get_assignment_overview():
    """
    Retrieve an overview for all published assignments.

    :return: A list containing the overview for each assignment.
    :rtype: list
    """
    assignments = Assignment.objects.filter(is_published=True)
    assignment_overview = [calculate_assignment_overview(assignment) for assignment in assignments]
    return assignment_overview

def calculate_assignment_overview(assignment):
    """
    Calculate an overview for a single assignment. 

    :param assignment: The assignment to calculate the overview for.
    :type assignment: Assignment

    :return: A dictionary containing the overview values for the assignment.
    :rtype: dict
    """
    assignment_units = AssignmentUnit.objects.filter(assignment=assignment).count()
    repository_submissions = Submissions.objects.filter(assignment=assignment).count()
    pass_submissions = Submissions.objects.filter(assignment=assignment, is_passed=True).count()
    fail_submissions = repository_submissions - pass_submissions
    pass_fail_percentages = f"{(pass_submissions / repository_submissions) * 100:.2f}%" if repository_submissions > 0 else "0.00% / 0.00%"
    
    # Count of graded submissions
    graded_submissions = Submissions.objects.filter(assignment=assignment).exclude(grading_status='Not Graded').count()
    grading_status = (graded_submissions / repository_submissions) * 100 if repository_submissions > 0 else 0

    # Collecting grades for the assignment
    grades = list(Submissions.objects.filter(assignment=assignment).values_list('total_points', flat=True))
    grades = [grade for grade in grades if grade is not None]
    
    if grades:
        max_grade = max(grades)
        min_grade = min(grades)
        std_dev = statistics.stdev(grades) if len(grades) > 1 else 0
    else:
        max_grade = min_grade = std_dev = 0

    return {
        'name': assignment.title,
        'type': "Individual" if assignment.is_individual else "Group",
        'points': assignment.total_points,
        'assignment_units': assignment_units,
        'repository_submissions': repository_submissions,
        'pass_fail_percentages': pass_fail_percentages,
        'grading_status': f"{grading_status:.2f}%",
        'max_grade': max_grade,
        'min_grade': min_grade,
        'std_dev': std_dev
    }