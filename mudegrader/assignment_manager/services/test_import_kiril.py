from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from assignment_manager.factories import CourseFactory, StudentFactory
from assignment_manager.services.import_kiril_output import load_class
from authentication.models import Role, CustomUser
from assignment_manager.models import Group, Student

@patch('assignment_manager.services.import_kiril_output.get_gitlab_id_by_netid')
class KirilImportTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(
            role=Role.TEACHER
        )
        self.course = CourseFactory()
        self.course.staff.add(self.user)
        self.course.save()

    def test_load_class_with_csv(self, mock_get_gitlab_id):
        mock_get_gitlab_id.return_value = 'gitlabXYZ'

        csv_data = """OrgDefinedId,Username,LastName,FirstName,Email,GroupCategory,GroupName
                      1,jdoe@school.edu,Doe,John,jdoe@school.edu,Test Group,Red_Group
                      2,asmith@school.edu,Smith,Anna,asmith@school.edu,Test Group,Blue_Group"""
        csv_file = SimpleUploadedFile("students.csv", csv_data.encode('utf-8'), content_type="text/csv")

        load_class(csv_file, self.course)

        self.assertEqual(Student.objects.count(), 2)
        self.assertEqual(Group.objects.count(), 2)
        self.assertTrue(Student.objects.filter(net_id="jdoe").exists())
        self.assertTrue(Group.objects.filter(name="Red_Group").exists())

    def test_load_class_with_missing_columns(self, mock_get_gitlab_id):
        mock_get_gitlab_id.return_value = 'gitlabABC'

        csv_data = """LastName,FirstName,Email
                  Doe,John,jdoe@school.edu
                  Smith,Anna,asmith@school.edu"""
        csv_file = SimpleUploadedFile("students.csv", csv_data.encode('utf-8'), content_type="text/csv")

        with self.assertRaises(ValueError):
            load_class(csv_file, self.course)

        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Group.objects.count(), 0)

    def test_load_class_with_invalid_data(self, mock_get_gitlab_id):
        mock_get_gitlab_id.return_value = 'gitlabDEF'

        csv_data = """OrgDefinedId,Username,LastName,FirstName,Email,GroupCategory,GroupName
              1,invalid_email,Doe,John,,Test Group,Red Group
              2,asmith@school.edu,Smith,Anna,asmith@school.edu,Test Group,Blue Group"""
        csv_file = SimpleUploadedFile("students.csv", csv_data.encode('utf-8'), content_type="text/csv")

        load_class(csv_file, self.course)

        self.assertEqual(Student.objects.count(), 1)
        self.assertTrue(Student.objects.filter(net_id="asmith").exists())
        self.assertFalse(Student.objects.filter(net_id="invalid_email").exists())

    def test_load_class_with_empty_csv(self, mock_get_gitlab_id):
        mock_get_gitlab_id.return_value = 'gitlabGHI'

        csv_data = "OrgDefinedId,Username,LastName,FirstName,Email,GroupCategory,GroupName"
        csv_file = SimpleUploadedFile("empty.csv", csv_data.encode('utf-8'), content_type="text/csv")

        load_class(csv_file, self.course)

        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Group.objects.count(), 0)

    def test_load_class_with_duplicates(self, mock_get_gitlab_id):
        mock_get_gitlab_id.return_value = 'gitlabJKL'

        csv_data = """OrgDefinedId,Username,LastName,FirstName,Email,GroupCategory,GroupName
              1,jdoe@school.edu,Doe,John,jdoe@school.edu,Test Group,Red Group
              1,jdoe@school.edu,Doe,John,jdoe@school.edu,Test Group,Red Group"""
        csv_file = SimpleUploadedFile("duplicates.csv", csv_data.encode('utf-8'), content_type="text/csv")

        load_class(csv_file, self.course)

        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Group.objects.count(), 1)

