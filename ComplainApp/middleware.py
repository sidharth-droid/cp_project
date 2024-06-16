# middleware.py
from django.contrib.sessions.models import Session
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Profile,AdminActivity


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
            except Profile.DoesNotExist:
                pass

        response = self.get_response(request)
        return response



# class UserActivityMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Comment out or remove this logging logic if using signals.
#         if request.user.is_authenticated:
#             ip_address = request.META.get('REMOTE_ADDR', '')
#             AdminActivity.objects.create(
#                 user=request.user,
#                 login_time=timezone.now(),
#                 ip_address=ip_address
#             )

#         response = self.get_response(request)
#         return response