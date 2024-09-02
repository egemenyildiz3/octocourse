
"""
    This module provides a class that provides services for gitlabmanager modules.

    The GitlabService class abstracts the functionality that gitlabmanager module has and connects it with the rest of the application.
    It requires every requirment that the modules this class uses.

    Modules that is related to this module:
    Uses:
        gitlabmanager/repositoryCrud
        gitlabmanager/studentCrud
        gitlabmanager/commit_data
        gitlabmanager/distribution_service

    Used by:
        assignment_manager/views/students
        assignment_manager/views/assignments
        assignment_manager/views/courses

    Example usage:
        gs = GitlabService()
        gs.create_course(my_course_object) with my_course_object being a Course object from assignmentmanager/models

    Dependencies:
        - Django
        - gitlabmanager
        - assignment_manager
"""




from gitlabmanager.repositoryCrud import GitlabManager
from gitlabmanager.studentCrud import GitlabManagerStudent
from gitlabmanager.commit_data import GitlabHistoryManager
from gitlabmanager.tasks import assignment_periodic_check_routine
from assignment_manager.models import Group, GroupRepo, GroupMember, StudentRepo, Interval, Course, Student
from gitlabmanager.distribution_service import DistributionService
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from django.core.exceptions import ObjectDoesNotExist
import gitlab.exceptions
import logging

from authentication.models import CustomUser

import json

