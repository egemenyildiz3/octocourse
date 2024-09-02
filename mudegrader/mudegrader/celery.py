import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mudegrader.settings")
# Create default Celery app
app = Celery('mudegrader')


# namespace='CELERY' means all celery-related configuration keys
# should be uppercased and have a `CELERY_` prefix in Django settings.
# https://docs.celeryproject.org/en/stable/userguide/configuration.html
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_default_queue = 'mude-exec-queue'
app.conf.beat_scheduler = 'django_celery_beat.schedulers.DatabaseScheduler'
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_max_retries = 10


# When we use the following in Django, it loads all the <appname>.tasks
# files and registers any tasks it finds in them. We can import the
# tasks files some other way if we prefer.
app.autodiscover_tasks([
    'gitlabmanager',
])


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))