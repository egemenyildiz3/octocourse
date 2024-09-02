import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from gitlab import GitlabGetError
from gitlabmanager.commit_data import GitlabHistoryManager

class TestGitlabHistoryManager(unittest.TestCase):

    def setUp(self):
        self.logger = MagicMock()
        self.mock_gl = MagicMock()
        self.manager = GitlabHistoryManager(mock=self.mock_gl)
        self.manager.logger = self.logger

    def test_get_student_commit_from_project(self):
        # Mock data
        student_gitlab_id = 1
        project_id = 1

        user = MagicMock()
        user.name = "Student Name"
        self.mock_gl.users.get.return_value = user

        project = MagicMock()
        project.name = "Test Project"
        commit = MagicMock()
        commit.author_name = "Student Name"
        commit.committed_date = '2024-06-06T17:05:52.000+02:00'
        commit.title = "Test Commit"
        commit.id = "12345"
        commit.short_id = "123"
        commit.web_url = "http://example.com"
        project.commits.list.return_value = [commit]
        self.mock_gl.projects.get.return_value = project

        expected_commit_info = [{
            'project_name': "Test Project",
            'title': "Test Commit",
            'commit_id': "12345",
            'short_id': "123",
            'author_name': "Student Name",
            'committed_date': datetime.fromisoformat('2024-06-06T17:05:52.000+02:00').strftime('%H:%M %d-%m-%Y'),
            'web_url': "http://example.com"
        }]

        result = self.manager.get_student_commit_from_project(student_gitlab_id, project_id)

        self.assertEqual(result, expected_commit_info)
        self.mock_gl.users.get.assert_called_once_with(student_gitlab_id)
        self.mock_gl.projects.get.assert_called_once_with(project_id)
        project.commits.list.assert_called_once_with(all=True)

    def test_get_student_commit_from_project_gitlab_get_error(self):
        # Mock data
        student_gitlab_id = 1
        project_id = 1

        self.mock_gl.users.get.side_effect = GitlabGetError

        result = self.manager.get_student_commit_from_project(student_gitlab_id, project_id)

        self.assertEqual(result, [])
        self.logger.exception.assert_called_once()

if __name__ == '__main__':
    unittest.main()
