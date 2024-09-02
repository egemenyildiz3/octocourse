from django.test import TestCase
from django.urls import reverse

from assignment_manager.factories import StudentFactory, CourseFactory
from assignment_manager.models import Student
from authentication.models import CustomUser, Role


class StudentViewsTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.client.login(username='testuser', password='testpassword')
        self.course = CourseFactory()
        session = self.client.session
        session['selected_course_id'] = self.course.pk
        session.save()
        self.student = StudentFactory(
            first_name='John',
            email='john@example.com',
        )
        self.student.courses_enrolled.add(self.course)

    def test_add_student(self):
        url = reverse('add_student')
        data = {
            'net_id': 'student2',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'enrollment_year': 2021,
            'program': 'Computer Engineering',
            'msc_track': 'Machine Learning',
            'self_assessed_skill': 'Java',
            'nationality_type': 'UK',
            'start_year_in_mude': 2020,
            'brightspace_id': '54321',
            'gitlab_id': 'janesmith',
            'public_ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Student.objects.filter(email='jane@example.com').exists())

    def test_edit_student_view(self):
        url = reverse('edit_student', args=[self.student.id])
        new_data = {
            'net_id': 'student3',
            'first_name': 'Mohammed',
            'last_name': 'Shomis',
            'email': 'mohammed@example.com',
            'enrollment_year': 2021,
            'program': 'Computer Engineering',
            'msc_track': 'Machine Learning',
            'self_assessed_skill': 'Java',
            'nationality_type': 'UK',
            'start_year_in_mude': 2020,
            'brightspace_id': '54321',
            'gitlab_id': 'mohammedshomis',
            'public_ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC'
        }
        response = self.client.post(url, new_data)
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()

        self.assertEqual(self.student.first_name, 'Mohammed')
        self.assertEqual(self.student.last_name, 'Shomis')

    def test_delete_student(self):
        student = Student.objects.get(email='john@example.com')
        url = reverse('delete_student', args=[student.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Student.objects.filter(email='john@example.com').exists())

    def test_search_students(self):
        url = reverse('search_students')
        response = self.client.get(url, {'search_query': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John')

    def test_filter_students(self):
        url = reverse('filter_students')
        response = self.client.get(url, {'filter': 'first_name', 'value': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John')