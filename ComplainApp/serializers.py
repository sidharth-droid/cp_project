from rest_framework import serializers
from .models import Complains,FIR

class FIRSerializer(serializers.ModelSerializer):
    class Meta:
        model=FIR
        fields = '__all__'

class ComplainsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complains
        fields = ('ack_number','mobile_number','name','email','fraud_type','description','accusedAccountNumbers','accusedSuspiciousItem','steps_taken','status','files')
        read_only_fields = ['ack_number']





# --------Unused Serializers-------------


# fields = ('ack_number','mobile_number','name','email','fraud_type','steps_taken','status')

# class LinkSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ScamLink
#         fields = ('url','status','details','complaints')
# class PhoneSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ScamPhone
#         fields = ('number','status','details','complaints')
# class EmailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ScamEmail
#         fields = ('email','status','details','complaints')