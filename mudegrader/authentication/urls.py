from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import RedirectView

from .views import login_view, logout_view

urlpatterns = [
    path('', login_required(RedirectView.as_view(pattern_name='course_list')), name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]