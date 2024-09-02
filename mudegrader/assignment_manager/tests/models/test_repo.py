from django.test import TestCase

from assignment_manager.models import Student, Group, StudentRepo, GroupRepo, Assignment
from assignment_manager.factories import AssignmentFactory, StudentFactory, GroupFactory, CourseFactory

class RepoModelTest(TestCase):
    """Tests for the Students model."""

    def setUp(self):
        """Set up a student for testing."""
        self.course = CourseFactory()
        self.student = StudentFactory()
        self.student.courses_enrolled.add(self.course)
        self.assignment = AssignmentFactory()
        self.group = GroupFactory()
        self.student_repo = StudentRepo.objects.create(
            student = self.student,
            repository_id = 0,
            assignment = self.assignment
        )
        self.group_repo = GroupRepo.objects.create(
            group = self.group,
            repository_id = 1,
            assignment = self.assignment
        )

    def test_student_repo(self):
        self.assertEqual(self.student_repo.student, self.student)
        self.assertEqual(self.student_repo.repository_id, 0)

    def test_group_repo(self):
        self.assertEqual(self.group_repo.group, self.group)
        self.assertEqual(self.group_repo.repository_id, 1)