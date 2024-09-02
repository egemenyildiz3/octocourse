import logging

import pandas as pd
from django.core.files import File

from assignment_manager.models import Student, Group, GroupMember, Course
from assignment_manager.tag_model import Tag
from gitlabmanager.studentCrud import GitlabManagerStudent

logger = logging.getLogger(__name__)


def get_gitlab_id_by_netid(net_id):
    """
    Helper function that uses a GitlabManagerStudent to get a Gitlab user ID by
    searching for a netid.

    Parameters:
    net_id (str): The netid to search for.
    """
    gms = GitlabManagerStudent()
    gitlab_id = gms.get_user_id_by_username(net_id)
    return gitlab_id


def load_class(csv_file: File, course: Course):
    """
    Load student and group data from a CSV file into the system.
    A Username column is required to be in the CSV file.

    The function reads from a CSV file using pandas, logs relevant information,
    and handles the creation and updating of student and group data based on the
    CSV content. The method creates a user from the netid part of the Username field.
    Using this, the method tries to find the GitLab ID associated with the netid.
    If the GitLab ID cannot be found in the CSV file, the method adds
    a `gitlab_id_missing` tag to the student. If GroupNames are specified,
    the method will create the Group and add students with the same GroupName to it.

    Parameters:
        csv_file (File): The CSV file containing student and group data.
        course (Course): The course object to which the students and groups will be linked.

    Raises:
        ValueError: If the CSV file cannot be parsed by pandas or the file lacks a Username column

    Notes:
        The method expects, but not necessarily requires, the CSV file to include the following columns:
        - OrgDefinedId      Understood to be netid
        - Username*         required, must be in the form of netid@url.something
        - LastName
        - FirstName
        - Email
        - GroupCategory*    ignored at the moment
        - GroupName*        required for adding students to groups
    """
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        raise ValueError(f'Pandas could not parse file: {e}')
    expected_columns = ['OrgDefinedId', 'Username', 'LastName', 'FirstName', 'Email', 'GroupCategory', 'GroupName']
    unexpected_columns = [col_name for col_name in df.columns.tolist() if not col_name in expected_columns]
    logger.info(f'Importing students & groups from {str(csv_file)}')
    # create tag for students with missing gitlab id
    missing_gitlab_id_tag, _ = Tag.objects.update_or_create(
        name='gitlab_id_missing',
        background_color='#FF00AA',
        course=course,
    )
    # keep important counts
    students_with_no_gitlab_id_count = 0
    students_with_no_group = 0
    student_created_count = 0
    student_updated_count = 0
    group_count = 0

    for index, row in df.iterrows():
        # dict from which we are going to create the student object
        student_fields = dict()
        if not 'Username' in df.columns:
            raise ValueError('Provided CSV file did not contain the required column "Username" (case-sensitive)')
        # if field is empty in dataframe or not valid email
        username = row['Username']
        if pd.isna(username) or "@" not in username:
            logger.warning(f'Provided CSV file does not have a valid Username field in row [{index}]. '
                           f'Skipping Student creation.')
            continue

        net_id = row['Username'].split('@')[0]
        # non-required fields
        if 'FirstName' in df.columns:
            student_fields['first_name'] = row['FirstName']
        if 'LastName' in df.columns:
            student_fields['last_name'] = row['LastName']
        if 'Email' in df.columns:
            student_fields['email'] = row['Email']
        if 'OrgDefinedId' in df.columns:
            student_fields['brightspace_id'] = row['OrgDefinedId']
        # todo GroupCategory as extra fields

        gitlab_id = get_gitlab_id_by_netid(net_id)
        if gitlab_id:
            student_fields['gitlab_id'] = gitlab_id
        # create or update the student
        student, was_created = Student.objects.update_or_create(
            net_id=net_id,
            defaults=student_fields,
        )
        student.courses_enrolled.add(course)
        student.save()

        if was_created:
            student_created_count += 1
        else:
            student_updated_count += 1

        if not gitlab_id:
            students_with_no_gitlab_id_count += 1
            student.tags.add(missing_gitlab_id_tag)

        if 'GroupName' not in df.columns:
            logger.warning('Provided CSV file did not contain the required column "GroupName" (case-sensitive)')
            continue

        group_name = row['GroupName']
        if pd.isna(group_name) or not group_name:
            logger.debug(f'Provided CSV file does not have a valid GroupName field in row [{index}]')
            continue

        # try to create the group
        group, was_created = Group.objects.get_or_create(
            name=group_name,
            course=course,
        )
        if was_created:
            group_count += 1
        # create the membership if it did not exist already
        GroupMember.objects.update_or_create(
            student_id=student,
            group_id=group,
        )

    if students_with_no_group > 0:
        logger.warning(f'There were [{students_with_no_gitlab_id_count}] not found by their net id on GitLab. '
                       f'"gitlab_id_missing" tags were added to those students.')
    if students_with_no_group > 0:
        logger.warning(f'There were [{students_with_no_group}] students added without a specific group.')
    logger.info(f'Successfully created [{student_created_count}] and updated [{student_updated_count}] students')
    logger.info(f'Successfully created [{group_count}] groups')
