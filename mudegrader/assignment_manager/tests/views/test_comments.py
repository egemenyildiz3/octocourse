from django.test import TestCase
from django.urls import reverse

from assignment_manager.factories import CourseFactory, AssignmentFactory, StudentFactory, GroupFactory
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
        self.student = StudentFactory()
        self.student.courses_enrolled.add(self.course)
        self.group = GroupFactory(
            name='group1',
        )
        self.group.assignments.add(self.assignment)
        self.group.save()
        session = self.client.session
        session['selected_course_id'] = self.course.pk
        session.save()

    def test_add_and_delete_comment_on_assignment(self):
        # adding comment
        add_url = reverse('assignment_details', args=[self.assignment.pk])
        self.assertEqual(self.assignment.comments.count(), 0)
        data = {'comment_text': 'Sample Text 0'}
        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.assignment.comments.count(), 1)
        new_comment = self.assignment.comments.first()
        self.assertEqual(new_comment.comment_text, 'Sample Text 0')
        # deleting comment
        del_url = reverse('delete_comment', args=[new_comment.pk])
        response = self.client.post(del_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.assignment.comments.count(), 0)


    def test_add_comment_on_student(self):
        url = reverse('student_details', args=[self.student.pk])
        self.assertEqual(self.student.comments.count(), 0)
        data = {'comment_text': 'Sample Text 1'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.student.comments.count(), 1)
        self.assertEqual(self.student.comments.first().comment_text, 'Sample Text 1')

    def test_add_comment_on_group(self):
        url = reverse('group_details', args=[self.group.id])
        self.assertEqual(self.group.comments.count(), 0)
        data = {'comment_text': 'Sample Text 2'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.group.comments.count(), 1)
        self.assertEqual(self.group.comments.first().comment_text, 'Sample Text 2')
