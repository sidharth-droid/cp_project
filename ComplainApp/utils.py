from django.contrib.sessions.models import Session
from django.utils import timezone

def invalidate_previous_sessions(user):
    current_session_key = user.profile.session_keys[-1]  # get the latest session key
    all_sessions = Session.objects.filter(expire_date__gte=timezone.now())

    for session in all_sessions:
        if session.session_key != current_session_key and session.get_decoded().get('_auth_user_id') == str(user.id):
            session.delete()
