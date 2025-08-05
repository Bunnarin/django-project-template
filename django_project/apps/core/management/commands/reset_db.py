import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import subprocess

class Command(BaseCommand):
    help = 'Reset the database and migrations to a clean state'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false',
            dest='interactive',
            help='Tells Django to NOT prompt the user for input of any kind.',
        )
        parser.add_argument(
            '--no-superuser',
            action='store_true',
            help='Skip creating a superuser after resetting the database.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('WARNING: This will delete your database and all migration files!'))
        
        if options['interactive']:
            confirm = input('Are you sure you want to continue? [y/N] ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        # Get database info from settings
        db = settings.DATABASES['default']
        db_name = db['NAME']
        db_engine = db['ENGINE']

        # Drop and recreate database based on engine
        if 'sqlite3' in db_engine:
            self._handle_sqlite(db_name)
        elif 'postgresql' in db_engine:
            self._handle_postgresql(db, db_name, options)
        else:
            raise CommandError(f'Unsupported database engine: {db_engine}')

        # Delete all migration files
        self._delete_migrations()

        # Run migrations
        self._run_migrations()

        # Create superuser if requested
        if not options['no_superuser'] and options['interactive']:
            self.stdout.write(self.style.SUCCESS('\nCreating superuser...'))
            subprocess.call(['python', 'manage.py', 'createsuperuser'], env=os.environ.copy())

    def _handle_sqlite(self, db_name):
        """Handle SQLite database reset."""
        self.stdout.write(self.style.SUCCESS(f'Deleting SQLite database: {db_name}'))
        if os.path.exists(db_name):
            os.remove(db_name)

    def _handle_postgresql(self, db_config, db_name, options):
        """Handle PostgreSQL database reset."""
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        # Create a clean connection parameters dict with only the parameters psycopg2 expects
        conn_params = {
            'host': db_config.get('HOST', 'localhost'),
            'port': db_config.get('PORT', '5432'),
            'user': db_config.get('USER'),
            'password': db_config.get('PASSWORD'),
            'dbname': 'postgres'  # Connect to default postgres DB first
        }
        
        # Add any additional options if they exist
        if 'OPTIONS' in db_config and 'options' in db_config['OPTIONS']:
            conn_params['options'] = db_config['OPTIONS']['options']

        self.stdout.write(self.style.SUCCESS(f'Dropping database: {db_name}'))
        try:
            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                # Terminate all connections to the database
                cursor.execute(
                    sql.SQL("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid();
                    """), [db_name])
                
                # Drop the database if it exists
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}")
                    .format(sql.Identifier(db_name))
                )
                
                # Create a new database
                self.stdout.write(self.style.SUCCESS(f'Creating database: {db_name}'))
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}")
                    .format(sql.Identifier(db_name))
                )
        except Exception as e:
            raise CommandError(f'Error resetting PostgreSQL database: {e}')
        finally:
            if 'conn' in locals() and conn is not None:
                conn.close()

    def _delete_migrations(self):
        """Delete all migration files except __init__.py."""
        project_dir = settings.PROJECT_DIR
        migrations_dirs = []
        
        # Find all migrations directories
        for root, dirs, _ in os.walk(project_dir):
            if 'migrations' in dirs:
                migrations_dir = os.path.join(root, 'migrations')
                migrations_dirs.append(migrations_dir)
        
        # Delete migration files
        for migrations_dir in migrations_dirs:
            self.stdout.write(self.style.SUCCESS(f'Processing migrations in: {migrations_dir}'))
            for item in os.listdir(migrations_dir):
                item_path = os.path.join(migrations_dir, item)
                if item == '__init__.py':
                    continue
                if item == '__pycache__':
                    shutil.rmtree(item_path, ignore_errors=True)
                elif item.endswith('.py'):
                    os.remove(item_path)
                    self.stdout.write(f'  Deleted: {item}')
        
        # Delete any .pyc files
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))

    def _run_migrations(self):
        """Run makemigrations and migrate."""
        self.stdout.write(self.style.SUCCESS('\nRunning migrations...'))
        subprocess.call(['python', 'manage.py', 'makemigrations'], env=os.environ.copy())
        subprocess.call(['python', 'manage.py', 'migrate'], env=os.environ.copy())
