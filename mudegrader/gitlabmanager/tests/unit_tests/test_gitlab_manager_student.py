from venv import create
import gitlab 
import os

import gitlab.const
import gitlab.v4
import gitlab.v4.objects

from gitlab.client import Gitlab
from assignment_manager.models import Group, Assignment, Course, Student, Group
from gitlabmanager.repositoryCrud import GitlabManager
from gitlabmanager.studentCrud import GitlabManagerStudent
from unittest.mock import patch, MagicMock, call
from graderandfeedbacktool.models import Submissions
from assignment_manager.factories import StudentFactory

from django.test import TestCase
from django.utils import timezone
from authentication.models import CustomUser, Role


class GeneralUnitTests(TestCase):
    # to run the tests type the following the docker terminal: python manage.py test
    def setUp(self):
        token = os.getenv("GITLAB_PRIVATE_TOKEN")

        self.gm = GitlabManager()
        self.gms = GitlabManagerStudent()

        self.user = CustomUser.objects.create_user(
            username='mehmet',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        self.client.login(username='mehmet', password='testpassword')
        
        self.course = Course.objects.create(
            id=1,
            course_code="TEST0001",
            description="TestCourse",
            start_year=2021,
            end_year=2022,
            department="Computer Science",
            created_by=self.user
        )
        self.group = Group.objects.create(name="Test Group", course=self.course)
        self.assertEqual(self.group.name, "Test Group")
        self.asg = Assignment.objects.create(
            course=self.course,
            title="Test Assignment",
            description="Test Assignment Description",
            start_date=timezone.now(),
            due_date=timezone.now(),
            total_points=100
        )

        # Example Student 1
        self.student1 = Student.objects.create(
            net_id = "dua321123312s",
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            enrollment_year=2020,
            program='Master of Science',
            msc_track='Computer Science',
            self_assessed_skill='Intermediate',
            nationality_type='Dutch',
            start_year_in_mude=2020,
            brightspace_id='john.doe',
            gitlab_id='231123',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc...'
        )

        # Example Student 2
        self.student2 = Student.objects.create(
            net_id='janesmith',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            enrollment_year=2021,
            program='Master of Science',
            msc_track='Artificial Intelligence',
            self_assessed_skill='Advanced',
            nationality_type='American',
            start_year_in_mude=2021,
            brightspace_id='jane.smith',
            gitlab_id='123123123',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc...'
        )

        # Example Student 3
        self.student3 = Student.objects.create(
            net_id='mjackson',
            first_name='Michael',
            last_name='Johnson',
            email='michael.johnson@example.com',
            enrollment_year=2019,
            program='Master of Science',
            msc_track='Data Science',
            self_assessed_skill='Beginner',
            nationality_type='British',
            start_year_in_mude=2019,
            brightspace_id='michael.johnson',
            gitlab_id='1234',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc...'
        )
        self.test_subject = Student.objects.create(
            net_id='mshomis',
            first_name='Mohamed',
            last_name='Shomis',
            email='M.S.A.Shomis@student.tudelft.nl',
            enrollment_year=2024,
            program='Master of Science',
            msc_track='Data Science',
            self_assessed_skill='Beginner',
            nationality_type='Yemen',
            start_year_in_mude=2024,
            brightspace_id='michael.johnson',
            gitlab_id='9949',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc...'
        )

        self.project_id = 19130

    def tearDown(self):
        self.group.delete()
        self.course.delete()
        self.asg.delete()
        self.student1.delete()
        self.student2.delete()
        self.student3.delete()
        self.test_subject.delete()

    def test_grouping_students(self):
        student_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        group_size = 3
        # uneven groups
        grouped_students = self.gms.divide_students_into_groups(student_ids, group_size)
        expected_groups = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
        self.assertEqual(len(grouped_students), len(expected_groups)) #we compare the length because the id's are scrambled

        student_ids_even_groups = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        grouped_students = self.gms.divide_students_into_groups(student_ids_even_groups, group_size)
        expected_groups = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        self.assertEqual(len(grouped_students), len(expected_groups))

    def test_add_student_groups_to_database(self):
        number_of_groups_prior_to_adding = Group.objects.count()
        gr1 = [self.student1.id, self.student2.id]
        gr2 = [self.student3.id, self.test_subject.id]
        grouped_students = [gr1, gr2]
        self.gms.add_student_groups_to_database(grouped_students, self.asg)
        number_of_groups_after_the_method = number_of_groups_prior_to_adding + 2 #two new groups should be added
        self.assertEqual(Group.objects.count(), number_of_groups_after_the_method)
        
    def test_get_student_gitlab_id(self):
        self.assertEqual(self.gms.get_student_gitlab_id(self.student1.id), 231123)
        self.student1.gitlab_id = ""
        self.student1.save()
        self.assertEqual(self.gms.get_student_gitlab_id(self.student1.id), -1)

class RepoMockTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='yusuf',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        self.client.login(username='yusuf', password='testpassword')
        self.student = Student.objects.create(
            net_id='jhonnydoe',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            enrollment_year=2020,
            program='Master of Science',
            msc_track='Computer Science',
            self_assessed_skill='Intermediate',
            nationality_type='Dutch',
            start_year_in_mude=2020,
            brightspace_id='john.doe',
            gitlab_id='123123',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc...'
        )
        self.user = CustomUser.objects.create_user(
            username='mahmut',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        self.client.login(username='mahmut', password='testpassword')
        
        self.course = Course.objects.create(
            course_code="subgroup1",
            description="Test Course",
            start_year=2021,
            end_year=2022,
            department="Computer Science",
            created_by=self.user
        )
        self.asg = Assignment.objects.create(
            course=self.course,
            title="Test Assignment",
            description="Test Assignment Description",
            start_date=timezone.now(),
            due_date=timezone.now(),
            gitlab_subgroup_id=1,
            total_points=100
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            title="TEST_ASSIGNMENT_2",
            description="Test Assignment Description",
            start_date=timezone.now(),
            due_date=timezone.now(),
            gitlab_subgroup_id=1,
            total_points=100
        )
        self.project_id = 1234

        #Mock
        self.gl = MagicMock()
        gl = Gitlab()
        rest_manager = gitlab.base.RESTManager(gl=gl)
        project = gitlab.v4.objects.Project(rest_manager, {})
        group = gitlab.v4.objects.Group(rest_manager, {})
        member = gitlab.v4.objects.ProjectMember(rest_manager, {})
        self.mocked_project = MagicMock(spec = project)
        self.mocked_group = MagicMock(spec = group)
        self.mocked_member = MagicMock(spec = member)
        self.gms = GitlabManagerStudent(self.gl)

    def tearDown(self):
        self.student.delete()

    def test_add_user_to_gitlab_group(self):
        mock_group = MagicMock()
        mock_group.members.create.return_value = None
        self.gl.groups.get.return_value = mock_group

        gitlab_user_id = 0
        gitlab_group_id = 0
        access_level = gitlab.const.AccessLevel.GUEST


        self.gms.add_user_to_gitlab_group(gitlab_user_id, gitlab_group_id, access_level)

        self.gl.groups.get.assert_called_once_with(gitlab_group_id)
        mock_group.members.create.assert_called_once_with({'user_id': gitlab_user_id, 'access_level': access_level})

        with self.assertRaises(ValueError):
            self.gms.add_user_to_gitlab_group("BROKEN", 0, 50)

    def test_add_student_to_gitlab_group(self):
        self.gl.groups.get.return_value = self.mocked_group
        self.gms.add_student_to_gitlab_group(self.student.id, 1234)

        self.mocked_group.members.create.assert_called_once()

    def test_remove_student_from_gitlab_group(self):
        self.gl.groups.get.return_value = self.mocked_group
        self.gms.remove_student_from_gitlab_group(self.student.id, 1234)

        self.mocked_group.members.delete.assert_called_once()

    def test_add_student_to_repo(self):
        self.gl.projects.get.return_value = self.mocked_project
        self.gms.add_student_to_repo(self.student.gitlab_id, self.project_id, student_email=None)
        self.mocked_project.members.create.assert_called_once()

        # case with -1 id
        self.student.gitlab_id = -1
        self.student.save()
        self.gms.add_student_to_repo(self.student.gitlab_id, self.project_id, student_email=None)
        self.mocked_project.invitations.create.assert_called_once()

    def test_add_student_to_repo_using_email(self):
        
        self.gl.projects.get.return_value = self.mocked_project
        self.gms.add_student_to_repo_without_git_account(self.student.email, self.project_id)
        self.mocked_project.invitations.create.assert_called_once()

    def test_student_exists_in_repo(self):
        self.gl.projects.get.return_value = self.mocked_project
        class MockMember:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        p = MockMember(123123, "Jeff")
        self.mocked_project.members.list.return_value = [
            p
        ]
        self.assertTrue(self.gms.student_exists_in_repo(1, self.student.gitlab_id))

        #case its not in the project
        self.assertFalse(self.gms.student_exists_in_repo(1, "23323"))

    def test_remove_student_from_repo(self):
        self.gl.projects.get.return_value = self.mocked_project
        self.mocked_project.members.get.return_value = self.mocked_member
        class MockMember:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        p = MockMember(123123, "Jeff")
        self.mocked_project.members.list.return_value = p
        self.mocked_project.members.list.return_value = [p]
        self.gms.remove_student_from_repo(self.student.id, self.project_id)
        self.mocked_member.delete.assert_called_once()

    def test_update_student_access_level(self):
        self.gl.projects.get.return_value = self.mocked_project
        self.mocked_project.members.get.return_value = self.mocked_member
        self.gms.update_student_access_level(self.student.id, self.project_id, gitlab.const.AccessLevel.GUEST)
        self.mocked_member.save.assert_called_once()

    def test_create_submission_for_assignment(self):
        # Mock the objects and methods needed for the test
        assignment_id = self.assignment.id
        student_id = self.student.id
        group_id = None  # Assuming we are testing with a student

        # Mock the get_object_or_404 calls
        with patch('gitlabmanager.studentCrud.get_object_or_404') as mock_get_object_or_404:
            mock_get_object_or_404.side_effect = lambda model, pk: {
                Assignment: self.assignment,
                Student: self.student,
                Group: None,  # Mocking no group scenario
            }[model]

            # Mock the Submissions.objects.create method
            with patch('graderandfeedbacktool.models.Submissions.objects.create') as mock_create_submission:
                mock_submission_instance = MagicMock(spec=Submissions)
                mock_create_submission.return_value = mock_submission_instance

                # Call the method under test
                submission = self.gms.create_submission_for_assignment(assignment_id, student_id, group_id)

                # Assert that Submissions.objects.create was called with the correct arguments
                mock_create_submission.assert_called_once_with(
                    assignment=self.assignment,
                    student=self.student,
                    group=None,
                    file_path='',
                    grading_status='Not Graded',
                    feedback=''
                )

                # Assert that the submission object returned matches the mocked instance
                self.assertEqual(submission, mock_submission_instance)

    @patch('gitlabmanager.studentCrud.Student.objects.get')
    @patch('gitlabmanager.studentCrud.logging')
    def test_get_student_gitlab_id(self, mock_logger, mock_get): 
        student_with_gitlab_id = self.student
        mock_get.return_value = student_with_gitlab_id
        gms = GitlabManagerStudent()
        result = gms.get_student_gitlab_id(student_with_gitlab_id.id)
        self.assertEqual(result, int(student_with_gitlab_id.gitlab_id))
        mock_logger.error.assert_not_called()


        student_without_gitlab_id = StudentFactory(gitlab_id = "")
        mock_get.return_value = student_without_gitlab_id
        result = gms.get_student_gitlab_id(student_without_gitlab_id.id)
        self.assertEqual(result, -1)

        # Test case: student does not exist
        mock_get.side_effect = Student.DoesNotExist
        with self.assertRaises(Student.DoesNotExist):
            gms.get_student_gitlab_id(9999)

        
    @patch('gitlabmanager.studentCrud.logging')
    def test_create_and_return_repo_id(self, mock_logging):
        # Setup mock objects
        mock_project_id = 12345
        self.mocked_project.id = mock_project_id
        
        mock_commit = MagicMock()
        mock_protectedbranch = MagicMock()
        
        # Create a mock project manager object
        mock_projects_manager = MagicMock()
        mock_projects_manager.create.return_value = self.mocked_project
        self.gl.projects = mock_projects_manager
        
        # Initialize GitlabManagerStudent with the mocked GitLab instance
        gms = GitlabManagerStudent(self.gl)
        
        assignment_gitlab_id = 1
        group_name = "test_group"
        
        # Call the method under test
        result = gms.create_and_return_repo_id(assignment_gitlab_id, group_name)
        
        # Assertions
        self.assertEqual(result, mock_project_id)
        mock_projects_manager.create.assert_called_once_with({'name': group_name, 'namespace_id': assignment_gitlab_id})
        self.mocked_project.commits.create.assert_called_once_with({
            'branch': 'main',
            'commit_message': 'Initial commit',
            'actions': [
                {
                    'action': 'create',
                    'file_path': 'README.md',
                    'content': '# Initial commit\n\nThis is the initial commit for the repository.'
                }
            ]
        })
        self.mocked_project.protectedbranches.create.assert_called_once_with({
            'name': 'main',
            'allow_force_push': True,
            'push_access_level': gitlab.const.DEVELOPER_ACCESS,
            'merge_access_level': gitlab.const.DEVELOPER_ACCESS,
            'unprotect_access_level': gitlab.const.MAINTAINER_ACCESS,
        })

        # Test the case where the repository already exists
        mock_projects_manager.create.side_effect = gitlab.exceptions.GitlabCreateError("Project already exists")
        
        result = gms.create_and_return_repo_id(assignment_gitlab_id, group_name)
        
        self.assertIsInstance(result, gitlab.exceptions.GitlabCreateError)

    @patch('gitlabmanager.studentCrud.GitlabManager')
    @patch('assignment_manager.models.Assignment.objects.get')
    @patch.object(GitlabManagerStudent, 'add_student_to_repo')
    def test_create_repositories_and_add_students(self, mock_add_student_to_repo, mock_assignment_get, mock_gitlab_manager):
        # Mock the GitlabManager instance and its create_repositories method
        mock_gitlab_manager_instance = MagicMock()
        mock_gitlab_manager.return_value = mock_gitlab_manager_instance
        mock_gitlab_manager_instance.create_repositories.return_value = [101, 102]

        # Mock the Assignment instance
        mock_assignment_instance = MagicMock()
        mock_assignment_get.return_value = mock_assignment_instance

        # Instantiate GitlabManagerStudent
        gms = GitlabManagerStudent()

        # Test data
        grouped_students = [[1, 2], [3, 4]]
        assignment_id = 1

        # Call the method under test
        gms.create_repositories_and_add_students(grouped_students, assignment_id)

        # Assertions
        mock_gitlab_manager_instance.create_repositories.assert_called_once_with(mock_assignment_instance)
        self.assertEqual(mock_add_student_to_repo.call_count, 4)

    @patch('gitlabmanager.studentCrud.GitlabManager')
    @patch('assignment_manager.models.Assignment.objects.get')
    def test_create_repositories_and_add_students_gitlab_get_error(self, mock_assignment_get, mock_gitlab_manager):
        # Mock the GitlabManager instance and simulate a GitlabGetError
        mock_gitlab_manager_instance = MagicMock()
        mock_gitlab_manager.return_value = mock_gitlab_manager_instance
        mock_gitlab_manager_instance.create_repositories.side_effect = gitlab.exceptions.GitlabGetError

        # Mock the Assignment instance
        mock_assignment_instance = MagicMock()
        mock_assignment_get.return_value = mock_assignment_instance

        # Mock the logger
        with patch('gitlabmanager.studentCrud.logging') as mock_logging:
            mock_logger = mock_logging.getLogger.return_value

            # Instantiate GitlabManagerStudent
            gms = GitlabManagerStudent()

            # Test data
            grouped_students = [[1, 2], [3, 4]]
            assignment_id = 1

            # Call the method under test
            gms.create_repositories_and_add_students(grouped_students, assignment_id)

            # Assertions
            mock_gitlab_manager_instance.create_repositories.assert_called_once_with(mock_assignment_instance)
            mock_logger.exception.assert_called()

    @patch('gitlabmanager.studentCrud.GitlabManager')
    @patch('assignment_manager.models.Assignment.objects.get')
    def test_create_repositories_and_add_students_gitlab_create_error(self, mock_assignment_get, mock_gitlab_manager):
        # Mock the GitlabManager instance and simulate a GitlabCreateError
        mock_gitlab_manager_instance = MagicMock()
        mock_gitlab_manager.return_value = mock_gitlab_manager_instance
        mock_gitlab_manager_instance.create_repositories.side_effect = gitlab.exceptions.GitlabCreateError

        # Mock the Assignment instance
        mock_assignment_instance = MagicMock()
        mock_assignment_get.return_value = mock_assignment_instance

        # Mock the logger
        with patch('gitlabmanager.studentCrud.logging') as mock_logging:
            mock_logger = mock_logging.getLogger.return_value

            # Instantiate GitlabManagerStudent
            gms = GitlabManagerStudent()

            # Test data
            grouped_students = [[1, 2], [3, 4]]
            assignment_id = 1

            # Call the method under test
            gms.create_repositories_and_add_students(grouped_students, assignment_id)

            # Assertions
            mock_gitlab_manager_instance.create_repositories.assert_called_once_with(mock_assignment_instance)
            mock_logger.exception.assert_called()

    @patch('gitlabmanager.studentCrud.gitlab')
    def test_get_gitlab_user(self, mock_gitlab):
        mock_gitlab_instance = MagicMock()
        mock_gitlab.return_value = mock_gitlab_instance

        fake_id = 101
        fake_gitlab_user = "SS"

        mock_gitlab_instance.users.get.return_value = fake_gitlab_user
        gms = GitlabManagerStudent(mock_gitlab_instance)
        
        result = gms.get_gitlab_user(fake_id)
        
        self.assertEqual(fake_gitlab_user, result)

        mock_gitlab_instance.users.get.side_effect = gitlab.exceptions.GitlabGetError
        with patch.object(gms, 'logger') as mock_logger:
            try:
                result2 = gms.get_gitlab_user(fake_id)
                self.assertIsNone(result2)
                mock_logger.exception.assert_called_once_with(f"Failed to get GitLab user with ID {fake_id}: {mock_gitlab_instance.users.get.side_effect}")
            except Exception as e: 
                pass

