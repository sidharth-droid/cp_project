from django.db import models
from multiselectfield import MultiSelectField
from django.contrib.auth.models import User
# Create your models here.

Fraud_Type_Choices = [
    ('investment_scam','Investment Scam'),
    ('fake_social_media','Fake Social Media'),
    ('credit_card_scam','Credit Card Scam'),
    ('fake_loan_scam','Fake Loan Scam'),
    ('crypto_scam','Cryptocurrency Scam'),
    ('hacking','Hacking'),
    ('sextortion','Sextortion'),
    ('defamation','Defamation'),
    ('custom','Custom')
]
class Complains(models.Model):
    ack_number = models.CharField(max_length=20,primary_key=True)
    mobile_number = models.TextField(help_text="Enter Mobile Numbers")
    name = models.CharField(max_length=255)
    address = models.TextField(help_text="Enter Address",blank=True)
    email = models.EmailField(blank=True, null=True)
    # fraud_type = MultiSelectField(choices=Fraud_Type_Choices,max_choices=9)
    fraud_type = models.TextField(help_text="Enter Type of Fraud")
    # custom_fraud_type = models.CharField(max_length=255, blank=True, null=True)
    steps_taken = models.TextField(blank=True,null=True)
    images_videos = models.FileField(upload_to='case_files/', blank=True, null=True)
    status = models.CharField(max_length=50, default='Pending')
    investigating_officer = models.CharField(max_length=255,blank=True,null=True)

    def __str__(self):
        return f'{self.ack_number}-{self.name}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_keys = models.JSONField(default=list, blank=True)

class AdminActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"