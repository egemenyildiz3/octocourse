import random
import factory
from django.utils import timezone
from assignment_manager.models import Student, Comment, Course, Group, Assignment, AssignmentUnit, GroupMember,Tasks
from assignment_manager.tag_model import Tag
from django.contrib.contenttypes.models import ContentType
from authentication.models import CustomUser, Role


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    author = factory.LazyAttribute(lambda _: random.choice(CustomUser.objects.all()))
    comment_text = factory.Faker('text')
    comment_time = factory.Faker('date_time_this_year')
    content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object))
    object_id = factory.SelfAttribute('content_object.id')


class CommentableFactory(factory.django.DjangoModelFactory):
    @factory.post_generation
    def add_comments(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for comment in extracted:
                CommentFactory(content_object=self, comment_text=comment)


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course

    course_code = factory.Sequence(lambda n: f"CS{n:03d}")
    description = factory.Faker('text')
    start_year = factory.Faker('year')
    end_year = factory.LazyAttribute(lambda o: str(int(o.start_year) + 4))
    department = factory.Iterator(['Computer Science', 'Mathematics', 'Physics'])
    gitlab_subgroup_id = factory.Faker('random_int', min=0, max=9999)

    @factory.lazy_attribute
    def created_by(self):
        # Ensure the Teacher user exists
        teacher = CustomUser.objects.filter(role=Role.TEACHER).first()
        if not teacher:
            teacher = CustomUser.objects.create_user(
                username='Teacher',
                password='teacher123',
                first_name='Otto',
                last_name='Visser',
                email='teacher@tudelft.com',
                is_staff=True,
                role=Role.TEACHER
            )

        # Ensure the TA user exists
        ta = CustomUser.objects.filter(role=Role.TA).first()
        if not ta:
            ta = CustomUser.objects.create_user(
                username='TA',
                password='ta123',
                first_name='Aleksandra',
                last_name='Jach',
                email='ta@tudelft.com',
                is_staff=True,
                role=Role.TA
            )

        # Ensure the Admin user exists
        admin = CustomUser.objects.filter(is_superuser=True).first()
        if not admin:
            admin = CustomUser.objects.create_user(
                username='root',
                password='123',
                first_name='Admin',
                last_name='User',
                email='admin@example.com',
                is_staff=True,
                is_superuser=True
            )

        return teacher

    @factory.post_generation
    def add_staff(self, create, extracted, **kwargs):
        if not create:
            return

        # Add Teacher to staff
        teacher = CustomUser.objects.filter(role=Role.TEACHER).first()
        if teacher:
            self.staff.add(teacher)

        # Optionally add TA to staff if needed
        ta = CustomUser.objects.filter(role=Role.TA).first()
        if ta:
            self.staff.add(ta)


class StudentFactory(CommentableFactory):
    class Meta:
        model = Student

    net_id = factory.Sequence(lambda n: f"{n}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda o: f"{o.first_name}.{o.last_name}@university.edu".lower())
    enrollment_year = factory.Faker('year')
    program = factory.Iterator(['Undergraduate', 'Masters', 'PhD', 'Postdoc'])
    msc_track = factory.Sequence(lambda n: f"Track{n % 5}")
    self_assessed_skill = factory.Iterator(['Beginner', 'Intermediate', 'Advanced'])
    nationality_type = factory.Faker('country')
    start_year_in_mude = factory.Faker('year')
    brightspace_id = factory.Sequence(lambda n: f"bspace{n}")
    gitlab_id = factory.Sequence(lambda n: f"git{n}")
    public_ssh_key = factory.Faker('sha256')

    @factory.post_generation
    def courses_enrolled(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for course in extracted:
                self.courses_enrolled.add(course)
        else:
            all_courses = list(Course.objects.all())
            selected_courses = random.sample(all_courses, k=random.randint(1, len(all_courses)))
            self.courses_enrolled.set(selected_courses)


class AssignmentFactory(CommentableFactory):
    class Meta:
        model = Assignment

    course = factory.LazyAttribute(lambda _: random.choice(Course.objects.all()))
    title = factory.Faker('slug')
    description = factory.Faker('paragraph')
    start_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=1))
    due_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))
    total_points = factory.Faker('random_int', min=10, max=100)
    is_published = factory.Faker('boolean')
    gitlab_subgroup_id = factory.Faker('random_int', min=0, max=9999)
    is_individual = factory.Faker('boolean')


class GroupFactory(CommentableFactory):
    class Meta:
        model = Group

    name = factory.Faker('company')
    creation_date = factory.LazyFunction(timezone.now)
    course = factory.LazyAttribute(lambda _: random.choice(Course.objects.all()))

    @factory.post_generation
    def add_assignments(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for assignment in extracted:
                self.assignments.add(assignment)
        else:
            all_assignments = list(Assignment.objects.all())
            selected_assignments = random.sample(all_assignments, k=random.randint(1, len(all_assignments)))
            self.assignments.set(selected_assignments)


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker('slug')
    course = factory.LazyAttribute(lambda _: random.choice(Course.objects.all()))



class GroupMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupMember

    student_id = factory.LazyAttribute(lambda _: random.choice(Student.objects.all()) if Student.objects.exists() else StudentFactory())
    group_id = factory.LazyAttribute(lambda _: random.choice(Group.objects.all()) if Group.objects.exists() else GroupFactory())
    join_date = factory.LazyFunction(timezone.now)
    leave_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))


class AssignmentUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AssignmentUnit

    name = factory.Faker('sentence')
    assignment = factory.LazyAttribute(lambda o: AssignmentFactory())
    file = factory.django.FileField(filename="example.txt")
    type = factory.Iterator(['master', 'non_master'])
    total_points = factory.Faker('random_int', min=10, max=100)


class TasksFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tasks

    assignment_unit = factory.LazyAttribute(lambda _: random.choice(AssignmentUnit.objects.all()))
    question_text = factory.Faker('text')
    question_path = factory.Faker('file_path')
    max_score = factory.Faker('random_int', min=1, max=100)
