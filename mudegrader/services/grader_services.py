
from graderandfeedbacktool.populations import populate_database_for_one_assignment


class GraderServices:
    """
    GraderServices provides methods to populate submission data for assignments.
    
    Methods
    -------
    __init__(self, mock_object=None)
        Initializes the GraderServices class.
    
    populate_submissions(self, assignment_id, student_id=None, group_id=None)
        Populates the database with submission data for a given assignment.
    """

    def __init__(self, mock_object = None) -> None:
        """
        Initializes the GraderServices class.

        Parameters
        ----------
        mock_object : object, optional
            An optional parameter for injecting mock objects during testing. Defaults to None.
        """
        pass


    def populate_submissions(self, assignment_id, student_id=None, group_id=None):
        """
        Populates the database with submission data for a given assignment. This function utilizes `populate_database_for_one_assignment` to handle the population of submission data, including the creation of submission units and task grades, grading, and generating file paths.

        Parameters
        ----------
        assignment_id : int
            The ID of the assignment for which the database is being populated.
        student_id : int, optional
            The ID of the student. Defaults to None. If provided, the function treats the submission as an individual submission.
        group_id : int, optional
            The ID of the group. Defaults to None. If provided, the function treats the submission as a group submission.

        Returns
        -------
        The result of `populate_database_for_one_assignment`, which is a comprehensive process for populating and grading submission data for the specified assignment.
        """
        return populate_database_for_one_assignment(ass_id=assignment_id, stu_id=student_id, grp_id=group_id)