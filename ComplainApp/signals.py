from django.db.models.signals import post_save, post_delete,pre_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
import string
import pandas as pd
from .models import Complains  
from django.contrib.auth.models import User
from .models import Profile,AdminActivity
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone

# Genereate Random 10 digit ack number
@receiver(pre_save, sender=Complains)
def set_ack_number(sender, instance, **kwargs):
    if not instance.ack_number:
        unique_ack = False
        while not unique_ack:
            ack_number = get_random_string(length=10, allowed_chars=string.ascii_uppercase + string.digits)
            if not Complains.objects.filter(ack_number=ack_number).exists():
                unique_ack = True
                instance.ack_number = ack_number

# Creating and updating users                
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

# Grab IP Address of user loggedin 
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]  
    else:
        ip_address = request.META.get('REMOTE_ADDR', '') 
    AdminActivity.objects.create(
        user=user,
        login_time=timezone.now(),
        ip_address=ip_address
    )