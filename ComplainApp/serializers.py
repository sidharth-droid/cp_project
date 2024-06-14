from rest_framework import serializers
from .models import Complains

class ComplainsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complains
        fields = ('ack_number','mobile_number','name','email','fraud_type','steps_taken','status')