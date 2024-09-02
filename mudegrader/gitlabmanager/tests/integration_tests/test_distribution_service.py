# from operator import sub
# from venv import create
# from django.test import TestCase
# import gitlab.exceptions

# from gitlabmanager.repositoryCrud import GitlabManager
# from assignment_manager.models import Assignment, Course, Group, Student
# from unittest.mock import patch, MagicMock, call
# from django.utils import timezone
# from gitlabmanager.distribution_service import DistributionService
# import os

# from graderandfeedbacktool.models import Submissions
# from authentication.models import CustomUser, Role


# class CommonSetupTestCase(TestCase):
#     def setUp(self):
#         super().setUp()



#         self.gm = GitlabManager(mocked_gl=None)
#         self.gl = gitlab.Gitlab(url='https://gitlab.tudelft.nl/', private_token= os.getenv("GITLAB_PRIVATE_TOKEN"))
        
#         self.gl.auth()

#         if not self.gl.user:
#             raise Exception("Authentication failed")    
                
#         self.user = CustomUser.objects.create_user(
#             username='testuser',
#             password='testpassword',
#             role=Role.TEACHER
#         )
#         self.user.set_password('testpassword')
#         self.client.login(username='testuser', password='testpassword')
        
#         self.course = Course.objects.create(
#             id=1,
#             course_code="TEST0001",
#             description="TestCourse",
#             start_year=2021,
#             end_year=2022,
#             department="Computer Science",
#             created_by=self.user
#         )
#         self.course.save()
#         self.asg = Assignment.objects.create(
#             id=1,
#             course=self.course,
#             title="TestAssignment",
#             description="Test Assignment Description",
#             assignment_path="/app/local_files/assignments/Project_12/",
#             start_date=timezone.now(),
#             is_individual=False,
#             due_date=timezone.now(),
#             total_points=100,
#             gitlab_subgroup_id=None
#         )
#         self.indiv_asg = Assignment.objects.create(
#             id=2,
#             course=self.course,
#             title="TestAssignment",
#             description="Test Assignment Description",
#             assignment_path="/app/local_files/assignments/Project_12/",
#             start_date=timezone.now(),
#             is_individual=True,
#             due_date=timezone.now(),
#             total_points=100,
#             gitlab_subgroup_id=None
#         )
#         self.indiv_asg.save()

#         self.student1 = Student.objects.create(
#             first_name='asd',
#             last_name='Yusufk',
#             email='mohammedasd@example.com',
#             enrollment_year=2022,
#             program='Computer Science',
#             msc_track='Data Science',
#             self_assessed_skill='Python',
#             nationality_type='American',
#             start_year_in_mude=2023,
#             brightspace_id='MJs123',
#             gitlab_id='mohammedss_yusuf',
#             public_ssh_key='ssh-rssa AAAAB3NzaC1yc2EAAAADAQABAAAB...'
#         )
#         self.student1.save()

#         self.group1 = Group.objects.create(name="TestGroup1", assignment_id=self.asg, creation_date=timezone.now())
#         self.group2 = Group.objects.create(name="TestGroup2", assignment_id=self.asg, creation_date=timezone.now())
        
#         self.sub = Submissions.objects.create(
#             id=1,
#             assignment = self.asg,
#             student = None,
#             group = self.group1,
#             submission_time = timezone.now(),
#             file_path = "/app/local_files/poject_gee_q1-main/README.md",
#             grading_status = "Not Graded",
#             total_points = None,
#             feedback = None
#         )
        
#         self.sub.save()
#         self.asg.save()
#         self.group1.save()
#         self.group2.save()

#         # print("Subgroup id:", self.course.gitlab_subgroup_id)
#         self.gm.create_course_group(self.course)
#         # print("HERE Subgroup id:", self.course.gitlab_subgroup_id)
#         self.gm.create_assignment_group(self.asg)

#         self.gm.create_repo(self.group1)

#     def tearDown(self):
#         self.gm.remove_course_group(self.course)
#         # self.gm.remove_assignment_group(self.asg)
        
#         # self.course.delete()
#         self.asg.delete()
#         self.group1.delete()
#         self.group2.delete()

# class DistributionTests(CommonSetupTestCase):

#     def setUp(self):    
#         super().setUp() 

                
#     @patch('assignment_manager.models.Assignment.objects.get')
#     @patch('gitlab.v4.objects.GroupManager.get')
#     @patch('gitlab.v4.objects.ProjectManager.get')
#     @patch('os.walk')
#     @patch('builtins.open')
#     def test_distribute_assignment_success(self, mock_open, mock_os_walk, 
#     mock_get_project, mock_get_group, mock_get_assignment):

