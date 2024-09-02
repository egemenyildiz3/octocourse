

from django.test import TestCase
from unittest.mock import patch, Mock
from django.conf import settings
import os
from graderandfeedbacktool.models import TaskGrades, SubmissionUnits, Submissions
from assignment_manager.models import Assignment, Course, Group, AssignmentUnit, Tasks
from graderandfeedbacktool.grading_service import (get_submission_path, validate_submission, calculate_total_grade_for_submission,
                                            calculate_total_grade_for_submission_unit, grade_auto_graded_tasks,
                                            get_submission_auto_graded_grade)
from graderandfeedbacktool.extrachecksUtils import validate_submission as validate_submission_utils
from authentication.models import CustomUser, Role

class GradingServiceTests(TestCase):

    def setUp(self):
        # Creating a Course instance
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.course = Course.objects.create(
            course_code='CS101',
            description='Introduction to Computer Science',
            start_year=2022,
            end_year=2023,
            department='Computer Science',
            created_by=self.user
        )

        # Creating an Assignment instance
        self.assignment = Assignment.objects.create(
            title='test-assignment', 
            course=self.course, 
            total_points=100
        )

        # Creating a Group instance
        self.group = Group.objects.create(
            name='Test Group', 
            course=self.course
        )

        # Creating a Submission instance
        self.submission = Submissions.objects.create(
            assignment=self.assignment, 
            id=1, 
            is_graded_at_this_level=False, 
            group=self.group
        )

        # Creating an AssignmentUnit instance
        self.assignment_unit = AssignmentUnit.objects.create(
            assignment=self.assignment,
            name='test-unit',
            file='path/to/file',
            type='non_master'
        )

        # Creating a SubmissionUnits instance with a valid assignment_unit
        self.submission_unit = SubmissionUnits.objects.create(
            submission=self.submission, 
            id=1, 
            is_graded_at_this_level=False,
            assignment_unit=self.assignment_unit,
            file_path='path/to/submission_unit'
        )

        # Creating a Task instance
        self.task = Tasks.objects.create(
            task_number=1,
            assignment_unit=self.assignment_unit,
            question_text="Sample Question",
            max_score=10
        )

        # Creating a TaskGrades instance with a valid task and submission_unit
        self.task_grade = TaskGrades.objects.create(
            task=self.task,
            submission_unit=self.submission_unit, 
            is_graded=False, 
            max_points=10, 
            points_received=5
        )

    @patch('graderandfeedbacktool.grading_service.os.path.join')
    def test_get_submission_path(self, mock_path_join):
        expected_path = os.path.join(settings.MEDIA_ROOT, 'submissions', self.course.course_code, str(self.submission.id))
        mock_path_join.return_value = expected_path
        path = get_submission_path(self.submission)
        self.assertEqual(path, expected_path)
        mock_path_join.assert_called_with(settings.MEDIA_ROOT, 'submissions', self.course.course_code, str(self.submission.id))

    @patch('graderandfeedbacktool.grading_service.validate_submission_utils')
    def test_validate_submission(self, mock_validate_submission_utils):
        validate_submission(self.submission)
        submission_path = get_submission_path(self.submission)
        mock_validate_submission_utils.assert_called_with(submission_path, self.assignment.extra_checks)

    def test_calculate_total_grade_for_submission(self):
        self.submission_unit.is_graded = True
        self.submission_unit.total_grade = 80
        self.submission_unit.total_points = 100
        self.submission_unit.save()
        total_grade = calculate_total_grade_for_submission(self.submission)
        self.assertEqual(total_grade, 0)

    def test_calculate_total_grade_for_submission_unit(self):
        self.task_grade.is_graded = True
        self.task_grade.save()
        total_grade = calculate_total_grade_for_submission_unit(self.submission_unit)
        self.assertEqual(total_grade, 5.0)

    @patch('graderandfeedbacktool.grading_service.grade_submission')
    def test_grade_auto_graded_tasks(self, mock_grade_submission):
        mock_result_object = Mock()
        mock_result_object.total = 80
        mock_result_object.possible = 100
        mock_result_object.get_score = Mock(return_value=0.8)
        mock_grade_submission.return_value = mock_result_object

        grade_auto_graded_tasks('config_path', 'notebook_path', self.submission_unit.id)
        self.submission_unit.refresh_from_db()
        self.assertEqual(self.submission_unit.auto_graded_grade, 8.0)
        self.task_grade.refresh_from_db()
        self.assertEqual(self.task_grade.points_received, 5.0)
        self.assertFalse(self.task_grade.is_graded)

    def test_get_submission_auto_graded_grade(self):
        self.submission_unit.auto_graded_grade = 8.0
        self.submission_unit.save()
        grade = get_submission_auto_graded_grade(self.submission)
        self.assertEqual(grade, 0)
