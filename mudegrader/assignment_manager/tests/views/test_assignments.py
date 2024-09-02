import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages

from assignment_manager.factories import CourseFactory, AssignmentFactory
from assignment_manager.views.assignments import handle_uploaded_files
from assignment_manager.models import Course, AssignmentUnit, Assignment, Student, Interval
from authentication.models import CustomUser, Role

from unittest.mock import patch, MagicMock, Mock


class AssignmentViewsTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.client.login(username='testuser', password='testpassword')

        course = CourseFactory(course_code='CS101')
        AssignmentFactory(
            course=course,
            title='Assignment_1',
            description='First assignment',
        )
        session = self.client.session
        session['selected_course_id'] = course.pk
        session.save()

    def test_add_assignment(self):
        course = Course.objects.get(course_code='CS101')
        url = reverse('add_assignment')
        data = {
            'course': course.id,
            'title': 'Assignment_2',
            'description': 'Second assignment',
            'total_points': 100,
            'server_check_interval': Interval.WEEK,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Assignment.objects.filter(title='Assignment_2').exists())

    @patch('assignment_manager.views.assignments.GitlabService')
    def test_delete_assignment(self, mock_gitlab_service):
        mock_gitlab_service.delete_assignment.return_value = "Deleted_assignment"
        assignment = Assignment.objects.get(title='Assignment_1')
        url = reverse('delete_assignment', args=[assignment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Assignment.objects.filter(title='Assignment_1').exists())

    def test_edit_assignment(self):
        assignment = Assignment.objects.get(title='Assignment_1')
        url = reverse('edit_assignment', args=[assignment.id])
        data = {
            'course': assignment.course.id,
            'title': 'Assignment_1_edited',
            'description': 'First assignment (Edited)',
            'total_points': 100,
            'server_check_interval': Interval.WEEK,
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.title, 'Assignment_1_edited')

    def test_assignment_list(self):
        course = Course.objects.get(course_code='CS101')
        url = reverse('assignment_list', args=[course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assignment_1')

    # @patch('assignment_manager.views.assignments.GitlabService')
    # def test_publish_assignment(self, mock_gitlab_service):
    #     # mocking
    #     mock_gitlab_service_instance = mock_gitlab_service.return_value
    #     mock_gitlab_service_instance.add_assignment.return_value = True
    #     mock_gitlab_service_instance.publish_assignment_existing_groups.return_value = None
    #     # test itself
    #     assignment = Assignment.objects.get(title='Assignment_1')
    #     url = reverse('publish_assignment', args=[assignment.id])
    #     response = self.client.post(url)
    #     self.assertEqual(response.status_code, 302)  
    #     assignment.refresh_from_db()
    #     self.assertTrue(assignment.is_published)

    @patch('assignment_manager.views.assignments.get_object_or_404')
    @patch('assignment_manager.views.assignments.GitlabService')
    @patch('assignment_manager.views.assignments.StudentRepo')
    @patch('assignment_manager.views.assignments.GroupRepo')
    @patch('assignment_manager.views.assignments.Student')
    @patch('assignment_manager.views.assignments.Group')
    def test_publish_manually(self, mock_gitlab_service, mock_student_repo, mock_group_repo, mock_student, mock_group, mock_get_object_or_404):
        #set up
        mock_gitlab_service_instance = mock_gitlab_service.return_value
        mock_gitlab_service_instance.add_assignment.return_value = True
        assignment = AssignmentFactory(is_individual = True)

        #mock stuff
        mock_get_object_or_404.return_value = assignment
        mock_student_repo_instance = mock_student_repo.return_value
        mock_student_repo_instance.exists.return_value = False
        mock_student.objects.exclude.return_value.distinct.return_value = None
        mock_student.objects.filter.return_value.distinct.return_value = None
        mock_group.objects.exclude.return_value.distinct.return_value = None
        mock_group.objects.all.return_value = None


        # Case 1: Individual assignment
        assignment.is_individual = True
        assignment.save()
        mock_student_repo.objects.filter.return_value.exists.return_value = False
        url = reverse('publish_manually', args=[assignment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        assignment.refresh_from_db()

        # Case 2: Group assignment
        assignment.is_individual = False
        mock_group_repo_instance = mock_group_repo.return_value
        mock_group_repo_instance.exists.return_value = False
        mock_group_repo.objects.filter.return_value.exists.return_value = False
        assignment.save()  # Save the change to is_individual

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        assignment.refresh_from_db()


    
    def test_assignment_detail(self):
        assignment = Assignment.objects.get(title='Assignment_1')
        url = reverse('assignment_details', args=[assignment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First assignment')


class HelperFunctionsTestCase(TestCase):
    def setUp(self):
        self.course = CourseFactory(course_code='CS101')
        self.assignment = AssignmentFactory(
            course=self.course,
            title='Assignment_1'
        )
        self.factory = RequestFactory()

    # TODO: fix after integration
    # def test_handle_uploaded_master(self):
    #     # Create file instances
    #     content1 = b"file content"
    #     file1 = SimpleUploadedFile("file1.txt", content1, content_type="text/plain")
    #
    #     data = {
    #         'unit_file': [file1],
    #         'unit_type': ['master']
    #     }
    #     request = self.factory.post('/fake-url/', data, format='multipart')
    #
    #     handle_uploaded_files(request, self.assignment)
    #
    #     self.assertEqual(AssignmentUnit.objects.filter(assignment=self.assignment).count(), 1)
    #
    #     # todo: Path is wrong here
    #     master_path = os.path.join(settings.BASE_DIR.parent / 'project_files/assignments' / self.assignment.title / 'master' / file1.name)
    #
    #     self.assertTrue(os.path.exists(master_path) , "The file does not exist in the filesystem.")
    #
    #     with open(master_path, 'rb') as f:
    #         self.assertEqual(f.read(), content1, "The file content is incorrect.")
    #
    # def test_handle_uploaded_non_master(self):
    #     content2 = b"another file content"
    #     file2 = SimpleUploadedFile("file2.txt", content2, content_type="text/plain")
    #
    #     data = {
    #         'unit_file': [file2],
    #         'unit_type': ['non_master']
    #     }
    #     request = self.factory.post('/fake-url/', data, format='multipart')
    #
    #     handle_uploaded_files(request, self.assignment)
    #
    #     self.assertEqual(AssignmentUnit.objects.filter(assignment=self.assignment).count(), 1)
    #
    #     # todo: Path is wrong here
    #     non_master_path = os.path.join(settings.BASE_DIR.parent / 'project_files/assignments' / self.assignment.title / 'non_master' / file2.name)
    #     self.assertTrue(os.path.exists(non_master_path), "The file does not exist in the filesystem.")
    #
    #     with open(non_master_path, 'rb') as f:
    #         self.assertEqual(f.read(), content2, "Tcontent is incorrect.")



    def tearDown(self):
        path = os.path.join(settings.ASSIGNMENTS_ROOT)
        if os.path.exists(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(path)