#         mock_assignment = MagicMock()
#         mock_assignment.id = 1
#         mock_assignment.gitlab_subgroup_id = 1
#         mock_assignment.assignment_path = "/fake/path"
#         mock_assignment.title = "Test Assignment"
#         mock_get_assignment.return_value = mock_assignment

#         mock_group = MagicMock()
#         mock_group.projects.list.return_value = [MagicMock(id=1), MagicMock(id=2)]
#         mock_get_group.return_value = mock_group

#         mock_project = MagicMock()
#         mock_get_project.return_value = mock_project

#         mock_os_walk.return_value = [("/fake/path", [], ["file.txt"])]

#         mock_file = MagicMock()
#         mock_file.read.return_value = "file content"
#         mock_open.return_value.__enter__.return_value = mock_file

#         ds = DistributionService()

#         failed_repositories = ds.distribute_assignment(1, None)

#         self.assertEqual(failed_repositories, [])
#         mock_get_assignment.assert_called_once_with(id=1)
#         mock_get_group.assert_called_once_with(1)
#         mock_get_project.assert_called()
    
#     @patch('gitlab.v4.objects.ProjectManager.get')
#     def test_distribute_assignment_failure(self, mock_get_project):


#         mock_assignment = MagicMock()
#         mock_assignment.id = 1
#         mock_assignment.gitlab_subgroup_id = 1
#         mock_assignment.assignment_path = "/fake/path"
#         mock_assignment.title = "Test Assignment"

#         mock_project = MagicMock()
#         mock_project.commits.create.side_effect = gitlab.exceptions.GitlabCreateError
#         mock_get_project.return_value = mock_project

#         ds = DistributionService()

#         failed_repositories = ds.distribute_assignment(1, [MagicMock()])

#         self.assertEqual(len(failed_repositories), 1)
#         mock_get_project.assert_called()
    
#     def tearDown(self) -> None:        
#         super().tearDown()


# class GatherAndCloneSubmissionTests(CommonSetupTestCase):

#     def setUp(self):    
#         super().setUp() 

                
#     @patch('gitlab.v4.objects.GroupManager.get')
#     @patch('gitlab.v4.objects.ProjectManager.list')
#     @patch('assignment_manager.models.Assignment.objects.get')
#     @patch('subprocess.run')
#     def test_gather_submissions_success(self, mock_subprocess_run, mock_get_assignment,
#                                         mock_list_projects, mock_get_group):

#         mock_assignment = MagicMock()
#         mock_assignment.id = 1
#         mock_assignment.gitlab_subgroup_id = 1
#         mock_get_assignment.return_value = mock_assignment

#         mock_group = MagicMock()
#         mock_group.projects.list.return_value = [MagicMock(id=58), MagicMock(id=61)]
#         mock_get_group.return_value = mock_group

#         mock_project = MagicMock()
#         mock_project.id = 58
#         mock_list_projects.return_value = [mock_project]

#         mock_subprocess_run.return_value = 0

#         ds = DistributionService()

#         ret = ds.gather_submissions(1, 1)

#         self.assertTrue(isinstance(ret, list))
#         self.assertEqual(ret[0].id, 58)
#         self.assertEqual(ret[1].id, 61)
#         self.assertEqual(len(ret), 2)

#     @patch('gitlab.v4.objects.GroupManager.get')
#     @patch('gitlab.v4.objects.ProjectManager.list')
#     @patch('assignment_manager.models.Assignment.objects.get')
#     @patch('subprocess.run')
#     def test_gather_submissions_assignment_non_existent(self, mock_subprocess_run,
#                                                         mock_get_assignment, mock_list_projects, mock_get_group):

#         mock_assignment = MagicMock()
#         mock_assignment.id = 1
#         mock_assignment.gitlab_subgroup_id = 1
#         mock_get_assignment.side_effect = Assignment.DoesNotExist

#         mock_group = MagicMock()
#         mock_group.projects.list.return_value = [MagicMock(id=58), MagicMock(id=61)]
#         mock_get_group.return_value = mock_group

#         mock_project = MagicMock()
#         mock_project.id = 58
#         mock_list_projects.return_value = [mock_project]

#         mock_subprocess_run.return_value = 0

