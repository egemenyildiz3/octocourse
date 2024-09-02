
"""
This module provides a class for managing GitLab operations, such as creating course groups, updating course groups,
creating assignment groups, and creating repositories.

The GitlabManager class encapsulates the functionality for interacting with GitLab using the python-gitlab library.
It requires the python-gitlab library to be installed.

Example usage:
    
    gm = GitlabManager()\n
    gm.createCourseGroup("test-course")
    
Note: This module assumes the presence of certain dependencies and environment variables, such as the Django framework,
the assignment_manager.models.Groups model, and the GITLAB_PRIVATE_TOKEN environment variable.

Dependencies:
    - Django (assignment_manager.models.Groups)
    - python-gitlab

Environment Variables:
    - GITLAB_PRIVATE_TOKEN: GitLab private access token

"""


import random
import gitlab.exceptions
from assignment_manager.models import Group, Assignment, Course
import os
import subprocess
import gitlab
import logging



# gl.enable_debug()

## GLOBAL PARAMS
# mude-x test env id: 35312
# logging namespace: mudegrader.gitlabmanager


class GitlabManager:
    """
    Class for managing GitLab operations.
    """

    def __init__(self, mocked_gl=None):
        """
        Initializes a RepositoryCrud object.

        :param mocked_gl: Optional mocked GitLab connection object for testing purposes.
        :type mocked_gl: gitlab.Gitlab or None
        
        """
        
        #: Logger with namespace "mudegrader.gitlabmanager".
        self.logger = logging.getLogger("mudegrader.gitlabmanager")

        #: Global group ID for the Mude-X test environment on the TU central gitlab.
        self.global_group_id = 35312

        self.token = os.getenv("GITLAB_PRIVATE_TOKEN") 

        if mocked_gl is None:
            #: GitLab connection object.
            self.gl = gitlab.Gitlab(url='https://gitlab.tudelft.nl/', private_token=self.token)
            self.gl.auth()
        else:
            self.gl = mocked_gl

    

    def create_course_group(self, course):
        """
        Create a gitlab subgroup for the course in the global group (mude-x-test).

        :param course_name: Name of the course.

        :return: 0 if the course was created successfully, The raised exception otherwise.

        """

        try:
            course_name = course.unique_name

            # self.logger.info(f"Course name: {course.course_code} | Top level group: {topLevelGroup.name}")
            subgroup = self.gl.groups.create({'name': f'{course_name}', 'path': f'{course_name}', 'parent_id': self.global_group_id})

            course.gitlab_subgroup_id = subgroup.get_id()
            course.save()
            self.logger.info(f"Course '{course_name}' created successfully.")
            return 0
        
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.warning(f"Course '{course_name}' already exists. Assigning existing group id.")
            course.gitlab_subgroup_id = self.gl.groups.get(f"mude-project-x/{course_name}").get_id()    
            course.save()
            return course.gitlab_subgroup_id
        
        except gitlab.exceptions.GitlabGetError as e:
            self.logger.error(f"Course could not be found. strace: {e}")
            return e

    def remove_course_group(self,course):
            """
            Delete a gitlab subgroup for the course in the global group (mude-x-test).

            :param course_name: Course object to be deleted.

            :return: 0 if the course was deleted successfully, The raised exception otherwise.

            """

            try:
                course_name = course.unique_name

                if course.gitlab_subgroup_id is None:
                    self.logger.error("Course subgroup not found.")
                    return 1
                
                self.gl.groups.delete(course.gitlab_subgroup_id)
                self.logger.info(f"Course subgroup'{course_name}' deleted successfully.")
                return 0
            
            except gitlab.exceptions.GitlabDeleteError as e:
                self.logger.warning(f"Course '{course_name}' couldnt be deleted. {e}")
                return e
            
    def update_course_group_name(self, course_name, course_gitlab_subgroup_id):
        """
        Update the name of the course group in GitLab subgroups.

        :param course_name: Updated name of the course.
        :param course_gitlab_subgroup_id: GitLab ID of the course subgroup. (added to database when created)

        :return: 0 if the course was updated successfully, The raised exception otherwise.

        """

        try:
            course_group = self.gl.groups.get(course_gitlab_subgroup_id)

            course_group.name = course_name
            course_group.save()
            self.logger.info(f"Course '{course_name}' updated successfully.")
            return 0

        except gitlab.exceptions.GitlabUpdateError as e:

            self.logger.warning(f"Course '{course_name}' could not be updated.")
            return e


    def create_assignment_group(self, assignment: Assignment):
        """
        Create a gitlab subgroup for the assignment in the course subgroup.

        :param assignment: Assignment object reference that comes from database

        :return: Assingment Group ID if the assignment was created successfully, The raised exception otherwise.
        """
        course_name = assignment.course.unique_name
        assignment_name = assignment.title
        
        name_space = "mude-project-x"
        
        # course_group = self.gl.groups.get("subgroup1")
        # todo this line below is wrong, refactor method
        course = Course.objects.filter(id=assignment.course.id).first()
        self.logger.info(f"Assignment belongs to {course.course_code}")
        
        if course.gitlab_subgroup_id is None:
            self.logger.error("Course subgroup not found on Gitlab.")
            return "Course subgroup not found on Gitlab."
        course_group_gitlab_id = assignment.course.gitlab_subgroup_id

        try:
            subg_path = {'name': assignment_name, 'path': f"{name_space}-{course_name}-{assignment_name}", 'parent_id': course_group_gitlab_id} 
            subgroup = self.gl.groups.get(subg_path)
            assignment.gitlab_subgroup_id = subgroup.get_id()
            assignment.save()
            return subgroup.get_id()
        
        except gitlab.exceptions.GitlabGetError as e:
            self.logger.warning(f"Assignment '{assignment_name}' could not be found. Creating assignment subgroup...")
            try:
                subgroup = self.gl.groups.create(subg_path)
                assignment.gitlab_subgroup_id = subgroup.get_id()
                assignment.save()
                self.logger.info(f"Assignment '{assignment_name}' created successfully.")
                return assignment.gitlab_subgroup_id
            except gitlab.exceptions.GitlabCreateError as e:
                self.logger.error(f"Assignment '{assignment_name}' could not be created.")
                return e
        
        except Exception as e:
            self.logger.error(f"Unexpected excpection in assignment group creation")
            return e  
    
    def remove_assignment_group(self, assignment: Assignment):
        """
        Delete a gitlab subgroup for the assignment in the course subgroup.

        :param assignment: Assignment object to be deleted.
        :type assignment: Assignment

        :return: 0 if the assignment was deleted successfully, The raised exception otherwise.
        :rtype: int or Exception

        """

        try:
            asg_name = assignment.title

            if assignment.gitlab_subgroup_id is None:
                self.logger.error("Assignment subgroup not found.")
                return 1
            
            self.gl.groups.delete(assignment.gitlab_subgroup_id)

            assignment.delete()
            self.logger.info(f"Assignment subgroup'{asg_name}' deleted successfully.")
            
            return 0
        
        except gitlab.exceptions.GitlabDeleteError as e:
            self.logger.warning(f"Assignment '{asg_name}' couldnt be deleted. {e}")
            return e

    def create_repo(self,group):
        """
        Create a repository for the group in the assignment subgroup.
        
        :param group: Group object.
        :type group: Group

        :return: 0 if the repository was created successfully, The raised exception otherwise.

        """
        # TODO: This line seems wrong
        asg = Assignment.objects.get(id=group.assignments.first().id)
        course = Course.objects.get(id=asg.course.id)
        name_space = f"mude-project-x/{course.course_code}/{asg.title}"

        try:
            res = self.gl.projects.create({'name': group.name, 'namespace_id': asg.gitlab_subgroup_id})
            self.logger.info(f"Repository for group {group.name} created successfully.")
            return res
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.warning(f"Repository for group '{group.name}' already exists.")
            return e
        


    def create_repositories(self, assignment):
        # course table needs a gitlab_subgroup_id field
        groupList = Group.objects.filter(assignments=assignment).all()
       
        # put assignment.gitlab_subgroup_id
        if assignment.gitlab_subgroup_id is None:
            try:
                self.logger.warning(f"Assignment subgroup not found. Creating assignent subgroup...")
                self.create_assignment_group(assignment)
            except gitlab.exceptions.GitlabCreateError as e:
                self.logger.error(f"Assignment subgroup could not be created.")
                return e
        # Specify filepath for the new assignment
        list_of_repo_ids = []
        for group in groupList:
            project = self.create_repo(group)
            if (isinstance(project, gitlab.exceptions.GitlabCreateError)):
                self.logger.error("Could not create repo!")
            else:
                list_of_repo_ids.append(project.id)
        return list_of_repo_ids
    
    def delete_all_courses(self):
        """
        This method deletes all courses from the top level gitlab group!
            Courses mean "Subgroups" in the context of gitlab
        
        """
        topLevelGroup = self.gl.groups.get(self.global_group_id)
        courses = topLevelGroup.subgroups.list()

        for course in courses:
            self.gl.groups.delete(course.id)
            self.logger.info(f"gitlab course cleaner is ON! Deleted: {course}")
        
    def delete_assigment(self, group_gitlab_id):
        try:
            group = self.gl.groups.get(group_gitlab_id)
            group.delete()
        except Exception as e:
            self.logger.exception(e)

    def get_gitlab_group(self, gitlab_group_id: int):
        try:
            course_group = self.gl.groups.get(id=gitlab_group_id)
        except Exception as e:
            raise e
        return course_group
    
    def create_gitlab_group(self, name, name_space, course_name, course_group_gitlab_id):
        try:
            self.gl.groups.create({'name': name, 'path': f"{name_space}-{course_name}", 'parent_id': course_group_gitlab_id})
        except:
            pass




if __name__ == '__main__':
    gm = GitlabManager()
    gm.create_course_group("test-course")


    