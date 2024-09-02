# from mailbox import Mailbox
# from django.test import TestCase
# import gitlab.exceptions
# import os

# from gitlabmanager.repositoryCrud import GitlabManager
# from assignment_manager.models import Assignment, Course, Group
# from unittest.mock import patch, MagicMock
# from django.utils import timezone
# from gitlab.v4.objects import Project, Group, GroupManager
# from authentication.models import CustomUser, Role



# class CommonSetupTestCase(TestCase):
#     def setUp(self):
#         super().setUp()
        
#         self.mocked_gl = MagicMock(spec=['groups'])
        

#         self.rest_manager = gitlab.base.RESTManager(gl=self.mocked_gl)

#         self.project = Project(self.rest_manager, {})
#         self.group = Group(self.rest_manager, {})
#         self.group_manager = GroupManager(gl=self.mocked_gl)

#         self.mocked_group_manager = MagicMock(spec = self.group_manager)
#         self.mocked_group = MagicMock(spec = self.group)
#         self.mocked_project = MagicMock(spec = self.project)

#         self.mocked_group.get_id.return_value = 1234

#         self.mocked_group_manager = MagicMock()
#         self.mocked_group_manager.create.return_value = self.mocked_group
        
#         self.mocked_gl.groups.return_value = self.mocked_group_manager


#         self.gm = GitlabManager(mocked_gl=None)
#         # gm.generate_sample_groups()  # Call generate_sample_groups in setUp method
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
#         self.asg = Assignment.objects.create(
#             course=self.course,
#             title="Test Assignment",
#             description="Test Assignment Description",
#             assignment_path="Test Path",
#             start_date=timezone.now(),
#             due_date=timezone.now(),
#             total_points=100
#         )
#         self.group1 = Group.objects.create(name="TestGroup1", assignment_id=self.asg, creation_date=timezone.now())
#         self.group2 = Group.objects.create(name="TestGroup2", assignment_id=self.asg, creation_date=timezone.now())
#         self.group1.save()
#         self.group2.save()
#         self.asg.save()
#         self.course.save()



# class CourseSubgroup(CommonSetupTestCase):

    
#     # @patch('gitlab.v4.objects.GroupManager.create')
#     # @patch('gitlab.v4.objects.GroupManager.get')
#     # def test_creation_success(self, mock_get, mock_create):


#     #     mock_create().return_value = self.mocked_group
#     #     self.mocked_group().get_id = 1
        
#     #     # if self.course.gitlab_subgroup_id is not None:
#     #     #     res = self.gm.remove_course_group(self.course)
#     #     #     self.assertEqual(res, 0)
#     #     breakpoint()
#     #     self.gm.createCourseGroup(self.course)
#     #     self.assertEqual(self.course.gitlab_subgroup_id, 12345)

#     @patch('gitlab.v4.objects.GroupManager.create')
#     def test_creation_success(self, mock_create):
#         # Mock the return value of the create method
#         mock_group = MagicMock()
#         mock_group.get_id.return_value = 12345
#         mock_create.return_value = mock_group

#         self.gm.create_course_group(self.course)
#         self.assertEqual(self.course.gitlab_subgroup_id, 12345)
        
#         retrieved_course = Course.objects.get(course_code=self.course.course_code)

#         self.assertEqual(retrieved_course.gitlab_subgroup_id, str(12345)) 
#         self.assertEqual(retrieved_course, self.course)       

#     @patch('gitlab.v4.objects.GroupManager.get')
#     @patch('gitlab.v4.objects.GroupManager.create')
#     def test_creation_failure(self, mock_create, mock_get):

#         def mock_get_side_effect(arg):
#             if arg == f"mude-project-x/{self.asg.course.course_code}":
#                 return MagicMock(get_id=lambda: 12345)
#             else:
#                 raise gitlab.exceptions.GitlabGetError

#         mock_create.side_effect = gitlab.exceptions.GitlabCreateError
#         mock_get.side_effect = mock_get_side_effect

#         ret = self.gm.create_course_group(self.course)
        
#         self.assertEqual(ret, 12345)
#         self.assertEqual(mock_get.call_count, 1) 
        
#         mock_get.assert_called_with(f"mude-project-x/{self.asg.course.course_code}")
#         mock_create.assert_called_once()


            
#     @patch('gitlab.v4.objects.GroupManager.create')
#     def test_group_non_existent(self, mock_create):
#         mock_create.side_effect = gitlab.exceptions.GitlabGetError
#         res = self.gm.create_course_group(self.course)
#         self.assertEqual(isinstance(res, gitlab.exceptions.GitlabGetError), True)
    
#     @patch('gitlab.v4.objects.GroupManager.delete')
#     def test_remove_course_group_success(self, mock_delete):
        
