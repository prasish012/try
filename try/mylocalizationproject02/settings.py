# settings.py
import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-%kzv7eni0hy6j0duzjfx(6#jqz_9(*00ar6lj$cwka!-bk=s5e"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'wptranslate.org',
    'www.wptranslate.org',
    '88.222.241.110',
]

# CSRF protection for custom domains
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1',
    'http://localhost',
    'http://wptranslate.org',
    'https://wptranslate.org',
    'http://www.wptranslate.org',
    'https://www.wptranslate.org',
]

# ====================== IMPORTANT FIX FOR TOO MANY FIELDS ======================
# This fixes the error: "TooManyFieldsSent" when saving large PO files
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000      # Increased from default 1000
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB (helps with large forms)
# =============================================================================

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "localizationtool",
    "modeltranslation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'mylocalizationproject02.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = 'mylocalizationproject02.wsgi.application'

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_copy.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = 'en-us'

LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
    ('de', _('German')),
    ('fr', _('French')),
    ('pt', _('Portuguese')),
    ('hi', _('Hindi')),
    ('ne', _('Nepali')),
    ('ar', _('Arabic')),
    ('it', _('Italian')),
    ('ja', _('Japanese')),
    ('pl', _('Polish')),
    ('ru', _('Russian')),
    ('nl', _('Dutch')),
    ('id', _('Indonesian')),
    ('th', _('Thai')),
    ('tl', _('Filipino')),
    ('ko', _('Korean')),
    ('en-gb', _('English (UK)')),
    ('sw', _('Swahili')),
    ('da', _('Danish')),
    ('fi', _('Finnish')),
    ('is', _('Icelandic')),
    ('no', _('Norwegian')),
    ('sv', _('Swedish')),
    ('zh-hans', _('Chinese (Simplified)')),
)

TIME_ZONE = 'Asia/Kathmandu'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Important for .mo files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "localizationtool" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media_copy"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login/Logout redirect
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'