from django.shortcuts import render
from rest_framework import generics
from .models import Complains
from .serializers import ComplainsSerializer

class ComplainsList(generics.ListAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
class ComplaintDetail(generics.RetrieveAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
