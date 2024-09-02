from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """
    Middleware that ensures a user is logged in to access any page.
    Exemptions to this requirement can be specified in settings.py.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        assert hasattr(request, 'user'), (
            "The Login Required middleware requires authentication middleware to be installed.")

        if not request.user.is_authenticated:
            exempt_urls = [reverse(url) for url in getattr(settings, 'LOGIN_EXEMPT_URLS', [])]

            if request.path not in exempt_urls and not request.path.startswith(reverse('admin:index')):
                return redirect(settings.LOGIN_URL)
        else:
            if request.path == reverse('login'):
                return redirect('course_list')

        return None
