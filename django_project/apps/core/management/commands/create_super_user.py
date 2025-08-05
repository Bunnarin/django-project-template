from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from decouple import config
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(email=config('SUPERUSER_EMAIL')).exists():
            admin_grp, _ = Group.objects.get_or_create(name="ADMIN")
            admin = User.objects.create_superuser(
                username="admin",
                email=config('SUPERUSER_EMAIL'),
            )
            admin.groups.set([admin_grp])
            admin.save()            