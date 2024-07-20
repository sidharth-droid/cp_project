from rest_framework import serializers
from .models import Complains
class ComplainsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complains
        fields = ('ack_number','mobile_number','name','address','email','place_of_incidence','fraud_type','description','fraudlent_amount','suspect_account_numbers','suspect_emails','suspect_links','suspect_mobile_numbers','steps_taken','message','status','files','upload_status')
        read_only_fields = ['ack_number']

