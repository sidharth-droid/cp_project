from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import pandas as pd
from .models import Complains  
from django.contrib.auth.models import User
from .models import Profile,AdminActivity
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
file_path = 'D:\Documents\sidharth\cp_cell\Exports.xlsx'

def export_to_excel():
  
    data = Complains.objects.all().values()  

    df = pd.DataFrame(data)

    df.to_excel(file_path, index=False, engine='openpyxl')
    print(f"Data exported to {file_path}")

@receiver(post_save, sender=Complains)
def model_saved(sender, instance, **kwargs):
    print("Model instance saved")
    export_to_excel()

@receiver(post_delete, sender=Complains)
def model_deleted(sender, instance, **kwargs):
    print("Model instance deleted")
    export_to_excel()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip_address = request.META.get('REMOTE_ADDR', '')
    AdminActivity.objects.create(
        user=user,
        login_time=timezone.now(),
        ip_address=ip_address
    )