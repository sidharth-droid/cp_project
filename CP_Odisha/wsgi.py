"""
WSGI config for CP_Odisha project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import dotenv,pathlib
from django.core.wsgi import get_wsgi_application


CURRENT_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ENV_PATH = BASE_DIR / '.env'
dotenv.read_dotenv(str(ENV_PATH))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CP_Odisha.settings')

application = get_wsgi_application()
