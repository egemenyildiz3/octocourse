from unittest import mock
from django.test import TestCase
import gitlab.exceptions

from gitlabmanager.repositoryCrud import GitlabManager
from assignment_manager.models import Assignment, Course, Group, Student
from unittest.mock import patch, MagicMock, call
from django.utils import timezone
from gitlabmanager.distribution_service import DistributionService
import os

from django.http.response import Http404
from graderandfeedbacktool.models import Submissions
from authentication.models import CustomUser, Role


class CommonSetupTestCase(TestCase):

    def setUp(self):
        super().setUp()

        self.gm = GitlabManager(mocked_gl=None)
        self.gl = gitlab.Gitlab(url='https://gitlab.tudelft.nl/', private_token= os.getenv("GITLAB_PRIVATE_TOKEN"))
        
        self.gl.auth()
        print("CALLED")
        if not self.gl.user:
            raise Exception("Authentication failed")    
                
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        self.client.login(username='testuser', password='testpassword')
        
        self.course = Course.objects.create(
            id=1,
            course_code=f"TEST{timezone.now().strftime("%d-%m-%y")}",
            description="TestCourse",
            start_year=2021,
            end_year=2022,
            department="Computer Science",
            created_by=self.user
        )
        self.course.save()
        self.asg = Assignment.objects.create(
            id=1,
            course=self.course,
            title="TestAssignment",
            description="Test Assignment Description",
            start_date=timezone.now(),
            is_individual=False,
            due_date=timezone.now(),
            total_points=100,
            gitlab_subgroup_id=None
        )
        self.indiv_asg = Assignment.objects.create(
            id=2,
            course=self.course,
            title="TestAssignment2",
            description="Test Assignment Description",
            start_date=timezone.now(),
            is_individual=True,
            due_date=timezone.now(),
            total_points=100,
            gitlab_subgroup_id=None
        )
        self.indiv_asg.save()

        self.student1 = Student.objects.create(
            net_id='jhonnydoe',
            first_name='asd',
            last_name='Yusufk',
            email='mohammedasd@example.com',
            enrollment_year=2022,
            program='Computer Science',
            msc_track='Data Science',
            self_assessed_skill='Python',
            nationality_type='American',
            start_year_in_mude=2023,
            brightspace_id='MJs123',
            gitlab_id='mohammedss_yusuf',
            public_ssh_key='ssh-rssa AAAAB3NzaC1yc2EAAAADAQABAAAB...'
        )
        self.student1.save()

        self.group1 = Group.objects.create(name="TestGroup1", course=self.course, creation_date=timezone.now())
        self.group2 = Group.objects.create(name="TestGroup2", course=self.course, creation_date=timezone.now())
        
        self.group1.assignments.add(self.asg)
        self.group2.assignments.add(self.asg)

        self.sub = Submissions.objects.create(
            id=1,
            assignment = self.asg,
            student = None,
            group = self.group1,
            submission_time = timezone.now(),
            file_path = "/app/local_files/poject_gee_q1-main/README.md",
            grading_status = "Not Graded",
            total_points = None,
            feedback = None
        )
        
        self.sub.save()
        self.asg.save()
        self.group1.save()
        self.group2.save()

        # print("Subgroup id:", self.course.gitlab_subgroup_id)
        # self.gm.create_course_group(self.course)
        # print("HERE Subgroup id:", self.course.gitlab_subgroup_id)
        # self.gm.create_assignment_group(self.asg)

        # self.gm.create_repo(self.group1)

    def tearDown(self):
        self.gm.remove_course_group(self.course)
 
        self.asg.delete()
        self.group1.delete()
        self.group2.delete()

