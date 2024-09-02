from django.test import TestCase

from assignment_manager.models import Student, Group, GroupMember, Course
from authentication.models import CustomUser, Role


class GroupsModelTest(TestCase):
    """Tests for the Groups model."""

    def setUp(self):
        """Set up a group for testing."""
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
        self.group = Group.objects.create(name='Jasper', course=self.course)

    def test_group_creation(self):
        """Test creating a group with valid data."""
        self.assertEqual(self.group.name, 'Jasper')


class GroupMembersModelTest(TestCase):
    """Tests for the GroupMembers model."""

    def setUp(self):
        """Set up a group membership for testing."""
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
        self.group = Group.objects.create(name='Jasper', course=self.course)
        self.group_member = GroupMember.objects.create(student_id=self.student, group_id=self.group)

    def test_group_membership(self):
        """Test creating a group membership with valid data."""
        self.assertEqual(self.group_member.student_id, self.student)
        self.assertEqual(self.group_member.group_id, self.group)
