from django.db import models
from multiselectfield import MultiSelectField
from django.contrib.auth.models import User


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
    Date = models.DateTimeField(auto_now_add=True)
    ack_number = models.CharField(max_length=20,primary_key=True)
    mobile_number = models.TextField(help_text="Enter Mobile Numbers")
    name = models.CharField(max_length=255)
    address = models.TextField(help_text="Enter Address",blank=True)
    email = models.EmailField(blank=True, null=True)
    # fraud_type = MultiSelectField(choices=Fraud_Type_Choices,max_choices=9)
    fraud_type = models.TextField(help_text="Enter Type of Fraud")
    # custom_fraud_type = models.CharField(max_length=255, blank=True, null=True)
    steps_taken = models.TextField(blank=True,null=True)
    # images_videos = models.FileField(upload_to='case_files/', blank=True, null=True)
    status = models.CharField(max_length=50, default='Pending',choices=[('open','Open'),('in review','In Review'),('visit ps','Visit Police Station'),('in progress','In Progress'),('closed','Closed (Reach out to Police Station)')])
    investigating_officer = models.CharField(max_length=255,blank=True,null=True)

    def __str__(self):
        return f'{self.ack_number}-{self.name}'
class FIR(models.Model):
    complain = models.OneToOneField(Complains, on_delete=models.CASCADE, primary_key=True, related_name='fir')
    date = models.DateTimeField()
    fir_number = models.CharField(max_length=20)
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






class Attachment(models.Model):
    complain = models.ForeignKey(Complains, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='case_files/')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Attachment for {self.complain.ack_number}'
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_keys = models.JSONField(default=list, blank=True)

class AdminActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
    
class ScamPhone(models.Model):
    number = models.CharField(max_length=30,unique=True,db_index=True)
    status = models.CharField(max_length=60,choices=[('confirmed',"Confirmed"),('unconfirmed','Unconfirmed')])
    details = models.TextField(blank=True,null=True)
    complaints = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.number
class ScamLink(models.Model):
    url = models.CharField(max_length=255, unique=True,db_index=True)
    status = models.CharField(max_length=60,choices=[('confirmed',"Confirmed"),('unconfirmed','Unconfirmed')])
    details = models.TextField(blank=True,null=True)
    complaints = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.url
class ScamEmail(models.Model):
    email = models.EmailField(max_length=255, unique=True,db_index=True)
    status = models.CharField(max_length=60,choices=[('confirmed',"Confirmed"),('unconfirmed','Unconfirmed')])
    details = models.TextField(blank=True,null=True)
    complaints = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.email