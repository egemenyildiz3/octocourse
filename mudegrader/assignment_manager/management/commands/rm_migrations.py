from django.core.management.base import BaseCommand
import subprocess

class Command(BaseCommand):
    help = 'Deletes migrations starting with 0'

    def handle(self, *args, **options):

        command = "find . -path /app/assignment_manager/migrations/0*' -type d -exec rm -rv {} +"
        command2 = "sudo find . -path '/app/gitlabmanager/migrations/0..*' -type d -exec rm -rv {} +"
        command3 = "sudo find . -path '/app/graderandfeedbacktool/migrations/0..*' -type d -exec rm -rv {} +"
        try: 
            subprocess.run(command, shell=True, check=True)
            subprocess.run(command2, shell=True, check=True)
            subprocess.run(command3, shell=True, check=True)
            self.stdout.write(self.style.SUCCESS('Successfully deleted migrations'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Error running command: {e}'))
