import json

from django.test import TestCase
from django.urls import reverse

from assignment_manager.factories import CourseFactory, StudentFactory, AssignmentFactory, GroupFactory
from assignment_manager.models import Group, GroupMember
from authentication.models import CustomUser, Role


class GroupViewsTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.client.login(username='testuser', password='testpassword')

        self.course = CourseFactory()
        self.assignment = AssignmentFactory(course=self.course)
        self.group = GroupFactory(
                name='Group 1',
        )
        self.group.assignments.add(self.assignment)
        self.group.save()
        self.student = StudentFactory(first_name='student1')
        session = self.client.session
        session['selected_course_id'] = self.course.pk
        session.save()

    def test_add_group_view(self):
        url = reverse('add_group')
        data = {
            'name': 'Group 2',
            'assignment_id': self.assignment.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Group.objects.filter(name='Group 2').exists())

    def test_search_student_view(self):
        url = reverse('search_students')
        response = self.client.get(url, {'q': 'student1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student1')

    def test_add_student_to_group_view(self):
        url = reverse('add_student_to_group')
        data = {
            'group_id': self.group.id,
            'student_id': self.student.id
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GroupMember.objects.filter(group_id=self.group, student_id=self.student).exists())

    def test_remove_student_from_group_view(self):
        group_member = GroupMember.objects.create(group_id=self.group, student_id=self.student)
        url = reverse('remove_student_from_group')
        data = {
            'group_id': self.group.id,
            'student_id': self.student.id
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GroupMember.objects.filter(group_id=self.group, student_id=self.student).exists())

    def test_edit_group_view(self):
        url = reverse('edit_group', args=[self.group.id]) 
        new_data = {
            'name': 'Group 2',
            'assignment_id': self.assignment.id,
        }
        response = self.client.post(url, new_data)
        self.assertEqual(response.status_code, 302)  
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Group 2')

    def test_delete_group(self):
        group = Group.objects.get(name='Group 1')
        url = reverse('delete_group', args=[group.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Group.objects.filter(name='Group 1').exists())

    def test_search_groups(self):
        url = reverse('search_groups')
        response = self.client.get(url, {'search_query': 'Group 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Group 1') 

    def test_filter_groups(self):
        url = reverse('filter_groups')
        response = self.client.get(url, {'filter': 'name', 'value': 'Group 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Group 1')
