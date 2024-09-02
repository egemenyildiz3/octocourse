from django.test import TestCase

from assignment_manager.models import Course, Assignment, Student, Group, Comment
from django.utils import timezone
from datetime import timedelta
from authentication.models import CustomUser, Role



class CommentModelTest(TestCase):
    """Tests for the Comment model."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.course = Course.objects.create(
            course_code='CS102',
            description='Introduction to Computer Science',
            start_year=2023,
            end_year=2024,
            department='EEMCS',
            created_by=self.user
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            title='PA11',
            description='First assignment',
            start_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=7),
            total_points=100,
            is_published=True
        )
        self.student = Student.objects.create(
            first_name='Mohammed',
            last_name='Yusuf',
            email='mohammed@example.com',
            enrollment_year=2022,
            program='Computer Science',
            msc_track='Data Science',
            self_assessed_skill='Python',
            nationality_type='American',
            start_year_in_mude=2023,
            brightspace_id='MJ123',
            gitlab_id='mohammed_yusuf',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB...'
        )
        self.group = Group.objects.create(name='group1', course=self.course)
        self.assignment_comment = Comment.objects.create(
            comment_text='This is a test comment.',
            comment_time=timezone.now(),
            content_object=self.assignment,
            author=self.user
        )
        self.student_comment = Comment.objects.create(
            comment_text='This is a test comment.',
            comment_time=timezone.now(),
            content_object=self.student,
            author=self.user,
        )
        self.group_comment = Comment.objects.create(
            comment_text='This is a test comment.',
            comment_time=timezone.now(),
            content_object=self.group,
            author=self.user,
        )

    def test_comment_creation(self):
        """Test if comments were created successfully."""
        self.assertEqual(self.assignment_comment.comment_text, "This is a test comment.")
        self.assertEqual(self.assignment_comment.content_object, self.assignment)

        self.assertEqual(self.student_comment.comment_text, "This is a test comment.")
        self.assertEqual(self.student_comment.content_object, self.student)

        self.assertEqual(self.group_comment.comment_text, "This is a test comment.")
        self.assertEqual(self.group_comment.content_object, self.group)

    def test_comment_deletion(self):
        # Delete the comment
        comment_id = self.group_comment.id
        self.group_comment.delete()

        # Check if the comment is deleted
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=comment_id)

    def test_retrieve_comment_from_assignment(self):
        comments = self.assignment.comments.all()

        self.assertIn(self.assignment_comment, comments)
        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments.first().comment_text, "This is a test comment.")

    def test_retrieve_comment_from_student(self):
        comments = self.student.comments.all()

        self.assertIn(self.student_comment, comments)
        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments.first().comment_text, "This is a test comment.")

    def test_retrieve_comment_from_group(self):
        comments = self.group.comments.all()

        self.assertIn(self.group_comment, comments)
        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments.first().comment_text, "This is a test comment.")
