import os
import re
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import tempfile
from graderandfeedbacktool.extrachecksUtils import validate_submission, check_naming_convention, check_file_existence, check_file_type, check_file_location
from assignment_manager.models import Assignment, Student, Group, Course
from graderandfeedbacktool.models import Submissions, Feedback
from authentication.models import CustomUser, Role

class ViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Create a user and log in
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create a course
        self.course = Course.objects.create(
            course_code='CS101',
            description='Introduction to Computer Science',
            start_year=2022,
            end_year=2023,
            department='Computer Science',
            created_by=self.user
        )

        # Set the selected course in the session
        session = self.client.session
        session['selected_course_id'] = self.course.pk
        session.save()

        # Create a student
        self.student = Student.objects.create(
            first_name='Egemen',
            last_name='egemen',
            email='egemen@example.com',
            enrollment_year=2020,
            program='Computer Science',
            msc_track='Data Science',
            self_assessed_skill='Python',
            nationality_type='TR',
            start_year_in_mude=2019,
            brightspace_id='12345',
            gitlab_id='123',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC',
        )

        # Create an assignment
        self.assignment = Assignment.objects.create(
            course=self.course,
            title='Assignment_1',
            description='First assignment',
            total_points=100,
            is_individual=True
        )

        # Connect student and course
        self.student.courses_enrolled.set([self.course])

        # Create a group and a submission
        self.group = Group.objects.create(name='Group 1', course=self.course)
        self.group.assignments.add(self.assignment)
        self.submission = Submissions.objects.create(assignment=self.assignment, student=self.student)

        # Create feedback
        self.feedback = Feedback.objects.create(
            submission_id=self.submission,
            feedback_file_path="/",
            date_provided=timezone.now(),
        )

        # Setup for the additional tests
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = self.test_dir.name

        # Create sample files and directories
        os.makedirs(os.path.join(self.test_path, 'master', 'nice'))
        open(os.path.join(self.test_path, 'a_file.txt'), 'w').close()
        open(os.path.join(self.test_path, 'a_b_file.md'), 'w').close()
        open(os.path.join(self.test_path, 'master', 'nice', 'a_nested_file.md'), 'w').close()

    def tearDown(self):
        # Cleanup temporary directory
        self.test_dir.cleanup()

    def test_grading_assignment_list(self):
        response = self.client.get(reverse('grading_assignment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('assignments', response.context)
        self.assertTemplateUsed(response, 'assignment_list.html')

    def test_get_student_or_group_list(self):
        # Individual assignment
        response = self.client.get(reverse('student_group_list', args=[self.assignment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_list.html')
        self.assertIn('students', response.context)

        # Group assignment
        self.assignment.is_individual = False
        self.assignment.save()
        response = self.client.get(reverse('student_group_list', args=[self.assignment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('groups', response.context)
        self.assertTemplateUsed(response, 'group_list.html')

    def test_search_student(self):
        response = self.client.get(reverse('search_student', args=[self.assignment.id]), {'search_query': 'Egemen'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('students', response.context)
        self.assertTrue(response.context['is_search'])
        self.assertTemplateUsed(response, 'student_list.html')

    def test_filter_student(self):
        response = self.client.get(reverse('filter_student', args=[self.assignment.id]),
                                   {'filter': 'first_name', 'value': 'Egemen'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('students', response.context)
        self.assertTrue(response.context['is_filter'])
        self.assertTemplateUsed(response, 'student_list.html')

    def test_search_group(self):
        self.assignment.is_individual = False
        self.assignment.save()
        response = self.client.get(reverse('search_group', args=[self.assignment.id]), {'search_query': 'Group'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('groups', response.context)
        self.assertTrue(response.context['is_search'])
        self.assertTemplateUsed(response, 'group_list.html')

    def test_filter_group(self):
        self.assignment.is_individual = False
        self.assignment.save()
        response = self.client.get(reverse('filter_group', args=[self.assignment.id]),
                                   {'filter': 'name', 'value': 'Group'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('groups', response.context)
        self.assertTrue(response.context['is_filter'])
        self.assertTemplateUsed(response, 'group_list.html')

    # Additional tests for the functions

    def test_check_naming_convention(self):
        self.assertTrue(check_naming_convention(self.test_path, r'^a.*'))
        self.assertFalse(check_naming_convention(self.test_path, r'^z.*'))

    def test_check_file_existence(self):
        self.assertTrue(check_file_existence(self.test_path, 'a_file', 'txt'))
        self.assertFalse(check_file_existence(self.test_path, 'nonexistent_file', 'txt'))

    def test_check_file_type(self):
        self.assertTrue(check_file_type(self.test_path, 'a_b_file', 'md'))
        self.assertFalse(check_file_type(self.test_path, 'a_b_file', 'txt'))

    def test_check_file_location(self):
        self.assertTrue(check_file_location(self.test_path, 'a_nested_file.md', 'master/nice'))
        self.assertFalse(check_file_location(self.test_path, 'a_nested_file.md', 'wrong/path'))





    # TODO: fix this test
    # def test_submission_list(self):
    #     response = self.client.get(reverse('submission_list', args=[self.assignment.id, self.student.id]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn('submissions', response.context)
    #     self.assertIn('form', response.context)
    #     self.assertIn('feedback', response.context)
    #     self.assertTemplateUsed(response, 'submission_list.html')

    # TODO: fix this test
    # def test_send_feedback(self):
    #     response = self.client.get(reverse('send_feedback', args=[self.assignment.id]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json().get('status'), 'warning')
    #     self.submission.grading_status = 'Graded'
    #     self.submission.save()
    #     response = self.client.get(reverse('send_feedback', args=[self.assignment.id]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json().get('status'), 'success')
