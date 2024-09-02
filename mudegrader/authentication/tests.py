from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from authentication.models import CustomUser, LoginEvent, Role
from assignment_manager.models import Course
from authentication.forms import LoginForm, CustomUserChangeForm, CustomUserCreationForm


class LoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('login')
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = CustomUser.objects.create_user(username='testuser', password='testpassword')

    def test_login_view_get(self):
        """Test GET request to the login view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertContains(response, 'Login')

    def test_login_view_post_valid_credentials(self):
        """Test the login view with a POST request and valid credentials."""
        response = self.client.post(self.url, {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['login_success'])
        self.assertTemplateUsed(response, 'login.html')

    def test_login_view_post_invalid(self):
        """Test POST request with invalid credentials."""
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertContains(response, 'Invalid username or password')

    def test_login_view_already_logged_in(self):
        """Test the login view when the user is already logged in."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """Test the logout view."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_event_created(self):
        """Test that a LoginEvent is created when a user logs in."""
        self.client.post(self.url, {
            'username': self.username,
            'password': self.password
        })
        self.assertTrue(self.user.loginevent_set.exists())
        self.assertEqual(self.user.loginevent_set.first().user, self.user)


class CustomUserModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER,
            email='testuser@example.com',
            gitlab_id=123456,
        )
        self.user.set_password('testpassword')
        self.client.login(username='testuser', password='testpassword')

        self.course = Course.objects.create(
            course_code='CS101',
            description='Introduction to Computer Science',
            start_year=2021,
            end_year=2022,
            department='Computer Science',
            created_by=self.user
        )
        self.user.courses.add(self.course)

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.is_teacher)
        self.assertFalse(self.user.is_ta)
        self.assertIn(self.course, self.user.courses.all())

    def test_user_roles(self):
        self.user.role = 'Teaching Assistant'
        self.user.save()
        self.assertTrue(self.user.is_ta)
        self.assertFalse(self.user.is_teacher)


class LoginEventModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='loginuser',
            email='loginuser@example.com',
            password='password123'
        )

    def test_login_event_creation(self):
        login_event = LoginEvent.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )
        self.assertEqual(login_event.user.username, 'loginuser')
        self.assertEqual(login_event.ip_address, '192.168.1.1')
        self.assertEqual(login_event.user_agent, 'Mozilla/5.0')


User = get_user_model()


class CustomUserCreationFormTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER,
            email='testuser@example.com',
            gitlab_id=123456,
        )
        # Create a course for testing
        self.course = Course.objects.create(
            course_code='CS101',
            description='Introduction to Computer Science',
            start_year=2021,
            end_year=2022,
            department='Computer Science',
            created_by=self.user
        )

    def test_valid_form(self):
        form = CustomUserCreationForm({
            'username': 'testsuser',
            'email': 'testuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'Teacher',
            'courses': [self.course.id]
        })
        self.assertTrue(form.is_valid())

    def test_invalid_form_password_mismatch(self):
        form = CustomUserCreationForm({
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass123',
            'role': 'Teacher',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_courses_field(self):
        form = CustomUserCreationForm({
            'username': 'testusser',
            'email': 'testuser@example.com',
            'password1': 'arabaaaaaaaaa123123421',
            'password2': 'arabaaaaaaaaa123123421',
            'role': 'Teacher',
            'courses': [self.course.id]
        })
        self.assertTrue(form.is_valid())
        self.assertIn(self.course, form.cleaned_data['courses'])


class CustomUserChangeFormTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER,
            email='testuser@example.com',
            gitlab_id=123456,
        )
        # Create a course for testing
        self.course = Course.objects.create(
            course_code='CS101',
            description='Introduction to Computer Science',
            start_year=2021,
            end_year=2022,
            department='Computer Science',
            created_by=self.user
        )

    def test_valid_form(self):
        form = CustomUserChangeForm({
            'username': self.user.username,
            'email': self.user.email,
            'role': 'Teacher',
            'courses': [self.course.id]
        }, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_courses_field(self):
        form = CustomUserChangeForm({
            'username': self.user.username,
            'email': self.user.email,
            'role': 'Teacher',
            'courses': [self.course.id]
        }, instance=self.user)
        self.assertTrue(form.is_valid())
        self.assertIn(self.course, form.cleaned_data['courses'])


class LoginFormTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword',
            role=Role.TEACHER,
            email='testuser@example.com',
            gitlab_id=123456,
        )

    def test_valid_login_with_username(self):
        form = LoginForm({
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertTrue(form.is_valid())

    def test_valid_login_with_email(self):
        form = LoginForm({
            'username': 'testuser@example.com',
            'password': 'testpass123'
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], 'testuser')

    def test_invalid_login(self):
        form = LoginForm({
            'username': 'invaliduser',
        })
        self.assertFalse(form.is_valid())
