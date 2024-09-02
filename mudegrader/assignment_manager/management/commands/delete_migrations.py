import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Deletes migration files from specified directories'

    def handle(self, *args, **kwargs):
        # Determine the base directory of the project
        base_dir = settings.BASE_DIR
        
        migration_paths = [
            os.path.join(base_dir, 'assignment_manager', 'migrations'),
            os.path.join(base_dir, 'gitlabmanager', 'migrations'),
            os.path.join(base_dir, 'graderandfeedbacktool', 'migrations'),
        ]

        for path in migration_paths:
            # Use glob to match all .py files except __init__.py
            files = glob.glob(os.path.join(path, '*.py'))
            for file in files:
                if not file.endswith('__init__.py'):
                    os.remove(file)
                    self.stdout.write(self.style.SUCCESS(f'Successfully deleted {file}'))
            
            # Also remove the .pyc files in the __pycache__ directory if it exists
            pycache_path = os.path.join(path, '__pycache__')
            if os.path.exists(pycache_path):
                pycache_files = glob.glob(os.path.join(pycache_path, '*.pyc'))
                for file in pycache_files:
                    os.remove(file)
                    self.stdout.write(self.style.SUCCESS(f'Successfully deleted {file}'))

        self.stdout.write(self.style.SUCCESS('All specified migration files have been deleted.'))
