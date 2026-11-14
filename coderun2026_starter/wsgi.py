

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coderun2026_starter.settings')

application = get_wsgi_application()
