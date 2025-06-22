"""
WSGI config for piiscan_frontend project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piiscan_frontend.settings')

application = get_wsgi_application()