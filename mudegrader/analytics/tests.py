from django.test import TestCase
from django.utils import timezone
from assignment_manager.models import Assignment, Student, Group, AssignmentUnit, Course, GroupMember
from graderandfeedbacktool.models import Submissions, TaskGrades, Teachers
from authentication.models import Role, CustomUser
from .models import StudentExams, ExamMetadata, BuddyCheck
from .services import (
    get_exam_grades, get_time_left, get_pass_rate, 
    get_average_grades, get_grading_progress, get_nationality_rates, 
    get_exam_participants, get_group_performance, 
    get_group_grades, get_student_performance, 
    get_assignment_overview
)
import statistics

class ExamGradesTest(TestCase):
    def setUp(self):
        teacher = Teachers.objects.create(first_name="Teacher", last_name="One", email="teacher1@example.com")
        exam1 = ExamMetadata.objects.create(name="Exam 1", exam_date=timezone.now(), attempt="First", created_by_teacher=teacher, comments="Good exam")
        exam2 = ExamMetadata.objects.create(name="Exam 2", exam_date=timezone.now(), attempt="First", created_by_teacher=teacher, comments="Good exam")
        student1 = Student.objects.create(net_id="net1", first_name="Student1", last_name="LastName", email="student1@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        student2 = Student.objects.create(net_id="net2", first_name="Student2", last_name="LastName", email="student2@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 2", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        StudentExams.objects.create(exam_metadata=exam1, student=student1, grade=85)
        StudentExams.objects.create(exam_metadata=exam1, student=student2, grade=90)
        StudentExams.objects.create(exam_metadata=exam2, student=student1, grade=75)

    def test_get_exam_grades(self):
        exam_grades = get_exam_grades()
        self.assertEqual(exam_grades["Exam 1"], [85, 90])
        self.assertEqual(exam_grades["Exam 2"], [75])


class TimeLeftTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')

        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user)
        self.assignment1 = Assignment.objects.create(title="Assignment1", due_date=timezone.now() + timezone.timedelta(days=5), is_published=True, total_points=100, course=course)
        self.assignment2 = Assignment.objects.create(title="Assignment2", due_date=timezone.now() + timezone.timedelta(days=10), is_published=True, total_points=100, course=course)

    def test_get_time_left(self):
        time_left = get_time_left()
        self.assertIn('Assignment1', time_left)
        self.assertIn('Assignment2', time_left)


class PassRateTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user)
        self.assignment = Assignment.objects.create(title="Assignment1", is_published=True, total_points=100, course=course)
        student1 = Student.objects.create(net_id="net1", first_name="Student1", last_name="LastName", email="student1@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        student2 = Student.objects.create(net_id="net2", first_name="Student2", last_name="LastName", email="student2@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 2", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        Submissions.objects.create(assignment=self.assignment, is_passed=True, student=student1)
        Submissions.objects.create(assignment=self.assignment, is_passed=False, student=student2)

    def test_get_pass_rate(self):
        pass_rate = get_pass_rate()
        self.assertIn('Assignment1', pass_rate)
        self.assertEqual(pass_rate['Assignment1'], 50.0)


class AverageGradesTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user)
        self.assignment = Assignment.objects.create(title="Assignment1", is_published=True, total_points=100, course=course)
        student1 = Student.objects.create(net_id="net1", first_name="Student1", last_name="LastName", email="student1@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        student2 = Student.objects.create(net_id="net2", first_name="Student2", last_name="LastName", email="student2@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 2", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        Submissions.objects.create(assignment=self.assignment, total_points=80, student=student1)
        Submissions.objects.create(assignment=self.assignment, total_points=90, student=student2)

    def test_get_average_grades(self):
        average_grades = get_average_grades()
        self.assertIn('Assignment1', average_grades)
        self.assertEqual(average_grades['Assignment1'], 85.0)


class GradingProgressTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user)
        self.assignment = Assignment.objects.create(title="Assignment1", is_published=True, total_points=100, course=course)
        student1 = Student.objects.create(net_id="net1", first_name="Student1", last_name="LastName", email="student1@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        student2 = Student.objects.create(net_id="net2", first_name="Student2", last_name="LastName", email="student2@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 2", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        Submissions.objects.create(assignment=self.assignment, grading_status='Graded', student=student1)
        Submissions.objects.create(assignment=self.assignment, grading_status='Not Graded', student=student2)

    def test_get_grading_progress(self):
        grading_progress = get_grading_progress()
        self.assertIn('Assignment1', grading_progress)
        self.assertEqual(grading_progress['Assignment1'], 50.0)


class NationalityRatesTest(TestCase):
    def setUp(self):
        Student.objects.create(net_id="net1", first_name="Student1", last_name="LastName", email="student1@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        Student.objects.create(net_id="net2", first_name="Student2", last_name="LastName", email="student2@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        Student.objects.create(net_id="net3", first_name="Student3", last_name="LastName", email="student3@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 2", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")

    def test_get_nationality_rates(self):
        nationality_rates = get_nationality_rates()
        self.assertIn('Type 1', nationality_rates)
        self.assertIn('Type 2', nationality_rates)
        self.assertAlmostEqual(nationality_rates['Type 1'], 66.67, places=2)
        self.assertAlmostEqual(nationality_rates['Type 2'], 33.33, places=2)



class ExamParticipantsTest(TestCase):
    def setUp(self):
        teacher = Teachers.objects.create(first_name="Teacher", last_name="One", email="teacher1@example.com")
        exam1 = ExamMetadata.objects.create(name="Exam 1", exam_date=timezone.now(), attempt="First", created_by_teacher=teacher, comments="Good exam")
        exam2 = ExamMetadata.objects.create(name="Exam 2", exam_date=timezone.now(), attempt="First", created_by_teacher=teacher, comments="Good exam")
        student1 = Student.objects.create(net_id="net1", first_name="Student1", last_name="LastName", email="student1@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        student2 = Student.objects.create(net_id="net2", first_name="Student2", last_name="LastName", email="student2@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 2", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        StudentExams.objects.create(exam_metadata=exam1, student=student1, grade=80)
        StudentExams.objects.create(exam_metadata=exam1, student=student2, grade=85)
        StudentExams.objects.create(exam_metadata=exam2, student=student1, grade=90)

    def test_get_exam_participants(self):
        participants = get_exam_participants()
        self.assertEqual(participants["Exam 1"], 2)
        self.assertEqual(participants["Exam 2"], 1)



class GroupPerformanceTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user)
        self.group = Group.objects.create(name="Group1", course=course)
        self.assignment = Assignment.objects.create(title="Assignment1", is_published=True, total_points=100, course=course)
        Submissions.objects.create(group_id=self.group.id, total_points=80, assignment=self.assignment)
        Submissions.objects.create(group_id=self.group.id, total_points=90, assignment=self.assignment)

    def test_get_group_performance(self):
        performance = get_group_performance()
        self.assertEqual(performance["Group1"], 85.0)


class GroupGradesTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user)
        self.group = Group.objects.create(name="Group1", course=course)
        self.assignment = Assignment.objects.create(title="Assignment1", is_published=True, total_points=100, course=course)
        Submissions.objects.create(group_id=self.group.id, assignment=self.assignment, total_points=80)
        Submissions.objects.create(group_id=self.group.id, assignment=self.assignment, total_points=90)

    def test_get_group_grades(self):
        group_grades = get_group_grades()
        self.assertIn('Group1', group_grades)
        self.assertIn('Assignment1', group_grades['Group1'])
        self.assertEqual(group_grades['Group1']['Assignment1'], 85.0)


class StudentPerformanceTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        self.user.set_password('testpassword')
        self.student = Student.objects.create(net_id="net1", first_name="John", last_name="Doe", email="john@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        self.assignment = Assignment.objects.create(title="Assignment1", is_published=True, total_points=100, course=Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user))
        teacher = Teachers.objects.create(first_name="Teacher", last_name="One", email="teacher1@example.com")
        exam = ExamMetadata.objects.create(name="Exam 1", exam_date=timezone.now(), attempt="First", created_by_teacher=teacher, comments="Good exam")
        Submissions.objects.create(student=self.student, total_points=80, assignment=self.assignment)
        Submissions.objects.create(student=self.student, total_points=90, assignment=self.assignment)
        StudentExams.objects.create(student=self.student, exam_metadata=exam, grade=85)
        StudentExams.objects.create(student=self.student, exam_metadata=exam, grade=75)
        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2024, end_year=2025, department="CS", created_by= self.user)
        group = Group.objects.create(name="Group1", course=course)
        group.assignments.add(self.assignment)
        BuddyCheck.objects.create(group=group, student=self.student, submission_time=timezone.now(), on_time=True, overall_performance=8, comments="Good")

    def test_get_student_performance(self):
        performance = get_student_performance()
        self.assertEqual(performance[0]['first_name'], "John")
        self.assertEqual(performance[0]['assignment_scores'], 85.0)
        self.assertEqual(performance[0]['exam_scores'], 80.0)
        self.assertEqual(performance[0]['buddy_check_scores'], 8.0)


class AssignmentOverviewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER
        )
        course = Course.objects.create(course_code="C101", description="Course 1", start_year=2023, end_year=2024, department="CS", created_by= self.user)
        self.assignment = Assignment.objects.create(title="Assignment1", is_published=True, total_points=100, course=course)
        AssignmentUnit.objects.create(assignment=self.assignment, name="Unit1", file="unit1.pdf")
        AssignmentUnit.objects.create(assignment=self.assignment, name="Unit2", file="unit2.pdf")
        student1 = Student.objects.create(net_id="net1", first_name="Student1", last_name="LastName", email="student1@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 1", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        student2 = Student.objects.create(net_id="net2", first_name="Student2", last_name="LastName", email="student2@example.com", enrollment_year=2020, program="Program1", msc_track="Track1", self_assessed_skill="Skill1", nationality_type="Type 2", start_year_in_mude=2019, brightspace_id="B123", gitlab_id="G123", public_ssh_key="SSHKEY")
        Submissions.objects.create(assignment=self.assignment, is_passed=True, total_points=85, student=student1, grading_status='Graded')
        Submissions.objects.create(assignment=self.assignment, is_passed=False, total_points=45, student=student2)

    def test_get_assignment_overview(self):
        overview = get_assignment_overview()
        self.assertIn('Assignment1', [ov['name'] for ov in overview])
        assignment_overview = next(ov for ov in overview if ov['name'] == 'Assignment1')
        self.assertEqual(assignment_overview['points'], 100)
        self.assertEqual(assignment_overview['assignment_units'], 2)
        self.assertEqual(assignment_overview['repository_submissions'], 2)
        self.assertEqual(assignment_overview['pass_fail_percentages'], '50.00%')
        self.assertEqual(assignment_overview['grading_status'], '50.00%')
        self.assertEqual(assignment_overview['max_grade'], 85)
        self.assertEqual(assignment_overview['min_grade'], 45)