class DistributionTests(CommonSetupTestCase):

    def setUp(self):    
        super().setUp() 

    @patch('assignment_manager.models.Assignment.objects.get')
    @patch('gitlab.v4.objects.GroupManager.get')
    @patch('gitlab.v4.objects.ProjectManager.get')
    @patch('os.walk')
    @patch('builtins.open')
    def test_distribute_assignment_success(self, mock_open, mock_os_walk, 
    mock_get_project, mock_get_group, mock_get_assignment):

        mock_group = MagicMock()
        mock_group.projects.list.return_value = [MagicMock(id=1), MagicMock(id=2)]
        mock_get_group.return_value = mock_group

        mock_project = MagicMock()
        mock_get_project.return_value = mock_project

        mock_os_walk.return_value = [("/fake/path", [], ["file.txt"])]

        mock_file = MagicMock()
        mock_file.read.return_value = "file content"
        mock_open.return_value.__enter__.return_value = mock_file

        ds = DistributionService()

        failed_repositories = ds.distribute_assignment(self.asg, [1])

        self.assertEqual(failed_repositories, [])
        mock_get_project.assert_called_once_with(1)
        mock_get_group.assert_called_once_with(self.asg.gitlab_subgroup_id)
        mock_get_project.assert_called()
    
    @patch('gitlab.v4.objects.GroupManager.get')
    @patch('gitlab.v4.objects.ProjectManager.get')
    def test_distribute_assignment_failure(self, mock_get_project, mock_get_group):

        mock_get_group.return_value = MagicMock()

        mock_project = MagicMock()
        mock_project.commits.create.side_effect = gitlab.exceptions.GitlabCreateError
        mock_get_project.return_value = mock_project

        ds = DistributionService()

        failed_repositories = ds.distribute_assignment(self.asg, [MagicMock()])

        self.assertEqual(len(failed_repositories), 1)
        mock_get_project.assert_called()
    
    def tearDown(self) -> None:        
        super().tearDown()


