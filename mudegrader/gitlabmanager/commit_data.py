import os
import gitlab
import logging
from assignment_manager.models import Group, Assignment, Student, Course, GroupRepo
from datetime import datetime

class GitlabHistoryManager:
    """
    Class that manages students and student groups gitlab commit history
    """
    def __init__(self, mock = None) -> None:
        self.logger = logging.getLogger("mudegrader.gitlabmanager")

        token = os.getenv("GITLAB_PRIVATE_TOKEN")
        if mock is None :
            self.gl = gitlab.Gitlab(url='https://gitlab.tudelft.nl/', private_token=token)
            self.gl.auth()
        else:
            self.gl = mock

    def get_project_commits(self, project_id):
        """
        Retrieves commit histor from a student group. Group as in group stored in database. 
            Typically a group has 5 people in it. They share assignments, which are repositories.

        :param group: an object reference for group, that is stored in db
        :type group: Group
        
        :returns: List of commit data, has author, commit id, date in it as a list.
        :rtype: list
        """
        commit_info_list = []

        try: 
            project = self.gl.projects.get(project_id)
            commits = project.commits.list(all=True)
            for commit in commits:
                datetime_str = commit.committed_date
                dt = datetime.fromisoformat(datetime_str)
                formatted_datetime = dt.strftime('%H:%M %d-%m-%Y')
                commit_info = {
                    'assignment_name': project.namespace['name'],
                    'title' : commit.title,
                    'commit_id': commit.id,
                    'short_id': commit.short_id,
                    'author_name': commit.author_name,
                    'committed_date': formatted_datetime,
                    'web_url' : commit.web_url
                }
                commit_info_list.append(commit_info)
            return commit_info_list
        except gitlab.exceptions.GitlabGetError as e:
            self.logger.exception(e)
            return commit_info_list

    def get_student_commit_from_project(self, student_gitlab_id, project_id):
        """
        Retrieves and formats commit information for a specific student within a given project.

        :param student_gitlab_id: The GitLab ID of the student whose commits are being retrieved.
        :param project_id: The ID of the project from which commits are being retrieved.
        :return: A list of dictionaries containing commit information. Each dictionary contains:
            - project_name: The name of the project.
            - title: The title of the commit.
            - commit_id: The full ID of the commit.
            - short_id: The short ID of the commit.
            - author_name: The name of the author of the commit.
            - committed_date: The date and time the commit was made, formatted as 'HH:MM DD-MM-YYYY'.
            - web_url: The URL to view the commit in the GitLab web interface.
        """
        commit_info_list = []
        try:
            user = self.gl.users.get(student_gitlab_id)
            project = self.gl.projects.get(project_id)
            commits = project.commits.list(all=True)
            student_commits = [commit for commit in commits if commit.author_name == user.name]
            for commit in student_commits:
                datetime_str = commit.committed_date
                dt = datetime.fromisoformat(datetime_str)
                formatted_datetime = dt.strftime('%H:%M %d-%m-%Y')
                commit_info = {
                    'project_name': project.name,
                    'title' : commit.title,
                    'commit_id': commit.id,
                    'short_id': commit.short_id,
                    'author_name': commit.author_name,
                    'committed_date': formatted_datetime,
                    'web_url' : commit.web_url
                }
                commit_info_list.append(commit_info)
            return commit_info_list
        except gitlab.exceptions.GitlabGetError as e:
            self.logger.exception(e)
            return commit_info_list
