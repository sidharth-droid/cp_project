from rest_framework import serializers
from .models import Complains,FIR

class FIRSerializer(serializers.ModelSerializer):
    class Meta:
        model=FIR
        fields = '__all__'

class ComplainsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complains
        fields = ('ack_number','mobile_number','name','address','email','fraud_type','description','fraudlent_amount','suspect_account_numbers','suspect_emails','suspect_links','suspect_mobile_numbers','steps_taken','status','files')
        read_only_fields = ['ack_number']

