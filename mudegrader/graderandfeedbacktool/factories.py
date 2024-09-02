import random
import factory
from django.utils import timezone
from assignment_manager.models import AssignmentUnit, Assignment, Student, Group
from assignment_manager.factories import AssignmentFactory, StudentFactory, GroupFactory, AssignmentUnitFactory  # Import the necessary factories
from .models import Teachers, Submissions, GradeHistory, TaskGrades, Feedback, Tasks,SubmissionUnits

class TeachersFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Teachers

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    department = factory.Iterator(['Computer Science', 'Mathematics', 'Physics'])

class SubmissionsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submissions

    assignment = factory.LazyAttribute(lambda _: random.choice(Assignment.objects.all()))
    student = factory.LazyAttribute(lambda _: random.choice(Student.objects.all()))
    group = factory.Maybe(
        'student', 
        yes_declaration=None, 
        no_declaration=factory.LazyAttribute(lambda _: random.choice(Group.objects.all()))
    )
    submission_time = factory.LazyFunction(timezone.now)
    file_path = factory.Faker('file_path')
    grading_status = 'Not Graded'
    feedback = factory.Faker('text')
    
    @factory.lazy_attribute
    def total_points(self):
        return random.randint(0, 100)

    @factory.lazy_attribute
    def is_passed(self):
        return self.total_points >= 50


class SubmissionUnitsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubmissionUnits

    submission = factory.LazyAttribute(lambda _: random.choice(Submissions.objects.all()) if Submissions.objects.exists() else SubmissionsFactory())
    assignment_unit = factory.LazyAttribute(lambda _: random.choice(AssignmentUnit.objects.all()) if AssignmentUnit.objects.exists() else AssignmentUnitFactory())
    submission_time = factory.LazyFunction(timezone.now)
    file_path = factory.Faker('file_path')
    feedback = factory.Faker('text')
    converted_file_path = factory.Faker('file_path')
    total_grade = factory.LazyFunction(lambda: random.uniform(0, 100))
    total_points = factory.Faker('random_int', min=0, max=100)
    number_of_tasks = factory.Faker('random_int', min=0, max=10)
    is_graded = factory.Faker('boolean')
    grading_status = factory.Iterator(['Not Graded', 'Graded'])
    
class TaskGradesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaskGrades

    question_id = factory.Faker('random_int', min=1, max=100)
    task = factory.LazyAttribute(lambda _: random.choice(Tasks.objects.all()) if Tasks.objects.exists() else None)
    submission_unit = factory.LazyAttribute(lambda _: random.choice(SubmissionUnits.objects.all()) if SubmissionUnits.objects.exists() else None)
    graded_by_teacher_id = factory.LazyAttribute(lambda _: random.choice(Teachers.objects.all()) if Teachers.objects.exists() else None)
    date_graded = factory.LazyFunction(timezone.now)
    max_points = factory.LazyFunction(lambda: random.uniform(0, 100))
    points_received = factory.LazyFunction(lambda: random.uniform(0, 100))
    is_auto_graded = factory.Faker('boolean')
    is_graded = factory.Faker('boolean')
    grading_type = factory.Iterator(['Manual', 'Automatic'])


class GradeHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GradeHistory

    grade_id = factory.LazyAttribute(lambda _: random.choice(TaskGrades.objects.all()))
    previous_points = factory.Faker('random_int', min=0, max=100)
    new_points = factory.Faker('random_int', min=0, max=100)
    changed_by_teacher_id = factory.LazyAttribute(lambda _: random.choice(Teachers.objects.all()))
    change_reason = factory.Faker('text')
    date_changed = factory.LazyFunction(timezone.now)

class FeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Feedback

    submission_id = factory.LazyAttribute(lambda _: random.choice(Submissions.objects.all()))
    grade_id = factory.LazyAttribute(lambda _: random.choice(TaskGrades.objects.all()))
    feedback_file_path = factory.Faker('file_path')
    date_provided = factory.LazyFunction(timezone.now)