class GatherAndCloneSubmissionTests(CommonSetupTestCase):

    def setUp(self):    
        super().setUp() 
        Submissions.objects.all().delete()

                
    @patch('gitlab.v4.objects.GroupManager.get')
    @patch('gitlab.v4.objects.ProjectManager.list')
    @patch('assignment_manager.models.Assignment.objects.get')
    @patch('subprocess.run')
    def test_gather_submissions_success(self, mock_subprocess_run, mock_get_assignment,
                                        mock_list_projects, mock_get_group):

        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.gitlab_subgroup_id = 1
        mock_get_assignment.return_value = mock_assignment

        mock_group = MagicMock()
        mock_group.projects.list.return_value = [MagicMock(id=58), MagicMock(id=61)]
        mock_get_group.return_value = mock_group

        mock_project = MagicMock()
        mock_project.id = 58
        mock_list_projects.return_value = [mock_project]

        mock_subprocess_run.return_value = 0

        ds = DistributionService()

        ret = ds.gather_submissions(self.course.id, self.asg.gitlab_subgroup_id, 
                                    self.asg.course.course_code, self.asg.title)

        self.assertTrue(isinstance(ret, list))
        self.assertEqual(ret[0].id, 58)
        self.assertEqual(ret[1].id, 61)
        self.assertEqual(len(ret), 2)

    @patch('gitlab.v4.objects.GroupManager.get')
    @patch('gitlab.v4.objects.ProjectManager.list')
    @patch('assignment_manager.models.Assignment.objects.get')
    @patch('subprocess.run')
    def test_gather_submissions_assignment_non_existent(self, mock_subprocess_run,
                                                        mock_get_assignment, mock_list_projects, mock_get_group):

        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.gitlab_subgroup_id = 1
        mock_get_assignment.side_effect = Assignment.DoesNotExist

        mock_group = MagicMock()
        mock_group.projects.list.return_value = [MagicMock(id=58), MagicMock(id=61)]
        mock_get_group.return_value = mock_group

        mock_project = MagicMock()
        mock_project.id = 58
        mock_list_projects.return_value = [mock_project]

        mock_subprocess_run.return_value = 0

        ds = DistributionService()

        ret = ds.gather_submissions(self.course.id, self.asg.gitlab_subgroup_id, 
                                    None, None)
        self.assertTrue(isinstance(ret, Http404))
    
    @patch('graderandfeedbacktool.populations.populate_database_for_one_assignment')
    @patch('requests.get')
    @patch('tempfile.NamedTemporaryFile')
    @patch('tarfile.open')
    @patch('os.makedirs')
    @patch('os.remove')
    @patch('assignment_manager.models.Assignment.objects.get')
    def test_clone_submissions_success(self, mock_get_assignment, mock_remove, 
                                       mock_makedirs, mock_tarfile_open, mock_tempfile,
                                       mock_requests_get, mock_popullate):
        repository1 = MagicMock()
        repository1.name = "repo1"
        repository1.web_url = "http://gitlab.com/repo1"
        repository1.path = "repo1"
        repository2 = MagicMock()
        repository2.name = "repo2"
        repository2.web_url = "http://gitlab.com/repo2"
        repository2.path = "repo2"

        repository_list = [repository1, repository2]

        mock_temp_file = MagicMock()
        mock_temp_file.name = "/fake/temp/file"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file

        mock_response = MagicMock()
        mock_response.content = b'fake content'
        mock_response.__enter__.return_value = mock_response
        mock_requests_get.return_value.__enter__.return_value = mock_response

        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        ds = DistributionService()

        failed_repos = ds.clone_submissions(repository_list, self.course.id, assignment_title="TestAssignment")

        self.assertEqual(len(failed_repos), 0)
    
        expected_path_suffix_repo1 = f"/submissions/{self.course.course_code}/{self.asg.title}/repo1"
        expected_path_suffix_repo2 = f"/submissions/{self.course.course_code}/{self.asg.title}/repo2"

        print("Expected path for repo1:", expected_path_suffix_repo1)
        print("Expected path for repo2:", expected_path_suffix_repo2)
        print("Mock calls to makedirs:", mock_makedirs.call_args_list)

        repo1_path_found = any(expected_path_suffix_repo1 in args[0] for args, kwargs in mock_makedirs.call_args_list)
        repo2_path_found = any(expected_path_suffix_repo2 in args[0] for args, kwargs in mock_makedirs.call_args_list)

        self.assertTrue(repo1_path_found, f"Path suffix {expected_path_suffix_repo1} not found in makedirs calls.")
        self.assertTrue(repo2_path_found, f"Path suffix {expected_path_suffix_repo2} not found in makedirs calls.")
        self.assertEqual(mock_tempfile.return_value.__enter__.call_count, 2)
        self.assertEqual(mock_tarfile_open.return_value.__enter__.call_count, 2)
        

    def tearDown(self) -> None:        
        super().tearDown()

class RemoveFilesTest(CommonSetupTestCase):
    
    def setUp(self):  
        self.ds = DistributionService() 
        super().setUp() 
               
    @patch('gitlab.v4.objects.Project')
    def test_remove_files_success(self, mock_project):
        mock_project.repository_tree.return_value = [{'path': 'f.txt'}]
        mock_project.commits.create.return_value = None

        ret = self.ds.remove_all_files(mock_project)

        self.assertTrue(ret)    
        mock_project.commits.create.assert_called_once()

    @patch('gitlab.v4.objects.Project')
    def test_remove_files_fail(self, mock_project):
        mock_project.repository_tree.return_value = [{'path': 'f2.txt'}]
        mock_project.commits.create.side_effect = gitlab.exceptions.GitlabCreateError

        ret = self.ds.remove_all_files(mock_project)

        self.assertTrue(isinstance(ret, gitlab.exceptions.GitlabCreateError))
        mock_project.commits.create.assert_called_once()


    def tearDown(self) -> None:
        super().tearDown()


