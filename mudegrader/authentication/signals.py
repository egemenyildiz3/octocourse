from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import LoginEvent


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    """
    Signal receiver that logs user login events.

    This function is triggered whenever a user logs in. It captures the user's IP address
    and user agent (browser details) from the request and logs these details in the LoginEvent model.
    """
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '<unknown>')

    LoginEvent.objects.create(user=user, ip_address=ip_address, user_agent=user_agent)
