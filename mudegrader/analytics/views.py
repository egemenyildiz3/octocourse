from django.shortcuts import render
from .services import (
    get_exam_grades,
    get_time_left,
    get_pass_rate,
    get_average_grades,
    get_grading_progress,
    get_nationality_rates,
    get_exam_participants,
    get_group_performance,
    get_group_grades,
    get_student_performance,
    get_assignment_overview, get_master_tracks
)

def index(request):
    assignment_grades = get_average_grades()
    exam_grades = get_exam_grades()
    time_left = get_time_left()
    pass_rate = get_pass_rate()
    grading_progress = get_grading_progress()
    master_tracks = get_master_tracks()
    exam_participants = get_exam_participants()
    group_performance = get_group_performance()
    group_grades = get_group_grades()
    student_performance = get_student_performance()
    assignment_overview = get_assignment_overview()

    context = {
        'assignment_grades': assignment_grades,
        'exam_grades': exam_grades,
        'time_left': time_left,
        'pass_rate': pass_rate,
        'grading_progress': grading_progress,
        'master_tracks': master_tracks,
        'exam_participants': exam_participants,
        'group_performance': group_performance,
        'group_grades': group_grades,
        'student_performance': student_performance,
        'assignment_overview': assignment_overview
    }

    return render(request, 'analytics.html', context)
