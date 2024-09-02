from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from assignment_manager.views.tags import delete_tag, edit_tags

from .views.students import (student_list, add_student, delete_student, search_students, filter_students, edit_student,
                             StudentDetailView, show_student_timeline, send_summary_report_feedback)
from .views.groups import (group_list, add_group, delete_group, search_groups, filter_groups, edit_group,
                           GroupDetailView, add_student_to_group, remove_student_from_group,
                           show_group_timeline)
from .views.courses import feedback_template_view
from .views.assignments import (assignment_list, add_assignment, edit_assignment, delete_assignment, AssignmentDetailView,publish_assignment, delete_assignment_unit)

from assignment_manager.views.students import (student_list, add_student, delete_student, search_students,
                                               filter_students, edit_student,StudentDetailView,export_all_students_for_selected_course,import_students_csv,
                                               send_summary_report_feedback)
from assignment_manager.views.groups import (group_list, add_group, delete_group, search_groups, filter_groups,
                                             edit_group,GroupDetailView,find_student_for_group)
from assignment_manager.views.courses import course_list, add_course, delete_course, edit_course, CourseDetailView, staff_list,export_all_courses,import_courses_csv
from assignment_manager.views.assignments import (assignment_list, add_assignment, edit_assignment, delete_assignment,
                                                  AssignmentDetailView,publish_assignment,export_all_assignments_for_selected_course,import_assignments_csv, import_zip_assignment_units, download_assignment_as_zip,
                                                  publish_manually,
                                                  publish_manually_individual, publish_manually_group)
from assignment_manager.views.exams import exam_list
urlpatterns = [
    # courses
    path('courses/', course_list, name='course_list'),
    path('courses/add/', add_course, name='add_course'),
    path('courses/details/<int:pk>/', CourseDetailView.as_view(), name='course_details'),
    path('courses/delete/<int:course_id>/', delete_course, name='delete_course'),
    path('courses/edit/<int:pk>/', edit_course, name='edit_course'),
    path('courses/staff/<int:course_id>/', staff_list, name='staff_list'),
    path('courses/export/', export_all_courses, name='export_all_courses'),
    path('courses/import/', import_courses_csv, name='import_courses_csv'),
    path('courses/edit-tags/<int:course_id>', edit_tags, name='edit_tags'),
    path('courses/<int:course_id>/delete-tag/<int:tag_id>/', delete_tag, name='delete_tag'),
    path('courses/<int:course_id>/feedback-template/', feedback_template_view, name='feedback_template_new'),
    path('courses/<int:course_id>/feedback-template/<int:template_id>/', feedback_template_view, name='feedback_template_view'),




    # assignments
    path('assignments/<int:course_id>/', assignment_list, name='assignment_list'),
    path('assignments/add', add_assignment, name='add_assignment'),
    path('assignments/details/<int:pk>/', AssignmentDetailView.as_view(), name='assignment_details'),
    path('assignments/delete/<int:assignment_id>/', delete_assignment, name='delete_assignment'),
    path('assignments/edit/<int:pk>/', edit_assignment, name='edit_assignment'),
    path('assignments/publish/<int:assignment_id>/', publish_assignment, name='publish_assignment'),
    path('assignments/export/', export_all_assignments_for_selected_course, name='export_all_assignments_for_selected_course'),
    path('assignments/publish_manually/<int:assignment_id>/', publish_manually,  name='publish_manually'),
    path('assignments/publish_manually_individual/<int:assignment_id>/<int:student_id>/', publish_manually_individual,  name='publish_manually_individual'),
    path('assignments/publish_manually_group/<int:assignment_id>/<int:group_id>/', publish_manually_group,  name='publish_manually_group'),
    path('assignments/import/', import_assignments_csv, name='import_assignments_csv'),
    path('assignments/import_zip/<int:assignment_id>/', import_zip_assignment_units, name='import_zip_assignment_units'),
    path('assignments/download/<int:assignment_id>/', download_assignment_as_zip, name='download_assignment_as_zip'),



    # assignment units
    path('assignments/units/delete/<int:unit_id>/', delete_assignment_unit, name='delete_assignment_unit'),

    # students
    path('students/', student_list, name='student_list'),
    path('students/add', add_student, name='add_student'),
    path('students/details/<int:pk>/', StudentDetailView.as_view(), name='student_details'),
    path('students/delete/<int:student_id>/', delete_student, name='delete_student'),
    path('students/edit/<int:student_id>/', edit_student, name='edit_student'),
    path('students/filter/', filter_students, name='filter_students'),
    path('students/search/', search_students, name='search_students'),
    path('students/export/', export_all_students_for_selected_course, name='export_all_students_for_selected_course'),
    path('students/import/', import_students_csv, name='import_students_csv'),
    path('students/exams/<int:student_id>', exam_list, name='exam_list'),
    path('students/timeline/<int:student_id>/', show_student_timeline, name='student_timeline'),
    path('send_summary_report_feedback/<int:course_id>', send_summary_report_feedback, name='send_summary_report_feedback'),

    # groups
    path('groups/', group_list, name='group_list'),
    path('groups/add', add_group, name='add_group'),
    path('groups/details/<int:pk>/', GroupDetailView.as_view(), name='group_details'),
    path('groups/delete/<int:group_id>/', delete_group, name='delete_group'),
    path('groups/edit/<int:group_id>/', edit_group, name='edit_group'),
    path('groups/filter/', filter_groups, name='filter_groups'),
    path('groups/search/', search_groups, name='search_groups'),
    path('groups/add-student/', add_student_to_group, name='add_student_to_group'),
    path('groups/remove-student/', remove_student_from_group, name='remove_student_from_group'),
    path('groups/search-student/', find_student_for_group, name='find_student_for_group'),
    path('groups/timeline/<int:group_id>/', show_group_timeline, name='group_timeline'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
