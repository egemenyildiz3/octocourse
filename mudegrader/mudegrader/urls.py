"""
URL configuration for mudegrader project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from assignment_manager.views.comments import delete_comment

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import path, re_path
import os
# from assignment_manager.views import delete_comment
from authentication import views
from authentication.views import privacy_policy, custom_404
from assignment_manager.views.comments import delete_comment

# NOTE: urlpatterns uses a fall-through system, the order of urls matters!
urlpatterns = [
    path('comments/delete/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('', include('authentication.urls')),
    path('admin/', admin.site.urls),
    path('grading/', include('graderandfeedbacktool.urls')),
    path('analytics/', include('analytics.urls')),
    path('', include('assignment_manager.urls')),
    path('privacy_policy/', privacy_policy, name='privacy_policy'),
]

handler404 = 'authentication.views.custom_404'

# Serve static files from the 'submissions' directory
urlpatterns += [
    re_path(r'^app/project_files/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
    

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
