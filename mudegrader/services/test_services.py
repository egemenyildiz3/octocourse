from django.test import TestCase
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock
from assignment_manager.models import Course, Assignment, Student, Group
from gitlabmanager.repositoryCrud import GitlabManager
from assignment_manager.factories import GroupFactory, StudentFactory, AssignmentFactory
from gitlabmanager.studentCrud import GitlabManagerStudent
from .gitlab_services import GitlabService
from authentication.models import CustomUser, Role


class GeneralUnitTests(TestCase):
    def setUp(self):
        self.gl = MagicMock()
        self.gitlab_services = GitlabService(self.gl)

        self.user = CustomUser.objects.create_user(
            username='testuser',
            role=Role.TEACHER,
        )
        self.user.set_password('testpassword')
        self.course = Course.objects.create(
            course_code="subgroup1",
            description="Test Course",
            start_year=2021,
            end_year=2022,
            department="Computer Science",
            created_by=self.user
        )

        self.student = Student.objects.create(
            net_id = '31312',
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

        self.student.courses_enrolled.add(self.course)

        self.student2 = Student.objects.create(
            net_id='jcena',
            first_name='John',
            last_name='Cena',
            email='john.Cena@example.com',
            enrollment_year=2022,
            program='Master of Science',
            msc_track='Computer Science',
            self_assessed_skill='Intermediate',
            nationality_type='Dutch',
            start_year_in_mude=2023,
            brightspace_id='john.doe',
            gitlab_id='312312',
            public_ssh_key='ssh-rsa AAAAB3NzaC1yc...'
        )

        self.student2.courses_enrolled.add(self.course)

        self.assignment = Assignment.objects.create(
            course=self.course,
            title="Test Assignment",
            description="Test Assignment Description",
            start_date=timezone.now(),
            due_date=timezone.now(),
            gitlab_subgroup_id=1,
            total_points=100
        )


    @patch.object(GitlabManager, 'create_course_group')
    def test_create_course(self, mock_create_course_group):
        mock_create_course_group.return_value = 0  


        result = self.gitlab_services.create_course(self.course)

        self.assertEqual(result, 0)
        mock_create_course_group.assert_called_once_with(self.course)

    @patch.object(GitlabManager, 'remove_course_group')
    def test_remove_course(self, mock_remove_course_group):
        mock_remove_course_group.return_value = 0  

        self.gitlab_services = GitlabService()
        result = self.gitlab_services.remove_course(self.course)

        self.assertEqual(result, 0)
        mock_remove_course_group.assert_called_once_with(self.course)

    @patch.object(GitlabManager, 'update_course_group_name')
    def test_edit_course(self, mock_update_course_group_name):
        mock_update_course_group_name.return_value = 0 

        self.gitlab_services = GitlabService()
        result = self.gitlab_services.edit_course(self.course)

        self.assertEqual(result, 0)
        mock_update_course_group_name.assert_called_once_with(self.course.course_code, self.course.gitlab_subgroup_id)

    @patch.object(GitlabManager, 'create_assignment_group')
    def test_add_assignment(self, mock_create_assignment_group):
        self.gitlab_services = GitlabService()
        self.gitlab_services.add_assignment(self.assignment)

        mock_create_assignment_group.assert_called_once_with(self.assignment)

    @patch.object(GitlabService, 'publish_individual_assignment')
    @patch.object(GitlabService, 'publish_group_assignment')
    @patch.object(GitlabService, 'publish_assignment_read_only')
    def test_publish_assignment_existing_groups(self, mock_publish_assignment_read_only, mock_publish_group_assignment, mock_publish_individual_assignment):
        # Create a mock assignment object
        mock_assignment = Mock()
        
        # Test case where the assignment is individual
        mock_assignment.is_individual = True
        self.gitlab_services.publish_assignment_existing_groups(mock_assignment)
        
        # Verify that publish_individual_assignment is called
        mock_publish_individual_assignment.assert_called_once_with(mock_assignment)
        mock_publish_group_assignment.assert_not_called()
        mock_publish_assignment_read_only.assert_called_once_with(mock_assignment)
        
        # Reset mocks
        mock_publish_individual_assignment.reset_mock()
        mock_publish_group_assignment.reset_mock()
        mock_publish_assignment_read_only.reset_mock()
        
        # Test case where the assignment is not individual
        mock_assignment.is_individual = False
        self.gitlab_services.publish_assignment_existing_groups(mock_assignment)
        
        # Verify the calls:
        mock_publish_group_assignment.assert_called_once_with(mock_assignment)
        mock_publish_individual_assignment.assert_not_called()
        mock_publish_assignment_read_only.assert_called_once_with(mock_assignment)

    @patch.object(GitlabManagerStudent, 'create_and_return_repo_id')
    @patch.object(GitlabManagerStudent, 'add_student_to_repo')
    @patch('services.gitlab_services.DistributionService')
    @patch('assignment_manager.models.Student')
    def test_publish_assignment_read_only(self, mock_student_class, mock_distribution_service, mock_add_student_to_repo, mock_create_and_return_repo_id):
        fake_repo_id = 0
        repo_list = [fake_repo_id]
        mock_create_and_return_repo_id.return_value = fake_repo_id
        mock_add_student_to_repo.return_value = "yay"
        mock_ds_instance = mock_distribution_service.return_value
        mock_ds_instance.distribute_assignment.return_value = None
        
        self.gitlab_services.publish_assignment_read_only(self.assignment)
        mock_ds_instance.distribute_assignment.assert_called_with(self.assignment, repo_list) 
        mock_add_student_to_repo.assert_called

    @patch.object(GitlabManagerStudent, 'create_and_return_repo_id')
    @patch('services.gitlab_services.DistributionService')
    @patch('services.gitlab_services.Group')
    @patch('services.gitlab_services.Student')
    def test_publish_group_assignment(self, mock_student_class, mock_group_class, mock_distribution_service, mock_create_and_return_repo_id):
        fake_group_one = GroupFactory()
        list_of_groups = [fake_group_one]
        mock_group_class.objects.filter.return_value = list_of_groups
        


    @patch.object(GitlabManagerStudent, 'divide_students_into_groups')
    @patch.object(GitlabManagerStudent, 'add_student_groups_to_database')
    @patch.object(GitlabManagerStudent, 'create_repositories_and_add_students')
    def test_publish_assignment(self, mock_create_repos, mock_add_groups, mock_divide_students):
       
        mock_divide_students.return_value = [[self.student.id],[self.student2.id]]
        mock_add_groups.return_value = None
        mock_create_repos.return_value = None

        
        self.gitlab_services.publish_assignment_randomized(self.course, self.assignment, group_size=1)

        mock_divide_students.assert_called_once_with([self.student.id, self.student2.id], 1)
        mock_add_groups.assert_called_once_with([[self.student.id], [self.student2.id]], self.assignment)
        mock_create_repos.assert_called_once_with([[self.student.id], [self.student2.id]], self.assignment.pk)


