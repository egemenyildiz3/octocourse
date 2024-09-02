import gitlab.exceptions
import gitlab.v4
import gitlab.v4.objects
from django.conf import settings

from gitlabmanager.repositoryCrud import GitlabManager
import logging
import os
import gitlab
from assignment_manager.models import Assignment, Course, Group, GroupMember, GroupRepo, Student, StudentRepo, GroupRepo
from graderandfeedbacktool.models import Submissions
import base64
import datetime
import subprocess
from django.db.models import Subquery, OuterRef, F
from django.db.models import Max, Min
import tempfile
import requests
import tarfile
from django.shortcuts import get_object_or_404
from graderandfeedbacktool.populations import populate_database_for_one_assignment

class DistributionService:
    """
    This class manages the distribution of assignments to student repositories. The gathering of submissions
    and the distribution of feedback is handled by this class as well. The GitLab API is used to interact
    with the GitLab instance. DistributionService is used by the Celery task scheduler to distribute assignments and feedback
    at regular intervals. DistributionService is also used by the Django views to distribute assignments and feedback on demand.
    
    """

    def __init__(self):
        """
        Initialize the DistributionService class.

        :param logger: Logger with namespace "mudegrader.gitlabmanager".
        :type logger: logging.Logger
        :param global_group_id: Global group ID for the Mude-X test environment on the TU central gitlab.
        :type global_group_id: int
        :param gm: GitLabManager object.
        :type gm: GitlabManager
        :param gl: GitLab connection object.
        :type gl: gitlab.Gitlab

        """
        logger_namepace = os.getenv("LOGGER_NAMESPACE")
        self.logger = logging.getLogger(logger_namepace)
        self.global_group_id = os.getenv("GLOBAL_GROUP_ID")
        token = os.getenv("GITLAB_PRIVATE_TOKEN")
        self.gm = GitlabManager()
        self.gl = gitlab.Gitlab(url='https://gitlab.tudelft.nl/', private_token=token)
        self.gl.auth()

    
    def gather_submissions(self, course_id, assignment_gitlab_id, course_path_name, assignment_title):
        """
        Gather all submissions for a given assignment.
        If the folder to clone the assignments does not exist yet
        (first gathering of submissions) it should be created.

        :param course_id: The ID of the course.
        :type course_id: int
        :param assignment_gitlab_id: The gitlab ID of the assignment.
        :type assignment_gitlab_id: int
        :param course_path_name: Path name of the head course
        :param assignment_title: Name of the assignment

        :return: A list of repositories containing the submissions.
        :rtype: list
        """
        try:
            assignment_subgroup = self.gl.groups.get(assignment_gitlab_id)

        except Exception as e:
            self.logger.error(f"Assignment {assignment_title} not found or gitlab id of the assignment is wrong!")
            return e

        try:
            assignment = get_object_or_404(Assignment, course__id=course_id, title=assignment_title)
            submissions_path = assignment.submission_path_in_filesystem
            os.makedirs(submissions_path, exist_ok=True)
            repository_list = assignment_subgroup.projects.list(all=True)
            return repository_list
        
        except Exception as e:
            self.logger.error(f"Error gathering submissions for assignment {assignment_title}. \n\n {e}")
            return e


    def clone_submissions(self, repository_list, course_id, assignment_title):
        """
        Clone all repositories in the prepared repository list.

        :param repository_list: A list of repositories to clone.
        :type repository_list: list
        :param course_id: The ID of the course.
        :type course_id: int
        :param assignment_title: The title of the assignment.
        :type assignment_title: str

        :return: list of failed repositories
        :rtype: list
        """
        assignment = get_object_or_404(Assignment, course__id=course_id, title=assignment_title)
        submissions_path = assignment.submission_path_in_filesystem
        failed_repositories = []

        for repository in repository_list:
            gname = repository.name
            access_token = os.getenv("GITLAB_PRIVATE_TOKEN")
            fpath = os.path.join(submissions_path, gname)

            tmp_file = None 
            try:
                self.logger.info(f"Cloning repository: {repository.name}")

                archive_url = f"{repository.web_url}/-/archive/main/{repository.path}-main.tar.gz"
                headers = {'PRIVATE-TOKEN': os.getenv("GITLAB_PRIVATE_TOKEN")}

                os.makedirs(fpath, exist_ok=True)

                with requests.get(archive_url, headers=headers, stream=True) as r:
                    r.raise_for_status()
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(r.content)
                        tmp_file.flush()
                        with tarfile.open(tmp_file.name, 'r:gz') as tar:
                            tar.extractall(path=fpath)
                self.logger.info(f"Successfully cloned repository: {repository.name}")
            except Exception as e:
                self.logger.warning(f"Error cloning repository {repository.name}: {e}")
                self.logger.error(f"Error cloning repository {repository.name_with_namespace}. {e}")
                failed_repositories.append({'name': repository.name, 'url': repository.web_url})
            finally:
                if tmp_file:
                    try:
                        os.remove(tmp_file.name)
                    except Exception as e:
                        self.logger.warning(f"Error cleaning up temp file: {e}")
                        self.logger.error(f"Error cleaning up temp file: {e}")

        self.logger.info("Finished cloning all repositories, starting database population...")
        # Populate database for each student or group after cloning all repositories
        try:
            ass_id = assignment.id

            if assignment.is_individual:
                self.logger.info(f"Assignment is individual, populating database for students...")
                students = Student.objects.filter(courses_enrolled__id=course_id)
                for student in students:
                    self.logger.info(f"-> -> Populating Submissions database for student ID: {student.id}")
                    populate_database_for_one_assignment(ass_id, stu_id=student.id, grp_id=None)
            else:
                self.logger.info(f"Assignment is group-based, populating database for groups...")
                groups = Group.objects.filter(course__id=course_id, assignments__id=ass_id)
                self.logger.info(f"groups found for this course : {groups}")
                for group in groups:
                    self.logger.info(f" -> -> Populating Submissions database for group ID: {group.id}")
                    populate_database_for_one_assignment(ass_id, stu_id=None, grp_id=group.id)
        except Exception as e:
            self.logger.warning(f"Error populating database for assignment {assignment_title}: {e}")
            self.logger.error(f"Error populating database for assignment {assignment_title}. {e}")

        self.logger.info("Database population completed.")
        return failed_repositories


        
    def distribute_assignment(self, asg, repo_list):
        """
        Distribute an assignment to created groups for a given assignment. When
        group_list is None, the assignment is distributed to all groups in the assignment's subgroup.

        the method returns a list of repositories that failed to distribute the assignment.
        the route we will take after that point should be planned out.
        in the case that the problem was a network issue, another call to the same repositories
        would prove useful, although when the issue is with the state of the git repo, we should
        consider a different approach.

        :param asg: The assignment object.
        :type asg: Assignment
        :param repo_list: The repository list to distribute the assignment to. if None, all repositories in the assignment's subgroup are distributed to.
        :type repo_list: list of gitlab repositories

        :return: True if the assignment was distributed successfully, False otherwise.
        :rtype: bool

        """

        base_path = asg.path_in_filesystem
        
        assignment_subgroup = self.gl.groups.get(asg.gitlab_subgroup_id)

        if repo_list is None:
            repository_list = assignment_subgroup.projects.list(get_all=True)
        else:
            repository_list = repo_list

        failed_repositories = []

        for repository in repository_list:
            try:
                project = self.gl.projects.get(repository)
            except gitlab.exceptions.GitlabGetError as e:
                self.logger.error(f"Error fetching project {repository}: {e}")
                failed_repositories.append(repository)
                continue

            actions = []

            for (dir_path, dir_names, files) in os.walk(base_path):

                if 'hidden' in dir_names:
                    dir_names.remove('hidden')

                for file in files:
                    relative_path = os.path.relpath(dir_path, base_path)
                    file_path = os.path.join(dir_path, file)
                    
                    item = {
                        'action': 'create',
                        'file_path': os.path.join(relative_path, file).replace("\\", "/"),
                    }

                    if file_path.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.exe')):
                        with open(file_path, "rb") as file:
                            content = file.read()
                            encoded_file = base64.b64encode(content).decode("utf-8")
                            item['content'] = encoded_file
                            item['encoding'] = 'base64'
                    else:
                        with open(file_path, "r", encoding='utf-8') as file:
                            content = file.read()
                            item['content'] = content
                            item['encoding'] = 'text'

                    actions.append(item)

            payload = {
                'branch': 'main',
                'commit_message': f'Assignment Distribution {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'actions': actions,
            }

            try:
                project.commits.create(payload)
                self.logger.info(f"Assignment {asg.title} distributed successfully.")
            except gitlab.exceptions.GitlabCreateError as e:
                self.logger.error(f"Error distributing assignment {asg.title}. Error: {e}")
                failed_repositories.append(repository)
                continue

        return failed_repositories
   
    def distribute_feedback_individual(self, submission: Submissions, is_automatic_feedback=False):
        """
        Distribute feedback to a given assignment.

        :param assignment_id: The ID of the assignment.
        :type assignment_id: int
        :param group_list: The repository list to distribute the feedback to.
        :type group_list:self, submission: Submissions list

        :return: True if the feedback was distributed successfully, False otherwise.
        :rtype: bool

        """
        asg = submission.assignment
        student = submission.student
        group = submission.group
        repo = None

        if asg.is_individual:
            if student:
                student_repo = get_object_or_404(StudentRepo, student=student, assignment=asg)
                repo = self.gl.projects.get(student_repo.repository_id)
            else:
                self.logger.error(f"No student associated with submission {submission.id}")
                return False
        else:
            if group:
                group_repo = get_object_or_404(GroupRepo, group=group, assignment=asg)
                repo = self.gl.projects.get(group_repo.repository_id)
            else:
                self.logger.error(f"No group associated with submission {submission.id}")
                return False

        if not repo:
            self.logger.error(f"No repository found for {group.name if group else 'unknown'}")
            return False

        # Check if file exists before pushing

        dir_path = '/app/project_files/feedback/1/sefakoybir/student_feedback/student_feedback/1/'
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            files = os.listdir(dir_path)
            logging.info("Files at %s:", dir_path)
            for file in files:
                logging.info(file)
        else:
            logging.error("Directory does not exist: %s", dir_path)

        self.logger.info(f"File path: {submission.file_path}")
        if not os.path.exists(submission.file_path):
            self.logger.error(f"File does not exist: {submission.file_path}")
            return False

        res = self.push_file_to_repository(repo, submission.file_path, is_automatic_feedback=is_automatic_feedback)
        
        if res:
            self.logger.info(f"Feedback for {repo.name} distributed successfully.")
            return True
        else:
            self.logger.error(f"Error distributing feedback for {repo.name}.")
            return False
        

    def distribute_feedback(self, assignment_id, is_automatic_feedback=False):
        """
        Distribute feedback to a given assignment. The feedback is distributed to the 
        latest submission of each student.

        :param assignment_id: The ID of the assignment.
        :type assignment_id: int

        :return: The list of failed feedback distributions for the assignment.
        :rtype: list

        """

        asg = Assignment.objects.get(id=assignment_id)
        submissions = []
        if asg.is_individual:
            students = Student.objects.filter(courses_enrolled=asg.course_id)

            for student in students:
                latest_sub = Submissions.objects.filter( assignment_id=assignment_id, 
                                                        student_id=student.id).latest('submission_time')
                submissions.append(latest_sub)
        else:

            groups = Group.objects.filter(course_id=asg.course_id)
            for group in groups:
                latest_sub = Submissions.objects.filter( assignment_id=assignment_id, 
                                                        group=group.id).latest('submission_time')
                submissions.append(latest_sub)
        failed_feedback = []

        for submission in submissions:
            ret = self.distribute_feedback_individual(submission, is_automatic_feedback)
            if not ret:
                failed_feedback.append(submission)

        return failed_feedback
    

    def push_file_to_repository(self, repo, file_path, is_automatic_feedback=False):
        """
        Push a file to a given repository.

        :param repo: The repository to push the file to.
        :type repo: gitlab.v4.objects.Project

        :param file_path: The path to the file to push.
        :type file_path: str

        :return: True if the file was pushed successfully, False otherwise.
        :rtype: bool
        """

        try:
            feedback_path = settings.FEEDBACK_ROOT

            # Construct the full path to the feedback file
            full_file_path = os.path.join(feedback_path, file_path)
            file_name = os.path.basename(file_path)
            
            self.logger.info(f"Full file path: {full_file_path}")
            self.logger.info(f"FEEDBACK PATH: {feedback_path}")

            if not os.path.exists(full_file_path):
                self.logger.error(f"File does not exist: {full_file_path}")
                return False

            with open(full_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            repo_relative_path = file_name


            self.logger.info(f"Automatic feedback: {is_automatic_feedback}")

            if is_automatic_feedback:
                repo_relative_path = f"automated-feedback/{repo_relative_path}"

            try:
                repo.files.get(file_path=repo_relative_path, ref='main')
                action = 'update'
                self.logger.info(f"File exists in repository. Action set to 'update'.")

            except gitlab.exceptions.GitlabGetError:
                action = 'create'
                self.logger.warning(f"File does not exist in repository. Action set to 'create'.")

            commit_data = {
                'branch': 'main',
                'commit_message': 'Feedback update',
                'actions': [
                    {
                        'action': action,
                        'file_path': repo_relative_path,  # Ensure this path is at the root level
                        'content': content,
                    }
                ]
            }

            self.logger.info(f"Commit data: {commit_data}")

            repo.commits.create(commit_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to push file to repository {file_name}: {e}")
            return False

    def remove_all_files(self, project):
        """
        Delete a commit from a project.

        :param project: The project to delete the files from.
        :type project: gitlab.v4.objects.Project

        :return: True if the commit was deleted successfully, False otherwise.
        :rtype: bool
        """

        file_tree = project.repository_tree(ref='main')

        actions = []

        for file in file_tree:
            
            item = {
                'action': 'delete',
                'file_path': file.get('path'),
            }
            actions.append(item)
                          
        payload = {
            'branch': 'main',
            'commit_message': f'Assignment Deletion {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',                
            'actions': actions,
        }

        try:
            project.commits.create(payload)
            self.logger.info(f"Assignment {project.name_with_namespace} distributed successfully.")
            return True

        except gitlab.exceptions.GitlabCreateError as e:

            self.logger.error(f"Error distributing assignment {project.name_with_namespace}.")
            return e