class GitlabService:
    """
    Class that provides gitlab services, abstracting the logic between assignment_manager classes and gitlabmanager classes.
    """
    def __init__(self, mock_object = None) -> None:
        """
        Initializes GitlabManger class and GitlabManagerStudent class to later use their methods
        
        :param mock_object: If the class is under test, fill in a proper mocked object.
        """

        self.logger = logging.getLogger("mudegrader.gitlabservice")
        self.gm = GitlabManager(mock_object)
        self.gms = GitlabManagerStudent(mock_object)
        self.ghm = GitlabHistoryManager(mock_object)

    def create_course(self, course_object):
        """
        Creates a course in gitlab using gitlab manager's "create_course_group" method

        :param course_object: Reference to course object in db


        :return: returns what method "create_course_group" would return
            so if succesfull 0, if not returnsan error message        
        """
        result = self.gm.create_course_group(course_object)
        
        for user in course_object.staff.all():
            self.add_system_user_to_course(user, course_object)
        return result

    def remove_course(self, course_object):
        """
        Deletes the specified course in gitlab using gitlab manager's "Remove_course_group" method

        :param course_object: Reference to course object in db

        :return: returns what method "remove_course_group" would return
            so if succesfull 0, if not returns an error message                
        """
        return self.gm.remove_course_group(course_object)

    def edit_course(self, course):
        """
        Edits/Updates a course's name
        
        :param course: Reference to course object

        :return: returns what method "update_course_group_name" would return
            so if succesfull 0, if not returns an error message               
        """
        course_name = course.course_code
        course_gitlab_subgroup_id = course.gitlab_subgroup_id
        result = self.gm.update_course_group_name(course_name, course_gitlab_subgroup_id)
        for user in course.staff.all():
            self.add_system_user_to_course(user, course)
        return result

    def add_assignment(self, assignment):
        """
        
        Creates a gitlab subgroup using 
        Gitlab manager's "Create_assignment_group" method

        """
        result = self.gm.create_assignment_group(assignment)
        if not isinstance(result, gitlab.exceptions.GitlabCreateError):            
            return True
        else:
            return False


    def publish_assignment_existing_groups(self, assignment):
        """
        Publishes assignment using existing groups or individual students. Groups are filtered from database.
        Only groups with "is_active" boolean set to true are retrieved. Then for each group, 
        a groupRepo object is created.

        :param assignment: Assignment object reference to database
        """
        if assignment.is_individual:
            self.publish_individual_assignment(assignment)
        else:
            self.publish_group_assignment(assignment)
            
        #to publish read-only assignment
        self.publish_assignment_read_only(assignment)

    def publish_assignment_read_only(self, assignment):
        """
        Adds one more repository and pushes the assignment files in that. And adds every student enrolled to this course
            as a GUEST to this repository. So students can use this repository as a READ ONLY repository.

        :param assignment: Assignment object that this read only repository will be created
        """
        repo_id = self.gms.create_and_return_repo_id(assignment.gitlab_subgroup_id, f"{assignment.title}-read-only")
        repo_list = []
        repo_list.append(repo_id)
        distribution_service = DistributionService()
        distribution_service.distribute_assignment(assignment, repo_list)

        students = assignment.course.enrolled_students.all()
        
        for student in students:
            self.gms.add_student_to_repo(student.gitlab_id, repo_id, student.email, gitlab.const.AccessLevel.REPORTER)

        

    def publish_group_assignment(self, assignment):
        """
        Publish a group assignment by creating repositories for each active group 
        and adding group members to the respective repositories.

        :param assignment: The assignment object that includes the GitLab subgroup ID.

        :return None: It raises exception if an error occurs.
        """
        list_of_groups = Group.objects.filter(is_active=True)

        group_list = []
        repo_list = []
        for gr in list_of_groups:
            try:
                repo_id = self.gms.create_and_return_repo_id(assignment.gitlab_subgroup_id, gr.name) 
                if isinstance(repo_id, gitlab.exceptions.GitlabCreateError):
                    self.logger.error(f"Failed to create repo for group {gr.name}: {repo_id}")
                    repo_id = None
                else:
                    group_list.append(gr)
            except gitlab.exceptions.GitlabCreateError as e:
                self.logger.error(f"Error creating repository for group {gr.name}: {e}")
                repo_id = None
            if(repo_id is not None):
                repo_list.append(repo_id)
                group_repo = GroupRepo.objects.create(
                    group=gr,
                    repository_id=repo_id,
                    assignment=assignment
                )
                group_repo.save()
                group_members = gr.group_members.all()
                for member in group_members:
                    student = member.student_id
                    student_gitlab_id = student.gitlab_id
                    self.gms.add_student_to_repo(student_gitlab_id, repo_id, student.email)


        distribution_service = DistributionService()
        distribution_service.distribute_assignment(assignment, repo_list)

    def publish_manually_individual_assignment(self, assignment, student):
        """
        Publish an individual assignment manually by creating a repository for the student 
        and adding the student to the repository.

        :param assignment: The assignment object that includes the GitLab subgroup ID.
        :param student: The student object for whom the repository will be created.

        :return: A tuple (True, None) if the assignment was published successfully, 
                otherwise (False, error_messages) containing error messages.
        """
        
        repo_list = []
        error_messages = []
        try:
            repo_id = self.gms.create_and_return_repo_id(assignment.gitlab_subgroup_id, student.net_id)
            repo_list.append(repo_id)
            if isinstance(repo_id, gitlab.exceptions.GitlabCreateError):
                self.logger.error(f"Failed to create repo for student {student.net_id}: {repo_id}")
                repo_id = None
                error_messages.append(f"Failed to create repo for student {student.net_id}: {repo_id}")
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.error(f"Error creating repository for student {student.net_id}: {e}")
            repo_id = None
            error_messages.append(e)
        if(repo_id is not None):
            student_repo = StudentRepo.objects.create(
                student=student,
                repository_id=repo_id,
                assignment=assignment
            )
            student_repo.save()
            self.gms.add_student_to_repo(student.gitlab_id, repo_id, student.email)
            distribution_service = DistributionService()
            distribution_service.distribute_assignment(assignment, repo_list)
            return True, None
        else: 
            return False, error_messages

    def publish_manually_group_assignment(self, assignment, group):
        """
        Publish a group assignment manually by creating a repository for the group 
        and adding group members to the repository.

        :param assignment: The assignment object that includes the GitLab subgroup ID.
        :param group: The group object for which the repository will be created.

        :return: A tuple (True, error_messages) if the assignment was published successfully, 
                otherwise (False, error_messages) containing error messages.
        """
        repo_list = []
        error_messages = []
        try:
            repo_id = self.gms.create_and_return_repo_id(assignment.gitlab_subgroup_id, group.name)
            repo_list.append(repo_id)
            if isinstance(repo_id, gitlab.exceptions.GitlabCreateError):
                self.logger.error(f"Failed to create repo for group {group.name}: {repo_id}")
                repo_id = None
                error_messages.append(f"Failed to create repo for group {group.name}: {repo_id}")
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.error(f"Error creating repository for group {group.name}: {e}")
            error_messages.append(e)
            repo_id = None
        if(repo_id is not None):
            group_repo = GroupRepo.objects.create(
                group=group,
                repository_id=repo_id,
                assignment=assignment
            )
            group_repo.save()
            group_members = group.group_members.all()
            for member in group_members:
                try:
                    student = member.student_id
                    student_gitlab_id = student.gitlab_id
                    self.gms.add_student_to_repo(student_gitlab_id, repo_id, student.email)
                except Exception as e:
                    message = f"Could not add student {student.email} to repo: Probably student has non integer id: {e}"
                    error_messages.append(message)

            distribution_service = DistributionService()
            distribution_service.distribute_assignment(assignment, repo_list)
            return True, error_messages
        else: 
            return False, error_messages
        
    def publish_individual_assignment(self, assignment):
        """
        Publish an individual assignment by creating repositories for each enrolled student 
        and adding the students to their respective repositories.

        :param assignment: The assignment object that includes the GitLab subgroup ID.

        :return None: 
        """    
        repo_list = []
        list_of_students = assignment.course.enrolled_students.all()  
        for student in list_of_students:
            try:
                repo_id = self.gms.create_and_return_repo_id(assignment.gitlab_subgroup_id, student.net_id)
                
                if isinstance(repo_id, gitlab.exceptions.GitlabCreateError):
                    self.logger.error(f"Failed to create repo for student {student.net_id}: {repo_id}")
                    repo_id = None
            except gitlab.exceptions.GitlabCreateError as e:
                self.logger.error(f"Error creating repository for student {student.net_id}: {e}")
                repo_id = None
            if(repo_id is not None): #only make repo object after it is working good
                repo_list.append(repo_id)
                student_repo = StudentRepo.objects.create(
                    student=student,
                    repository_id=repo_id,
                    assignment=assignment
                )
                student_repo.save()
                self.gms.add_student_to_repo(student.gitlab_id, repo_id, student.email)

        distribution_service = DistributionService()
        distribution_service.distribute_assignment(assignment, repo_list)


    def publish_assignment_randomized(self, course, assignment, group_size):
        """
        DEPRECATED!
        This function has to be first 

        Publishes assignment using gitlab student manager's
            methods. This method makes group randomly an adds them to repositories

        :param course: the course reference to object that the assignment
            is in.
        :param assignment: reference to assignment object
        :param group_size: group size of the student groups
        """
        list_of_students = list(course.enrolled_students.values_list('id', flat=True))
        
        student_groups = self.gms.divide_students_into_groups(list_of_students, group_size)
        self.gms.add_student_groups_to_database(student_groups, assignment)
        self.gms.create_repositories_and_add_students(student_groups, assignment.pk)

    def delete_assignment(self, assignment):
        """
        Deletes the specified assignment by removing its associated GitLab subgroup.

        This method uses the GitLab manager (gm) to delete the assignment based on
        its GitLab subgroup ID.

        :param assignment: The assignment object to be deleted. It should have a 
                        'gitlab_subgroup_id' attribute.
        :raises AttributeError: If the assignment does not have a 'gitlab_subgroup_id' attribute.
        :raises self.gm.GitlabError: If an error occurs while deleting the subgroup from GitLab.
        """
        try:
            self.gm.delete_assigment(assignment.gitlab_subgroup_id)
        except AttributeError as e:
            self.logger.error(f"AttributeError: {e}. Ensure the assignment object has a valid 'gitlab_subgroup_id'.")
            raise
        except self.gm.GitlabError as e:
            self.logger.error(f"GitlabError: {e}. Error while deleting the GitLab subgroup for assignment {assignment.gitlab_subgroup_id}.")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            raise

    def get_student_repositories(self, student_id):
        """
        Retrieves the repository IDs associated with the groups a student is a member of.

        This method queries the GroupMember model to find all groups the student is a member of
        and then retrieves the repository IDs from the GroupRepo model.

        :param student_id: The ID of the student.
        :return: A list of repository IDs associated with the student's groups.
        :raises ValueError: If the student_id is None or invalid.
        :raises Exception: For any other unexpected errors.
        """
        try:
            if student_id is None:
                raise ValueError("student_id must not be None.")

            # Find the groups the student is a member of
            groups = GroupMember.objects.filter(student_id=student_id).values_list('group_id', flat=True)
            
            # Find the repositories associated with these groups
            repository_ids = list(GroupRepo.objects.filter(group_id__in=groups).values_list('repository_id', flat=True))

            repo_id_indi = StudentRepo.objects.filter(student=student_id).values_list('repository_id', flat=True)
            repository_ids.extend(repo_id_indi)
            
            return repository_ids
        except ValueError as e:
            self.logger.error(f"ValueError: {e}")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            raise  

    def get_student_commits(self, student):
        """
        Retrieves and processes commits made by a student.

        This method uses the student's GitLab ID and retrieves the repositories the
        student is associated with. For each repository, it fetches the commits made
        by the student and aggregates them into a single list, sorted by date with
        the newest first.

        :param student: The student object, which should have a gitlab_id attribute.
        :return: A list of commits made by the student, sorted by date (newest first).
        """

        all_commits = []

        student_gitlab_id = student.gitlab_id
        repo_ids = self.get_student_repositories(student_id=student.id)
        for repo_id in repo_ids:
            try:
                commits = self.ghm.get_student_commit_from_project(student_gitlab_id=student_gitlab_id, project_id=repo_id)
                all_commits.extend(commits)
            except Exception as e:
                # General exception handling
                self.logger.error(f"An unexpected error occurred: {e}")

        all_commits.sort(key=lambda commit: commit['committed_date'], reverse=True)
    
        return all_commits
    

    def get_group_commits(self, group):
        """
        Retrieves and processes commits made by a group.

        This method uses the group's GitLab ID and retrieves the repositories the
        group is associated with. For each repository, it fetches the commits made
        by the group and aggregates them into a single list, sorted by date with
        the newest first.

        :param group: The group object in database
        :return: A list of commits made by the student, sorted by date (newest first).
        """

        all_commits = []
        try: 
            repository_ids = GroupRepo.objects.filter(group=group).values_list('repository_id', flat=True)
            for repo_id in repository_ids:
                commits = self.ghm.get_project_commits(repo_id)
                all_commits.extend(commits) 
        except AttributeError as e:
            self.logger.error(f"AttributeError: {e}. Ensure the group object has a valid groupRepo reference.")
        except self.ghm.GitlabError as e:
            self.logger.error(f"GitlabError: {e}. Error while fetching commits from GitLab for group {group.name}.")
        except Exception as e:

            self.logger.error(f"An unexpected error occurred: {e}")

        all_commits.sort(key=lambda commit: commit['committed_date'], reverse=True)
    
        return all_commits

    def setup_periodic_check_routine(self, assignment):

        self.logger.info(f"Setting up periodic check routine for assignment {assignment.title}")
        
        if assignment.server_check_interval == Interval.NONE:
            return 0
        elif assignment.server_check_interval == Interval.DAY:
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=1,
                period=IntervalSchedule.MINUTES,
            )
        elif assignment.server_check_interval == Interval.WEEK:
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=7,
                period=IntervalSchedule.DAYS,
            )
        
        task_name = f"asg.tasks.{assignment.title}.periodic_check"
    
        PeriodicTask.objects.get_or_create(
            interval=schedule,
            name=task_name,
            task="gitlabmanager.tasks.assignment_periodic_check_routine",  # This should be the name of your Celery task
            args=json.dumps([assignment.id]),
            expires=assignment.due_date,
        )

    def remove_periodic_check_routine(self, assignment):
        
        task_name = f"asg.tasks.{assignment.title}.periodic_check"
        try:
            task = PeriodicTask.objects.get(name=task_name)
            task.delete()
        except ObjectDoesNotExist as e:
            self.logger.error(f"ObjectDoesNotExist: {e}. Task {task_name} does not exist.")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
    

    def get_course_url(self, course_gitlab_subgroup_id):
        try:
            course_group = self.gm.get_gitlab_group(gitlab_group_id=course_gitlab_subgroup_id)
            url = course_group.web_url
            return url
        except Exception as e:
            raise e

    def get_student_url(self, student_gitlab_id):
        try:
            user = self.gms.get_gitlab_user(gitlab_user_id=student_gitlab_id)
            url = user.web_url
            return url
        except Exception as e:
            raise e

    def get_assignment_url(self, assignment_gitlab_id):
        try:
            assignment_group = self.gm.get_gitlab_group(gitlab_group_id=assignment_gitlab_id)
            url = assignment_group.web_url
            return url
        except Exception as e:
            raise e

    def add_system_user_to_course(self, user: CustomUser, course: Course) -> None:
        if not user.gitlab_id:
            self.logger.warning(f"No Gitlab ID found for user [{user}]")
            return

        if not course.gitlab_subgroup_id:
            self.logger.warning(f"No Gitlab ID found for course [{course.unique_name}]")
            return

        if user.is_teacher:
            role = gitlab.const.AccessLevel.MAINTAINER
        else:
            role = gitlab.const.AccessLevel.REPORTER


        self.logger.info(f'Trying to add user [{user}] to course [{course}] with Gitlab ID [{course.gitlab_subgroup_id}]')
        try:
            self.gms.add_user_to_gitlab_group(
                gitlab_user_id=user.gitlab_id,
                gitlab_group_id=course.gitlab_subgroup_id,
                access_level=role,
            )
            self.logger.info(f'Added user [{user}] to course [{course.course_code}] on gitlab with access level [{role.name}]')
        except:
            self.logger.error(f'FAILED to add user [{user}] to course [{course.course_code}] on gitlab with access level [{role.name}]')

