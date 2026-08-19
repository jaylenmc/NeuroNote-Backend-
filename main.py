import os 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NeuroNote.settings")

import django
django.setup()

from django.conf import settings
print("==================== Local Railway Variables Test =================")

print(f"DEBUG: {settings.DEBUG}")
print(f"DEBUG: {type(settings.DEBUG)}")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")