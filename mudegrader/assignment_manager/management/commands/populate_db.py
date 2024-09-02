import random
from typing import List, Type

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction, models

from assignment_manager.models import Assignment, Student, Group
from assignment_manager.tag_model import Tag
from django.apps import apps

from authentication.models import Role, CustomUser
from assignment_manager.factories import StudentFactory, CourseFactory, AssignmentFactory, GroupFactory, \
    AssignmentUnitFactory, TagFactory, CommentFactory,TasksFactory,GroupMemberFactory
from graderandfeedbacktool.factories import (
    TeachersFactory, SubmissionsFactory,SubmissionUnitsFactory,
    GradeHistoryFactory, FeedbackFactory,TaskGradesFactory
)
from analytics.factories import (
    ExamMetadataFactory, StudentExamsFactory, StudentExerciseAttemptsFactory,
    StudentQuestionAttemptsFactory, ExamExercisesFactory, ExamQuestionsFactory
)
from graderandfeedbacktool.models import Submissions


class Command(BaseCommand):
    help = 'Populates the database with sample data'

    @staticmethod
    def randomly_sample_objects(model: Type[models.Model]) -> List[models.Model]:

        object_list = list(model.objects.all())
        # Choose a random number of tags to add, between 0 and the number of available tags
        amount_to_add = random.randint(0, len(object_list))
        selected_object = random.sample(object_list, amount_to_add)
        return selected_object

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(self.style.ERROR('This command is only available in debug mode.'))
            return
        with transaction.atomic():
            for model in apps.get_models():
                model.objects.all().delete()  # Delete all data from each table
        self.stdout.write(self.style.SUCCESS('Successfully cleared the database.'))


        # Create or update users
        users_data = [
            {
                'username': 'Teacher',
                'password': 'teacher123',
                'first_name': 'Otto',
                'last_name': 'Visser',
                'email': 'teacher@tudelft.com',
                'is_staff': True,
                'is_superuser': False,
                'role': Role.TEACHER
            },
            {
                'username': 'TA',
                'password': 'ta123',
                'first_name': 'Aleksandra',
                'last_name': 'Jach',
                'email': 'ta@tudelft.com',
                'is_staff': True,
                'is_superuser': False,
                'role': Role.TA
            },
            {
                'username': 'root',
                'password': '123',
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        ]

        for user_data in users_data:
            user, created = CustomUser.objects.update_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                    'role': user_data.get('role', Role.UNREGISTERED)
                }
            )
            # setting password after the first initialization is needed for password being properly hashed, otherwise it won't work
            user.set_password(user_data['password'])
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f"Successfully created user '{user.username}'"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Successfully updated user '{user.username}'"))

        # Order matters in this case, the factories will try to connect some models that have foreign keys
        # to other models with random ones. This means that those have to be created before we pick randomly.
        CourseFactory.create_batch(2)
        StudentFactory.create_batch(15)
        AssignmentFactory.create_batch(10)
        TeachersFactory.create_batch(5)
        GroupFactory.create_batch(10)
        GroupMemberFactory.create_batch(40)
        TagFactory.create_batch(5)


        AssignmentUnitFactory.create_batch(10)
        SubmissionUnitsFactory.create_batch(30)
        # add tags
        for assignment in list(Assignment.objects.all()):
            selected_tags = self.randomly_sample_objects(Tag)
            assignment.tags.set(selected_tags)

        for student in list(Student.objects.all()):
            selected_tags = self.randomly_sample_objects(Tag)
            student.tags.set(selected_tags)

        for group in list(Group.objects.all()):
            selected_tags = self.randomly_sample_objects(Tag)
            group.tags.set(selected_tags)

        for submission in list(Submissions.objects.all()):
            selected_tags = self.randomly_sample_objects(Tag)
            submission.tags.set(selected_tags)

        # create rest
        TasksFactory.create_batch(10)
        ExamMetadataFactory.create_batch(5)
        SubmissionsFactory.create_batch(15)
        TaskGradesFactory.create_batch(20)
        FeedbackFactory.create_batch(10)
        # GradeHistoryFactory.create_batch(10)
        StudentExamsFactory.create_batch(15)
        ExamExercisesFactory.create_batch(10)
        ExamQuestionsFactory.create_batch(20)
        StudentExerciseAttemptsFactory.create_batch(15)
        StudentQuestionAttemptsFactory.create_batch(15)
        # TODO generate assignment units
        # todo: generate comments
        for assignment in Assignment.objects.all():
            # Choose a random number of comments to add, between 0 and 5
            number_of_comments_to_add = random.randint(0, 5)

            # Generate the specified number of comments and link them to the current assignment
            for _ in range(number_of_comments_to_add):
                CommentFactory(content_object=assignment)


        self.stdout.write(self.style.SUCCESS('Successfully populated the database.'))
