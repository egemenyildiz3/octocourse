from typing import Optional

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from assignment_manager.models import Group as AssignmentManagerGroup, Assignment, Student, GroupMember, Group
from .repositoryCrud import GitlabManager
from graderandfeedbacktool.models import SubmissionUnits, Submissions, TaskGrades
from django.conf import settings
import os
import gitlab
import logging
import random
import math


class GitlabManagerStudent:
    def __init__(self, mock_object = None):
        """
        Initializes the GitLabManager with a GitLab connection.

        :param mock_object: An optional mock object for the GitLab connection, used for testing.

        :return: None
        """

        #: Logger with namespace "mudegrader.gitlabmanager".
        self.logger = logging.getLogger("mudegrader.gitlabmanager")

        token = os.getenv("GITLAB_PRIVATE_TOKEN")

        #: GitLab connection object.
        if mock_object is None :
            self.gl = gitlab.Gitlab(url='https://gitlab.tudelft.nl/', private_token=token)
            self.gl.auth()
        else:
            self.gl = mock_object

    def add_user_to_gitlab_group(self, gitlab_user_id, gitlab_group_id, access_level):
        """
        Adds a user to a GitLab group. This method is used to add students or teachers to a 
        GitLab group. For example, adding a teacher as a maintainer to a course's group.

        :param gitlab_user_id: The ID of the GitLab user.
        :param gitlab_group_id: The ID of the GitLab group.
        :param access_level: The access level to grant to the user in the group.

        :return: None. Raises an exception if the user could not be added.
        """
        try:

            if gitlab_user_id is None or not isinstance(gitlab_user_id, int) or gitlab_user_id == -1:
                self.logger.error("User not found")
                raise ValueError("User did not have Gitlab ID or ID was invalid")
            group = self.gl.groups.get(gitlab_group_id)
            group.members.create({'user_id': gitlab_user_id, 'access_level': access_level})

        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.warning(f"Member with {gitlab_user_id} already in gitlab group!")
            raise e

    def add_student_to_gitlab_group(self, student_id, gitlab_subgroup_id, access_level = gitlab.const.AccessLevel.DEVELOPER):
        """
        Adds a student to an existing group in GitLab.

        Parameters
        ----------
        student_id : int
            The ID of the student in db.
        gitlab_subgroup_id : int
            The ID of the GitLab subgroup.

        Returns
        ----------
        None
        """
        gitlab_student_id = self.get_student_gitlab_id(student_id)
        self.add_user_to_gitlab_group(gitlab_student_id, gitlab_subgroup_id, access_level)
        # try:
        #     if isinstance(gitlab_student_id, int):
        #         group = self.gl.groups.get(gitlab_subgroup_id)
        #         group.members.create({'user_id': gitlab_student_id, 'access_level': access_level})
        #     else:
        #         self.logger("Error while adding student to a gitlab group: Student does not have proper gitlab id")

    def remove_student_from_gitlab_group(self, student_id, gitlab_subgroup_id):
        """
        Removes a student from an existing group in GitLab.

        Parameters
        ----------
        student_id : int
            The ID of the student in db.
        gitlab_subgroup_id : int
            The ID of the GitLab subgroup.

        Returns
        ----------
        None
        """
        try:
            gitlab_student_id = self.get_student_gitlab_id(student_id)
            group = self.gl.groups.get(gitlab_subgroup_id)
            group.members.delete(gitlab_student_id)
        except gitlab.exceptions.GitlabDeleteError as e:
            self.logger.warning("Could not remove student from group!")

    def divide_students_into_groups(self, list_of_student_ids, group_size):
        """
        Divides a list of students into groups of a specified size.

        Parameters
        ----------
        list_of_student_ids : list
            A list of student IDs from database.
        group_size : int
            The size of each group.

        Returns
        ----------
        grouped_students : list of lists
            A list of groups, each containing student IDs.
        """
        is_divisible = True
        rest = len(list_of_student_ids) % group_size
        if rest > 0:
            is_divisible = False
            self.logger.info("Number of students is not divisible by groupSize")

        random.shuffle(list_of_student_ids)
        num_of_groups = math.floor(len(list_of_student_ids) / group_size)
        if not is_divisible:
            num_of_groups += 1

        grouped_students = [list_of_student_ids[i * group_size:(i + 1) * group_size] for i in range(num_of_groups)]
        return grouped_students

    def add_student_groups_to_database(self, grouped_students, assignment):
        """
        Divide a list of students into groups of a specified size.

        Parameters
        ----------
        grouped_students : list of lists
            A list of groups, each containing student IDs.

        assignment_id: int
            id of the assignment these groups need to be assigned

        Returns
        ----------
        None
        """
        with transaction.atomic():
            
            for group in grouped_students:
                # todo: getting a course like this is not perfect, we probably should get it as a param
                course = assignment.course
                # Create a new group
                group_name = f"{assignment.title} Group_{grouped_students.index(group) + 1}"
                group_obj = AssignmentManagerGroup.objects.create(
                    name=group_name,
                    course=course,
                )
                group_obj.assignments.add(assignment)
                
                # Add students to the group
                for student_id in group:
                    student = Student.objects.get(id=student_id)
                    GroupMember.objects.create(
                        student_id=student,
                        group_id=group_obj
                    )

    def create_repositories_and_add_students(self, grouped_students, assignment_id):
        """
        Create repositories for each group and add students to them.

        Parameters
        ----------
        grouped_students : list of lists
            A list of groups, each containing student IDs.
        group_id : int
            The assignment/subgroup that the repositories will be created into.

        Returns
        ----------
            None
        """
        try:
            gm = GitlabManager()
            assignment = Assignment.objects.get(id = assignment_id)
            repo_id_list = gm.create_repositories(assignment) #it should have repo ids
            
            repo_index = 0
            for repo_id in repo_id_list:
                for student_id in grouped_students[repo_index]:
                    self.add_student_to_repo(student_id, repo_id)


        except gitlab.exceptions.GitlabGetError as e:
            self.logger.exception(e)
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.exception(e)

    def add_student_to_repo(self, student_gitlab_id, project_id, student_email, access_level=gitlab.const.AccessLevel.DEVELOPER):
        """
        Add a student to a repository with the developer role.

        Parameters
        ----------
        student_gitlab_id : (int)
            The ID of the student in gitlab.
        project_id : (int)
            The gitlab ID of the repository.
        
        Returns
        ----------
            None
        """
        try:
            project = self.gl.projects.get(project_id)
             # the method returns -1 if in db student_gitlab_id doesnt exist
            if not isinstance(int(student_gitlab_id), int):
                raise ValueError(f"student_gitlab_id is not an integer: actual type: {type(student_gitlab_id)}, actual value: {student_gitlab_id}")
            if int(student_gitlab_id) != -1:
                project.members.create({'user_id': student_gitlab_id, 'access_level': access_level})
                self.logger.info(f"Added student with gitlab id:{student_gitlab_id} to repo with id:{project_id}")
            else:
                self.add_student_to_repo_without_git_account(student_email, project_id)
                self.logger.info(f"Added student with repo   with id:{project_id} using their email: {student_email}")

        except gitlab.exceptions.GitlabGetError as e:
            self.logger.exception(f"Failed to get project: {e}")
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.exception(f"Failed to add member to project: {e}")
        except Exception as e:
            raise e

    def add_student_to_repo_without_git_account(self, email, project_id):
        """
        Invite a student to a GitLab project by email.

        Parameters
        ----------
            email : (str)
                The email address of the student.
            project_id : (int)
                The ID of the project (repo).

        Returns
        ----------
            None
        """
        try:
            access_level = gitlab.const.AccessLevel.DEVELOPER #adds as a developer rank
            # Retrieve the project
            project = self.gl.projects.get(project_id)

            # Invite the user to the project by email
            project.invitations.create({
                'email': email,
                'access_level': access_level
            })

        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.exception(f"Failed to invite user: {e}")

    def student_exists_in_repo(self, project_id, student_gitlab_id):
        """
        Check if a member with the given email exists in a GitLab project.

        Parameters
        ----------
            project_id : (int)
                The ID of the GitLab project.
            student_gitlab_id : (str)
                The gitlab_id of the member to check.

        Returns
        ----------
            bool: True if the member exists in the project, False otherwise.
        """
        try:
            project = self.gl.projects.get(project_id)
            members = project.members.list(all=True)
            for member in members:
                if int(member.id) == int(student_gitlab_id):
                    return True

            return False
        except gitlab.exceptions.GitlabGetError:
            self.logger.exception(f"Error: Project with ID {project_id} not found.")
            return False
        except Exception as e:
            self.logger.exception(f"Error: {str(e)}")
            return False

    def remove_student_from_repo(self, student_id, project_id):
        """
        Remove a student from a repository.

        Parameters
        ----------
            student_id (int): The ID of the student in database.
            project_id (int): The ID of the repository.

        Returns
        ----------
           None
        """
        try:
            student_gitlab_id = self.get_student_gitlab_id(student_id)
            if(self.student_exists_in_repo(project_id, student_gitlab_id)):
                project = self.gl.projects.get(project_id)
                member = project.members.get(student_gitlab_id)
                member.delete()
            else:
                self.logger.info(f"The user: {student_id} does not exist in repo: {project_id}")
        except gitlab.exceptions.GitlabGetError as e:
            self.logger.exception(f"Failed to get project: {e}")
        except gitlab.exceptions.GitlabDeleteError as e:
            self.logger.exception(f"Failed to remove member from project: {e}")

    def update_student_access_level(self, student_id, project_id, new_role):
        """
        Update the role of a student in a specific group.

        Parameters
        ----------
            student_id (int): The ID of the student in database.
            project_id (int): The ID of the project in gitlab.
            new_role (int): The new role (access level) for the student.

        Returns
        ----------
            None
        """
        try:
            project = self.gl.projects.get(project_id)
            student_gitlab_id = self.get_student_gitlab_id(student_id)
            member = project.members.get(user_id=student_gitlab_id)

            # Update the member's access level
            member.access_level = new_role
            member.save()

        except gitlab.exceptions.GitlabGetError as e:
            self.logger.exception(f"Failed to retrieve group or member: {e}")

        except gitlab.exceptions.GitlabUpdateError as e:
            self.logger.exception(f"Failed to update member role: {e}")

    @staticmethod
    def create_submission_for_assignment(assignment_id, student_id=None, group_id=None):
        """
        Create a submission, submission units, and task grades for a specific assignment and student or group.

        Args:
        - assignment_id (int): The ID of the assignment.
        - student_id (int, optional): The ID of the student. Default is None.
        - group_id (int, optional): The ID of the group. Default is None.

        Returns:
        - submission (Submissions): The created submission object.
        """
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        student = get_object_or_404(Student, pk=student_id) if student_id else None
        group = get_object_or_404(Group, pk=group_id) if group_id else None

        # Create the submission
        submission = Submissions.objects.create(
            assignment=assignment,
            student=student,
            group=group,
            file_path='',  # Default file path, can be updated later
            grading_status='Not Graded',
            feedback=''
        )
        

        # path to the submission units
        try:
            submission_unit_path = os.path.join(assignment.submission_path_in_filesystem, "students_submissions", "demo-fails1.ipynb")
            print("SUBMISSION FILE FOUND")
        except FileNotFoundError:
            print("FileNotFoundError: One of the directories or the file doesn't exist.")

        # Create submission units and task grades
        for unit in assignment.assignmentunit_set.all():
            submission_unit = SubmissionUnits.objects.create(
                submission=submission,
                assignment_unit=unit,
                file_path=submission_unit_path, 
                grading_status='Not Graded',
                feedback=''
            )

            for task in unit.tasks_set.all():
                TaskGrades.objects.create(
                    task=task,
                    submission_unit=submission_unit,
                    points_received=0,  # Initial points, can be updated later
                    graded_by_teacher_id=None,
                    date_graded=timezone.now(),
                    grading_type='Initial'
                )

        return submission

    def get_student_gitlab_id(self, student_id):
        """
        Retrieve the GitLab ID of a student.

        Parameters
        ----------
        student_id : int
            The ID of the student.

        Returns
        -------
        int or -1
            The GitLab ID of the student, or -1 if the student does not have a GitLab ID.
            The -1 is later used to send email to student if they dont have gitlab id.

        Raises
        ------
        DoesNotExist
            If the student with the given ID does not exist in the database.
        """
        student = Student.objects.get(id=student_id)
        if(student.gitlab_id == "" or student.gitlab_id is None):
            self.logger.error("Student does not have a gitlab id")
            return -1
        try:

            return int(student.gitlab_id)
        except ValueError as e:
            self.logger.exception(e)
            return -1
    

    def create_and_return_repo_id(self, assignment_gitlab_id, group_name):
        """
        Creates a repo for a student group under a given assignment in GitLab with the specified GitLab ID,
        and creates an initial commit to set up the main branch.

        :param assignment_gitlab_id: GitLab ID of the assignment
        :param group_name: Name of the group that will be created in GitLab
        :return: The ID of the created repository
        """
        try:
            project = self.gl.projects.create({'name': group_name, 'namespace_id': assignment_gitlab_id})
            self.logger.info(f"Repository for group {group_name} created successfully.")
            
            # Create an initial commit to set up the main branch
            initial_commit_data = {
                'branch': 'main',
                'commit_message': 'Initial commit',
                'actions': [
                    {
                        'action': 'create',
                        'file_path': 'README.md',
                        'content': '# Initial commit\n\nThis is the initial commit for the repository.'
                    }
                ]
            }
            project.commits.create(initial_commit_data)
            self.logger.info(f"Initial commit for group {group_name} created successfully.")
            
            # Unprotect the main branch by setting protection settings
            project.protectedbranches.create({
                'name': 'main',
                'allow_force_push': True,
                'push_access_level': gitlab.const.DEVELOPER_ACCESS,
                'merge_access_level': gitlab.const.DEVELOPER_ACCESS,
                'unprotect_access_level': gitlab.const.MAINTAINER_ACCESS,
            })
            self.logger.info(f"Main branch for group {group_name} unprotected successfully.")
            
            return project.id
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.warning(f"Repository for group '{group_name}' already exists.")
            return e

    def get_gitlab_user(self, gitlab_user_id):
        """
        Method that retrieves a gitlab user object by given gitlab user id

        :param gitlab_user_id: id of the user object 

        :return gitlab.User object: if successful

        :throws Exception: if user object could not be returned for some reason
        """
        try:
            user = self.gl.users.get(gitlab_user_id)
            return user
        except Exception as e:
            raise e

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        # username can be netid
        users = self.gl.users.list(username=username)
        if users:
            # Return the ID of the first user matching the username
            return users[0].id
        else:
            # No user found
            return None