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




# --------------Unused Utils-------------

    # current_session_key = user.profile.session_keys[-1]  # get the latest session key
    # all_sessions = Session.objects.filter(expire_date__gte=timezone.now())

    # for session in all_sessions:
    #     if session.session_key != current_session_key and session.get_decoded().get('_auth_user_id') == str(user.id):
    #         session.delete()

# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
# from django.conf import settings

    # def send_otp_via_email(email, otp):
#     message = Mail(
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         to_emails=email,
#         subject='Your OTP Code',
#         plain_text_content=f'Your OTP code is {otp}'
#     )
#     try:
#         sg = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)
#         response = sg.send(message)
#         print(response.status_code)
#         print(response.body)
#         print(response.headers)
#     except Exception as e:
#         print(e)