#         ds = DistributionService()

#         ret = ds.gather_submissions(1, 1)

#         self.assertTrue(isinstance(ret, Assignment.DoesNotExist))
    

#     @patch('gitlab.v4.objects.GroupManager.get')
#     @patch('gitlab.v4.objects.ProjectManager.list')
#     @patch('assignment_manager.models.Assignment.objects.get')
#     @patch('subprocess.run')
#     def test_gather_submissions_gitlab_get_error(self, mock_subprocess_run,
#                                                         mock_get_assignment, mock_list_projects, mock_get_group):

#         mock_assignment = MagicMock()
#         mock_assignment.id = 1
#         mock_assignment.gitlab_subgroup_id = 1
#         mock_get_assignment.return_value = mock_assignment

#         mock_group = MagicMock()
#         mock_group.projects.list.side_effect = gitlab.exceptions.GitlabGetError
#         mock_get_group.return_value = mock_group

#         mock_project = MagicMock()
#         mock_project.id = 58
#         mock_list_projects.return_value = [mock_project]

#         mock_subprocess_run.return_value = 0

#         ds = DistributionService()

#         ret = ds.gather_submissions(1, 1)

#         self.assertTrue(isinstance(ret, gitlab.exceptions.GitlabGetError))
    
#     @patch('subprocess.run')
#     def test_clone_submissions_success(self, mock_subprocess_run):

#         mock_project = MagicMock()
#         mock_project.id = 58
#         mock_project.name_space = "testCourse/TestAsg/Group1"
#         mock_project.web_url = "https://gitlab.tudelft.nl/58"
        
#         ds = DistributionService()

#         ret = ds.clone_submissions([mock_project])

#         self.assertTrue(isinstance(ret, list))
#         self.assertEqual(ret, [])
#         mock_subprocess_run.assert_called_once()


#     @patch('subprocess.run')
#     def test_clone_submissions_failure(self, mock_subprocess_run):

#         mock_project = MagicMock()
#         mock_project.id = 58
#         mock_project.web_url = "https://gitlab.tudelft.nl/58"
#         mock_subprocess_run.side_effect = Exception
        
#         ds = DistributionService()

#         ret = ds.clone_submissions([mock_project])

#         self.assertTrue(isinstance(ret, list))
#         self.assertEqual(ret, [mock_project])
#         mock_subprocess_run.assert_called_once()


#     def tearDown(self) -> None:
#         super().tearDown()

# class RemoveFilesTest(CommonSetupTestCase):
    
#     def setUp(self):    
#         super().setUp() 

                
#     def test_remove_files_success(self):

#         mock_project = MagicMock()
#         mock_project.id = 58
#         mock_project.repository_tree.return_value = [MagicMock(id=1, path="file.txt")]
        
#         mock_project.commits.create.return_value = 0

#         ds = DistributionService()

#         ret = ds.remove_all_files(mock_project)

#         self.assertTrue(ret)
#         mock_project.commits.create.assert_called_once()


#     def test_remove_files_fail(self):

#         mock_project = MagicMock()
#         mock_project.id = 58
#         mock_project.repository_tree.return_value = [MagicMock(id=1, path="file.txt")]
        
#         mock_project.commits.create.side_effect = gitlab.exceptions.GitlabCreateError

#         ds = DistributionService()

#         ret = ds.remove_all_files(mock_project)

#         self.assertTrue(isinstance(ret, gitlab.exceptions.GitlabCreateError))
#         mock_project.commits.create.assert_called_once()
    
# class FeedbackDistributionTest(CommonSetupTestCase):

#     def setUp(self):
#         super().setUp()


#         now = timezone.now()
#         yesterday = now - timezone.timedelta(days=1)
#         the_day_before = now - timezone.timedelta(days=2)

