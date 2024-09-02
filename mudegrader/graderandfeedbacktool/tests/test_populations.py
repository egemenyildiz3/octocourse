from django.test import TestCase
from unittest.mock import patch, Mock
from django.utils import timezone
from assignment_manager.models import Course, Group, Assignment, AssignmentUnit, Student, Tasks
from graderandfeedbacktool.models import SubmissionUnits, Submissions, TaskGrades
from authentication.models import CustomUser, Role
from graderandfeedbacktool.populations import (
    create_submission_from_assignment,
    create_submission_unit_and_task_grades,
    generate_file_path_master,
    generate_file_path_non_master,
    generate_configuration_path,
)

class GradingServiceTests(TestCase):
    def setUp(self):
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
        
        self.assignment = Assignment.objects.create(
            course=self.course,
            title='test_assignment',
            description='Test Assignment Description',
            start_date=timezone.now(),
            due_date=timezone.now(),
            gitlab_subgroup_id=1,
            total_points=100,
            is_individual=True
        )
        
        self.assignment_unit = AssignmentUnit.objects.create(
            assignment=self.assignment,
            name='test_unit',
            type='master',
            number_of_tasks=1
        )
        
        self.student = Student.objects.create(
            net_id='jdoe',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            enrollment_year=2020,
            program='Master of Science',
            msc_track='Computer Science',
            self_assessed_skill='Intermediate',
            nationality_type='Dutch',
            start_year_in_mude=2020,
            brightspace_id='john.doe',
            gitlab_id='123123',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc...'
        )
        
        self.group = Group.objects.create(
            name='test_group',
            course=self.course
        )
        
        self.task = Tasks.objects.create(
            task_number=1,
            assignment_unit=self.assignment_unit,
            question_text="Sample Question",
            max_score=10
        )

    def test_create_submission_from_assignment(self):
        submission = create_submission_from_assignment(self.assignment.id, student_id=self.student.id)
        self.assertIsInstance(submission, Submissions)
        self.assertEqual(submission.assignment, self.assignment)
        self.assertEqual(submission.student, self.student)
    
    def test_create_submission_unit_and_task_grades(self):
        submission = create_submission_from_assignment(self.assignment.id, student_id=self.student.id)
        submission_unit = create_submission_unit_and_task_grades(submission.id, self.assignment_unit)
        self.assertIsInstance(submission_unit, SubmissionUnits)
        self.assertEqual(submission_unit.assignment_unit, self.assignment_unit)
        self.assertEqual(submission_unit.submission, submission)
        self.assertEqual(submission_unit.number_of_tasks, self.assignment_unit.number_of_tasks)

    @patch('services.path_utils.get_submission_path')
    @patch('graderandfeedbacktool.populations.list_files_with_extension')
    def test_generate_file_path_master(self, mock_list_files_with_extension, mock_get_submission_path):
        mock_get_submission_path.return_value = '/fake/submission/path'
        mock_list_files_with_extension.return_value = ['notebook.ipynb']
        
        submission = create_submission_from_assignment(self.assignment.id, student_id=self.student.id)
        submission_unit = create_submission_unit_and_task_grades(submission.id, self.assignment_unit)
        path = generate_file_path_master(submission_unit.id)
        
        self.assertIn('notebook.ipynb', path)
        mock_list_files_with_extension.assert_called()
    
    @patch('services.path_utils.get_submission_path')
    @patch('graderandfeedbacktool.populations.list_files_with_extension')
    def test_generate_file_path_non_master(self, mock_list_files_with_extension, mock_get_submission_path):
        mock_get_submission_path.return_value = '/fake/submission/path'
        mock_list_files_with_extension.return_value = ['file.md']
        
        submission = create_submission_from_assignment(self.assignment.id, student_id=self.student.id)
        submission_unit = create_submission_unit_and_task_grades(submission.id, self.assignment_unit)
        path = generate_file_path_non_master(submission_unit.id)
        
        self.assertIn('file.md', path)
        mock_list_files_with_extension.assert_called()
    
    @patch('services.path_utils.get_assignment_otter_generated_path')
    @patch('graderandfeedbacktool.populations.list_files_with_extension')
    def test_generate_configuration_path(self, mock_list_files_with_extension, mock_get_assignment_otter_generated_path):
        mock_get_assignment_otter_generated_path.return_value = '/fake/otter/generated/path'
        mock_list_files_with_extension.return_value = ['config.zip']
        
        submission = create_submission_from_assignment(self.assignment.id, student_id=self.student.id)
        submission_unit = create_submission_unit_and_task_grades(submission.id, self.assignment_unit)
        path = generate_configuration_path(submission_unit.id)
        
        self.assertIn('config.zip', path)
        mock_list_files_with_extension.assert_called()
