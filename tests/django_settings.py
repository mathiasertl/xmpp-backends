# Basic django settings

# It's an error if the next version is already broken
import warnings
from django.utils import deprecation  # NOQA
warnings.filterwarnings('error', category=deprecation.RemovedInNextVersionWarning)  # NOQA
warnings.filterwarnings('always', category=deprecation.RemovedInDjango30Warning)  # NOQA

DEBUG = True
SECRET_KEY = 'dummy'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'xmpp_backends.django.fake_xmpp',
]
