from django.shortcuts import render
from rest_framework import generics
from .models import Complains
from .serializers import ComplainsSerializer
import requests
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from .utils import invalidate_previous_sessions

class ComplainsList(generics.ListAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
class ComplaintDetail(generics.RetrieveAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            invalidate_previous_sessions(user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def truecaller_bot_view(request):
    if request.method == "POST":
        message = request.POST.get("message")
        if message:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID  # This should be customized
            send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            response = requests.post(send_message_url, data={
                'chat_id': chat_id,
                'text': message
            })
            
            if response.status_code == 200:
                # Message sent successfully
                pass

        return HttpResponseRedirect(reverse('truecaller-bot'))

    context = {
        'bot_token': settings.TELEGRAM_BOT_TOKEN,
        'chat_id': settings.TELEGRAM_CHAT_ID,
    }
    return render(request, 'admin/truecaller_bot.html', context)