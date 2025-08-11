# myapp/management/commands/run_shell_script.py
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Runs backup.sh to backup postgres (to be called by django crontab)'

    def handle(self, *args, **options):
        script_path = settings.BASE_DIR / 'backup.sh'

        try:
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                check=True,
                shell=False
            )
            self.stdout.write(self.style.SUCCESS(f'Script executed successfully: {script_path}'))
            if result.stdout:
                self.stdout.write(f'STDOUT:\n{result.stdout}')
            if result.stderr:
                self.stderr.write(f'STDERR:\n{result.stderr}')

        except subprocess.CalledProcessError as e:
            raise CommandError(f'Error executing script: {script_path}\n'
                                f'Return Code: {e.returncode}\n'
                                f'STDOUT: {e.stdout}\n'
                                f'STDERR: {e.stderr}')
        except FileNotFoundError:
            raise CommandError(f'Script not found: {script_path}')
        except Exception as e:
            raise CommandError(f'An unexpected error occurred: {e}')