class FeedbackDistributionTest(CommonSetupTestCase):

    def setUp(self):
        super().setUp()

        self.ds = DistributionService()

        now = timezone.now()
        yesterday = now - timezone.timedelta(days=1)
        the_day_before = now - timezone.timedelta(days=2)

        self.submission1 = Submissions.objects.create(
            id=2,
            assignment = self.asg,
            student = None,
            group = self.group1,
            submission_time = now,
            file_path = "/app/local_files/poject_gee_q1-main/README.md",
            grading_status = "Not Graded",
            total_points = None,
            feedback = None
        )
        self.submission1.save()
        self.submission2 = Submissions.objects.create(
            id=3,
            assignment = self.asg,
            student = None,
            group = self.group1,
            submission_time = yesterday,
            file_path = "/app/local_files/poject_gee_q1-main/README.md",
            grading_status = "Not Graded",
            total_points = None,
            feedback = None
        )
        self.submission2.save()
        self.submission3 = Submissions.objects.create(
            id=4,
            assignment = self.asg,
            student = None,
            group = self.group2,
            submission_time = the_day_before,
            file_path = "/app/local_files/poject_gee_q1-main/README.md",
            grading_status = "Not Graded",
            total_points = None,
            feedback = None
        )
        self.submission3.save()
        self.submission4 = Submissions.objects.create(
            id=5,
            assignment = self.indiv_asg,
            student = self.student1,
            group = None,
            submission_time = now + timezone.timedelta(days=1),
            file_path = "/app/local_files/poject_gee_q1-main/README.md",
            grading_status = "Not Graded",
            total_points = None,
            feedback = None
        )
        self.submission4.save()
        self.submission5 = Submissions.objects.create(
            id=6,
            assignment = self.indiv_asg,
            student = self.student1,
            group = None,
            submission_time = now - timezone.timedelta(days=2),
            file_path = "/app/local_files/poject_gee_q1-main/README.md",
            grading_status = "Not Graded",
            total_points = None,
            feedback = None
        )
        self.submission5.save()
        self.submission6 = Submissions.objects.create(
            id=7,
            assignment = self.indiv_asg,
            student = self.student1,
            group = None,
            submission_time = now - timezone.timedelta(days=3),
            file_path = "/app/local_files/poject_gee_q1-main/README.md",
            grading_status = "Not Graded",
            total_points = None,
            feedback = None
        )
        self.submission6.save()
        

    @patch("gitlabmanager.distribution_service.DistributionService.distribute_feedback_individual")
    def test_distribute_feedback_success_is_group(self, mock_distribute_feedback_individual):

        mock_distribute_feedback_individual.return_value = True
        ds = DistributionService()

        ret = ds.distribute_feedback(assignment_id=self.asg.id)

        expected_calls = [call(self.submission2, False), call(self.submission3, False)]
        
        self.assertEqual(mock_distribute_feedback_individual.call_args_list, expected_calls)
        self.assertEqual(ret, [])
    

    # @patch("gitlabmanager.distribution_service.DistributionService.distribute_feedback_individual")
    # def test_distribute_feedback_success_is_individual(self, mock_distribute_feedback_individual):
    #     mock_distribute_feedback_individual.return_value = True
    #     ds = DistributionService()

    #     ret = ds.distribute_feedback(assignment_id=self.indiv_asg.id)

    #     # Assume that distribute_feedback_individual should be called for submission4
    #     # and not for submission5 and submission6 since their submissiontime is before the current time.

    #     expected_calls = [call(self.submission4, False)]

    #     self.assertEqual(mock_distribute_feedback_individual.call_args_list, expected_calls)

   
    @patch("gitlabmanager.distribution_service.DistributionService.distribute_feedback_individual")
    def test_distribute_feedback_fail(self, mock_distribute_feedback_individual):

        def side_effect(submission, is_automatic_feedback=False):
            if submission == self.submission2:
                return False
            if submission == self.submission3:
                return True
            return True
        
        mock_distribute_feedback_individual.side_effect = side_effect

        ds = DistributionService()

        ret = ds.distribute_feedback(assignment_id=self.asg.id)

        expected_calls = [call(self.submission2, False), call(self.submission3, False)]

        self.assertEqual(mock_distribute_feedback_individual.call_args_list, expected_calls)
        self.assertEqual(ret, [self.submission2])


    def tearDown(self) -> None:
        super().tearDown()