#         self.submission1 = Submissions.objects.create(
#             id=2,
#             assignment = self.asg,
#             student = None,
#             group = self.group1,
#             submission_time = now,
#             file_path = "/app/local_files/poject_gee_q1-main/README.md",
#             grading_status = "Not Graded",
#             total_points = None,
#             feedback = None
#         )
#         self.submission1.save()
#         self.submission2 = Submissions.objects.create(
#             id=3,
#             assignment = self.asg,
#             student = None,
#             group = self.group1,
#             submission_time = yesterday,
#             file_path = "/app/local_files/poject_gee_q1-main/README.md",
#             grading_status = "Not Graded",
#             total_points = None,
#             feedback = None
#         )
#         self.submission2.save()
#         self.submission3 = Submissions.objects.create(
#             id=4,
#             assignment = self.asg,
#             student = None,
#             group = self.group2,
#             submission_time = the_day_before,
#             file_path = "/app/local_files/poject_gee_q1-main/README.md",
#             grading_status = "Not Graded",
#             total_points = None,
#             feedback = None
#         )
#         self.submission3.save()
#         self.submission4 = Submissions.objects.create(
#             id=5,
#             assignment = self.indiv_asg,
#             student = self.student1,
#             group = None,
#             submission_time = now + timezone.timedelta(days=1),
#             file_path = "/app/local_files/poject_gee_q1-main/README.md",
#             grading_status = "Not Graded",
#             total_points = None,
#             feedback = None
#         )
#         self.submission4.save()
#         self.submission5 = Submissions.objects.create(
#             id=6,
#             assignment = self.indiv_asg,
#             student = self.student1,
#             group = None,
#             submission_time = now - timezone.timedelta(days=2),
#             file_path = "/app/local_files/poject_gee_q1-main/README.md",
#             grading_status = "Not Graded",
#             total_points = None,
#             feedback = None
#         )
#         self.submission5.save()
#         self.submission6 = Submissions.objects.create(
#             id=7,
#             assignment = self.indiv_asg,
#             student = self.student1,
#             group = None,
#             submission_time = now - timezone.timedelta(days=3),
#             file_path = "/app/local_files/poject_gee_q1-main/README.md",
#             grading_status = "Not Graded",
#             total_points = None,
#             feedback = None
#         )
#         self.submission6.save()
        

#     # def test_distribute_feedback_individual(self):

#     #     ds = DistributionService()

#     #     # ret = ds.distribute_feedback_individual(project_id=None,submission=self.sub)

#     @patch("gitlabmanager.DistributionService.DistributionService.distribute_feedback_individual")
#     def test_distribute_feedback_success_is_group(self, mock_distribute_feedback_individual):

#         mock_distribute_feedback_individual.return_value = True
#         ds = DistributionService()

#         ret = ds.distribute_feedback(assignment_id=self.asg.id)

#         self.assertIn(call(self.submission2), mock_distribute_feedback_individual.call_args_list)
#         self.assertIn(call(self.submission3), mock_distribute_feedback_individual.call_args_list)

#         self.assertEqual(ret, [])

#     @patch("gitlabmanager.DistributionService.DistributionService.distribute_feedback_individual")
#     def test_distribute_feedback_success_is_individual(self, mock_distribute_feedback_individual):

#         mock_distribute_feedback_individual.return_value = True
#         ds = DistributionService()

#         ret = ds.distribute_feedback(assignment_id=self.indiv_asg.id)
#         # TODO: 
#         # self.assertIn(call(self.submission4), mock_distribute_feedback_individual.call_args_list)
#         # self.assertNotIn(call(self.submission5), mock_distribute_feedback_individual.call_args_list)
#         # self.assertNotIn(call(self.submission6), mock_distribute_feedback_individual.call_args_list)
#         self.assertEqual(ret, [])

#     @patch("gitlabmanager.DistributionService.DistributionService.distribute_feedback_individual")
#     def test_distribute_feedback_fail(self, mock_distribute_feedback_individual):


#         def side_effect(submission):
#             if submission == self.submission2:
#                 return False
#             if submission == self.submission3:
#                 return True
#             return True
        
#         mock_distribute_feedback_individual.side_effect = side_effect

#         ds = DistributionService()

#         ret = ds.distribute_feedback(assignment_id=self.asg.id)

#         self.assertIn(call(self.submission2), mock_distribute_feedback_individual.call_args_list)
#         self.assertIn(call(self.submission3), mock_distribute_feedback_individual.call_args_list)

#         self.assertEqual(ret, [self.submission2])

# #TODO move over to integration
# # class GatherSubmissionTests(CommonSetupTestCase):

# #     def setUp(self):    
# #         super().setUp() 

                

# #     def test_gather_submissions_(self):


# #         # assignment_subgroup = self.gl.groups.get(35603)
        
# #         ds = DistributionService()
# #         ret = ds.gather_submissions(1, 1)
        
# #         self.assertTrue(isinstance(ret, list))
# #         self.assertEqual(len(ret), 0)

# #         # ds.clone_submissions(ret)
# #     def tearDown(self) -> None:

# #         super().tearDown()