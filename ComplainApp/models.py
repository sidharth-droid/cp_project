from django.db import models
from django.contrib.auth.models import User
import string
from django.utils.crypto import get_random_string
from django.utils import timezone
import random,hashlib

class Complains(models.Model):
    Date = models.DateTimeField(auto_now_add=True)
    ack_number = models.CharField(max_length=20,primary_key=True)
    mobile_number = models.TextField()
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True, null=True)
    place_of_incidence = models.TextField(blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    suspect_account_numbers = models.TextField(blank=True,null=True)
    suspect_emails = models.TextField(blank=True,null=True)
    suspect_links = models.TextField(blank=True,null=True)
    suspect_mobile_numbers = models.TextField(blank=True,null=True)
    fraud_type = models.TextField()
    steps_taken = models.TextField(blank=True,null=True)
    files = models.JSONField(blank=True,null=True,default=list)
    status = models.CharField(max_length=50, default='Verification Pending',choices=[('open','Open'),('in review','In Review'),('visit ps','Visit Police Station'),('in progress','In Progress'),('closed','Closed')])
    enquiry_officer = models.CharField(max_length=255,blank=True,null=True)
    fraudlent_amount = models.DecimalField(max_digits=20,decimal_places=2,default=0.00,blank=True)
    amount_recovered = models.DecimalField(max_digits=20,decimal_places=2,default=0.00,blank=True)
    message = models.TextField(blank=True,null=True)
    upload_status = models.BooleanField(default=False)
    close_date = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return f'{self.ack_number}-{self.name}--[{self.mobile_number}]'
    def save(self, *args, **kwargs):
        if not self.ack_number:
            unique_ack = False
            while not unique_ack:
                ack_number = get_random_string(length=10, allowed_chars=string.ascii_uppercase + string.digits)
                if not Complains.objects.filter(ack_number=ack_number).exists():
                    unique_ack = True
                    self.ack_number = ack_number
        if self.status == 'closed' and self.close_date is None:
            self.close_date = timezone.now()
        elif self.status != 'closed' and self.close_date is not None:
            self.close_date = None

        super(Complains, self).save(*args, **kwargs)


class FIR(models.Model):
    complain = models.ManyToManyField(Complains,related_name='firs')
    Date = models.DateTimeField(auto_now_add=True)
    fir_number = models.CharField(max_length=20)
    date_reported = models.DateTimeField(blank=True,null=True)
    place_of_occurrence = models.CharField(max_length=255,blank=True,null=True)
    distance = models.CharField(max_length=50,blank=True,null=True)
    direction = models.CharField(max_length=50,blank=True,null=True)
    date_of_dispatch_from_ps = models.DateTimeField(blank=True,null=True)
    name_of_complainant = models.CharField(max_length=255)
    residence_of_complainant = models.TextField(blank=True,null=True)
    name_of_accused = models.CharField(max_length=255,blank=True,null=True)
    residence_of_accused = models.TextField(blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    section = models.TextField(blank=True,null=True)
    steps_taken_by_io = models.TextField(blank=True,null=True)
    result_of_the_case = models.TextField()

    def __str__(self):
        return f'{self.fir_number} - {self.complain.name}'

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def generate_otp(self):
        OTP.objects.filter(user=self.user, is_active=True).update(is_active=False)
        raw_otp = str(random.randint(100000, 999999))
        self.otp_code = hashlib.sha256(raw_otp.encode()).hexdigest()
        self.save()
        return raw_otp

    def is_valid(self):
        expiration_time = timezone.now() - timezone.timedelta(minutes=5)
        return self.created_at > expiration_time and self.is_active
    def calculate_time_to_expiry(self):
        expiration_time = self.created_at + timezone.timedelta(minutes=5)
        return expiration_time - timezone.now()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    session_keys = models.JSONField(default=list, blank=True)

class AdminActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
    
