from django.contrib.sessions.models import Session
from django.utils import timezone

def invalidate_previous_sessions(user):
    session_keys = user.profile.session_keys if user.profile.session_keys else []
    
    if not session_keys:
        return
    
    current_session_key = session_keys[-1]  # Safely get the latest session key
    all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    for session in all_sessions:
        session_data = session.get_decoded()
        if session.session_key != current_session_key and session_data.get('_auth_user_id') == str(user.id):
            session.delete()