#         self.course.gitlab_subgroup_id = 12345
#         self.course.save()
        
#         mock_delete.return_value = 0

#         res = self.gm.remove_course_group(self.course)

#         querySet = Course.objects.filter(id=self.course.id)
#         self.assertEqual(querySet.count(), 0)
#         self.assertEqual(res, 0)
    
#     @patch('gitlab.v4.objects.GroupManager.delete')
#     def test_remove_course_group_fail(self, mock_delete):
        
#         self.course.gitlab_subgroup_id = 12345
#         self.course.save()
        
#         mock_delete.side_effect = gitlab.exceptions.GitlabDeleteError

#         res = self.gm.remove_course_group(self.course)

#         querySet = Course.objects.filter(id=self.course.id)
#         self.assertEqual(querySet.count(), 1)
#         self.assertTrue(isinstance(res, gitlab.exceptions.GitlabDeleteError))


# class AssignmentGroup(CommonSetupTestCase):

#     @patch('gitlab.v4.objects.GroupManager.create')
#     def test_creation_success(self, mock_create):

#         mock_group = MagicMock()
#         mock_group.get_id.return_value = 12345
#         mock_create.return_value = mock_group

#         self.course.gitlab_subgroup_id = "CEGM1000"
#         self.course.save()

#         self.gm.create_assignment_group(self.asg)
        
#         retrieved_asg = Assignment.objects.get(id=self.asg.id)

#         self.assertEqual(retrieved_asg.gitlab_subgroup_id, str(12345)) 
#         self.assertEqual(retrieved_asg, self.asg)
    
#     @patch('gitlab.v4.objects.GroupManager.get')
#     @patch('gitlab.v4.objects.GroupManager.create')
#     def test_creation_failure(self, mock_create, mock_get):
            
#             # Side effect is GitlabCreateError although expected to be GitlabGetError
#             # as the subgroup does not exist yet
#             mock_create.side_effect = gitlab.exceptions.GitlabCreateError
#             mock_get.return_value = MagicMock(get_id=lambda: 12345)

#             ret = self.gm.create_assignment_group(self.asg)
            
#             self.assertEqual(ret, "Course subgroup not found on Gitlab.")

#             self.asg.course.gitlab_subgroup_id = "1000"
#             self.asg.course.save()

#             ret = self.gm.create_assignment_group(self.asg)

#             retrieved_asg = Assignment.objects.get(id=self.asg.id)

#             mock_get.assert_called_once()
#             self.assertEqual(retrieved_asg.gitlab_subgroup_id, str(12345))
    
#     def test_creation_failure_no_course(self):

#         ret = self.gm.create_assignment_group(self.asg)
#         self.assertEqual(ret, "Course subgroup not found on Gitlab.")

    


# class RepositoryCreation(CommonSetupTestCase):

#     @patch('gitlabmanager.repositoryCrud.GitlabManager.create_repo')
#     @patch('gitlabmanager.repositoryCrud.GitlabManager.create_assignment_group')
#     @patch('gitlab.v4.objects.ProjectManager.create')
#     def test_creation_success(self, mock_create,
#                               mock_create_assignment_group,
#                               mock_create_repo,):

#         mock_project = MagicMock()
#         mock_create.return_value = mock_project
#         mock_create_assignment_group.return_value = [self.group1, self.group2]

#         self.asg.gitlab_subgroup_id = "1000"
#         self.asg.course.gitlab_subgroup_id = "CEGM1000"
#         self.asg.course.save()
#         self.asg.save()
        
#         self.gm.create_repositories(self.asg)

#         self.assertEqual(mock_create_repo.call_count, 2) 

#     @patch('gitlabmanager.repositoryCrud.GitlabManager.create_repo')
#     @patch('gitlabmanager.repositoryCrud.GitlabManager.create_assignment_group')
#     @patch('gitlab.v4.objects.ProjectManager.create')
#     def test_creation_failure_asg_group(self, mock_create,
#                              mock_create_assignment_group,
#                              mock_create_repo):

#         mock_create.side_effect = gitlab.exceptions.GitlabCreateError
#         mock_create_assignment_group.side_effect = gitlab.exceptions.GitlabCreateError

#         ret = self.gm.create_repositories(self.asg)

#         self.assertTrue(isinstance(ret, gitlab.exceptions.GitlabCreateError))
#         self.assertEqual(mock_create_repo.call_count, 0)

#     @patch('gitlab.v4.objects.ProjectManager.create')
#     def test_creation_failure_create_repo(self, mock_create):

#         mock_create.side_effect = gitlab.exceptions.GitlabCreateError

#         ret = self.gm.create_repo(self.group1)

#         self.assertTrue(isinstance(ret, gitlab.exceptions.GitlabCreateError))
#         self.assertEqual(mock_create.call_count, 1)


