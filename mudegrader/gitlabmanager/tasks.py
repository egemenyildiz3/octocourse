import logging
from celery import shared_task
import json
from gitlabmanager.distribution_service import DistributionService
from assignment_manager.models import Assignment
from graderandfeedbacktool.feedback_service import send_autograded_feedback
import os
from django.shortcuts import get_object_or_404
from graderandfeedbacktool.models import Submissions

@shared_task
def assignment_periodic_check_routine(assignment_id: int) -> int:
    """
    Periodic check routine task that checks for new submissions and autogrades them
    Integrated with Celery task queue

    :param assignment_id: the id of the assignment to check for new submissions
    :type assignment_id: int

    """
    
    logger_namepace = os.getenv("LOGGER_NAMESPACE")
    logger = logging.getLogger(logger_namepace)
    logger.info("Initiating periodic routine...")

    try:
        ds = DistributionService()
    
        asg = get_object_or_404(Assignment, id=assignment_id)
        course_id = asg.course.id
        assignment_title = asg.title
        assignment_gitlab_id = asg.gitlab_subgroup_id

        distribution_service = DistributionService()

        repository_list = distribution_service.gather_submissions(course_id, assignment_gitlab_id, asg.course.course_code, assignment_title)

        if isinstance(repository_list, Exception):
            logger.warning("Periodic check: repository list is an exception")

        failed_repositories = distribution_service.clone_submissions(repository_list, course_id, assignment_title)

        if failed_repositories:
            logger.warning("Periodic check: some repositories failed to clone")
        
        for repo in failed_repositories:
            logger.warning(f"Failed to clone repository: {repo}")
        
        jsonRes = send_autograded_feedback(assignment_id=asg.id)

        logger.info(logging.info("JSON Response: %s", json.dumps(jsonRes, indent=2)))
        
    except Exception as e:
        logger.warning(f"Periodic check: failed to complete routine\n\n {e}")

    

