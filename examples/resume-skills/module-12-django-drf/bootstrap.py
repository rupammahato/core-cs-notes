import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.core.management import call_command
from fixtures import seed

def prepare():
    call_command('migrate',verbosity=0,interactive=False)
    seed()
