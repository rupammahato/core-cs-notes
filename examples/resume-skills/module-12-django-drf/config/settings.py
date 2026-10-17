from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'public-local-teaching-key-not-for-deployment'
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1','localhost','testserver']
INSTALLED_APPS = ['django.contrib.auth','django.contrib.contenttypes',
                  'django.contrib.sessions','rest_framework','work']
MIDDLEWARE = ['work.middleware.CorrelationMiddleware',
              'django.contrib.sessions.middleware.SessionMiddleware',
              'django.middleware.csrf.CsrfViewMiddleware',
              'django.contrib.auth.middleware.AuthenticationMiddleware']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3',
                        'NAME': os.environ['M12_DATABASE'], 'OPTIONS':{'timeout':5}}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = 'UTC'
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES':['work.authentication.FixtureBearer'],
                  'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'],
                  'DEFAULT_PARSER_CLASSES':['rest_framework.parsers.JSONParser'],
                  'DEFAULT_RENDERER_CLASSES':['rest_framework.renderers.JSONRenderer']}
DATA_UPLOAD_MAX_MEMORY_SIZE = 16384
SESSION_COOKIE_HTTPONLY = True
LOGGING = {'version':1,'disable_existing_loggers':False,
           'handlers':{'null':{'class':'logging.NullHandler'}},
           'loggers':{'django.request':{'handlers':['null'],'propagate':False},
                      'django.server':{'handlers':['null'],'propagate':False}}}
