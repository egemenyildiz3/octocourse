from django.urls import path
from .views import *
from .feedback_service import *

urlpatterns = [
    path('assignments/', grading_assignment_list, name='grading_assignment_list'),
    path('students_groups/<int:assignment_id>/', get_student_or_group_list, name='student_group_list'),
    path('student/<int:student_id>/submissions/', student_submissions_list, name='student_submissions_list'),
    path('group/<int:group_id>/submissions/', group_submissions_list, name='group_submissions_list'),
    path('submission/<int:submission_id>/', submission_view, name='submission_view'),
    path('submission_unit/<int:unit_id>/', submission_unit_detail, name='submission_unit_detail'),
    path('search/students/<int:assignment_id>/', search_student, name='search_student'),
    path('filter/students/<int:assignment_id>/', filter_student, name='filter_student'),
    path('search_group/<int:assignment_id>/', search_group, name='search_group'),
    path('filter_group/<int:assignment_id>/', filter_group, name='filter_group'),
    path('collect_submissions/<int:assignment_id>/', collect_submissions, name='collect_submissions'),
    path('send_feedback/<int:assignment_id>/', send_feedback, name='send_feedback'),
    path('submission_list/<int:assignment_id>/<int:stu_id>/', submission_list, name='submission_list'),
    path('reset_task_grade_values/<int:sub_unit_id>/', reset_task_grade_values, name='reset_task_grade_values'),
    path('reset_submission_unit_level_grades/<int:sub_unit_id>/', reset_submission_unit_level_grades, name='reset_submission_unit_level_grades'),
    path('reset_submission_level_grade/<int:sub_id>/', reset_submission_level_grade, name="reset_submission_level_grade")
]
