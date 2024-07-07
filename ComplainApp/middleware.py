# middleware.py
from django.contrib.sessions.models import Session
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Profile,AdminActivity
from django.urls import reverse
from django.shortcuts import redirect

class SingleSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                profile = request.user.profile
                user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
                user_sessions = [s for s in user_sessions if s.get_decoded().get('_auth_user_id') == str(request.user.id)]

                if len(user_sessions) > 1:
                    for session in user_sessions:
                        if session.session_key != request.session.session_key:
                            session.delete()

                if request.session.session_key not in profile.session_keys:
                    profile.session_keys.append(request.session.session_key)
                    profile.save()
                # if not self.is_session_valid(request):
                #     return redirect(reverse('session_invalidated'))
            except Profile.DoesNotExist:
                pass

        response = self.get_response(request)
        return response
    def is_session_valid(self, request):
        """Check if the session key is in the user's profile session keys."""
        return request.session.session_key in request.user.profile.session_keys

