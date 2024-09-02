from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse

from assignment_manager.models import Course
from assignment_manager.factories import CourseFactory
from authentication.models import CustomUser, Role


class CourseViewsTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        self.client.login(username='testuser', password='testpassword')

        self.course = CourseFactory(
            course_code='CS101',
            description='Introduction to Computer Science',
            created_by=self.user
        )

        self.user.courses.add(self.course)

    @patch('assignment_manager.views.courses.GitlabService')
    def test_add_course(self, mock_gitlab_service):
        mock_gitlab_service.create_course.return_value = "Mock_Course"
        url = reverse('add_course')
        data = {
            'course_code': 'CS102',
            'description': 'Advanced Computer Science',
            'start_year': 2023,
            'end_year': 2024,
            'department': 'Computer Science',

        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  
        self.assertTrue(Course.objects.filter(course_code='CS102').exists())

    @patch('assignment_manager.views.courses.GitlabService')
    def test_delete_course(self, mock_gitlab_service):
        mock_gitlab_service.remove_course.return_value = "Deleted_Mock_Course"
        course = Course.objects.get(course_code='CS101')
        url = reverse('delete_course', args=[course.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  
        self.assertFalse(Course.objects.filter(course_code='CS101').exists())

    @patch('assignment_manager.views.courses.GitlabService')
    def test_edit_course(self, mock_gitlab_service):
        mock_gitlab_service.edit_course.return_value = "Edited_Mock_Course"
        course = Course.objects.get(course_code='CS101')
        url = reverse('edit_course', args=[course.id])
        data = {
            'course_code': 'CS101',
            'description': 'Introduction to Computer Science (Edited)',
            'start_year': 2022,
            'end_year': 2023,
            'department': 'Computer Science'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        course.refresh_from_db()
        self.assertEqual(course.description, 'Introduction to Computer Science (Edited)')

    def test_course_list(self):
        url = reverse('course_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CS101')

    def test_course_detail(self):
        course = Course.objects.get(course_code='CS101')
        url = reverse('course_details', args=[course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Introduction to Computer Science')
