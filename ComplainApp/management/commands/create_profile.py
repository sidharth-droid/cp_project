from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ComplainApp.models import Profile

class Command(BaseCommand):
    help = 'Creates missing profiles for existing users'

    def handle(self, *args, **options):
        for user in User.objects.all():
            Profile.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS('Profiles created successfully'))
