import random

import factory
from django.utils import timezone
from assignment_manager.factories import StudentFactory
from graderandfeedbacktool.factories import TeachersFactory
from graderandfeedbacktool.models import Teachers
from assignment_manager.models import Student
from .models import (
    ExamMetadata, StudentExams, StudentExerciseAttempts, StudentQuestionAttempts, 
    ExamExercises, ExamQuestions, BuddyCheck, BuddyCheckQuestion
)

class ExamMetadataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExamMetadata

    name = factory.Faker('sentence')
    exam_date = factory.LazyFunction(timezone.now)
    attempt = factory.Faker('word')
    created_by_teacher = factory.LazyAttribute(lambda _: random.choice(Teachers.objects.all()))
    comments = factory.Faker('paragraph')

class StudentExamsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentExams

    student = factory.LazyAttribute(lambda _: random.choice(Student.objects.all()))
    exam_metadata = factory.LazyAttribute(lambda _: random.choice(ExamMetadata.objects.all()))
    grade = factory.Faker('random_int', min=0, max=100)

class ExamExercisesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExamExercises

    exam_metadata = factory.LazyAttribute(lambda _: random.choice(ExamMetadata.objects.all()))
    name = factory.Faker('sentence')
    number_of_questions = factory.Faker('random_int', min=1, max=10)
    total_points = factory.Faker('random_int', min=10, max=100)
    topic = factory.Faker('word')
    author_teacher = factory.LazyAttribute(lambda _: random.choice(Teachers.objects.all()))

class ExamQuestionsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExamQuestions

    exercise = factory.LazyAttribute(lambda _: random.choice(ExamExercises.objects.all()))
    text = factory.Faker('paragraph')
    points = factory.Faker('random_int', min=1, max=10)
    type = factory.Faker('word')
    topic = factory.Faker('word')
    author_teacher = factory.LazyAttribute(lambda _: random.choice(Teachers.objects.all()))

class StudentExerciseAttemptsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentExerciseAttempts

    student = factory.LazyAttribute(lambda _: random.choice(Student.objects.all()))
    exercise = factory.LazyAttribute(lambda _: random.choice(ExamExercises.objects.all()))
    grade = factory.Faker('random_int', min=0, max=100)

class StudentQuestionAttemptsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentQuestionAttempts

    student = factory.LazyAttribute(lambda _: random.choice(Student.objects.all()))
    question = factory.LazyAttribute(lambda _: random.choice(ExamQuestions.objects.all()))
    points_awarded = factory.Faker('random_int', min=0, max=100)


class BuddyCheckFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuddyCheck

    group = factory.LazyAttribute(lambda _: random.choice(Group.objects.all()))
    student = factory.LazyAttribute(lambda _: random.choice(Student.objects.all()))
    submission_time = factory.LazyFunction(timezone.now)
    on_time = factory.Faker('boolean')
    overall_performance = factory.Faker('random_int', min=0, max=100)
    comments = factory.Faker('paragraph')

class BuddyCheckQuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuddyCheckQuestion

    buddy_check = factory.LazyAttribute(lambda _: random.choice(BuddyCheck.objects.all()))
    question_text = factory.Faker('paragraph')
    category = factory.Faker('random_element', elements=["attendance", "participation", "peer assessment"])
    score = factory.Faker('random_int', min=0, max=100)