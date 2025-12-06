from pathlib import Path

from decouple import config
from django.core.management.utils import get_random_secret_key
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default=get_random_secret_key())

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(
    ","
)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS", default="http://localhost:8000"
).split(",")

INSTALLED_APPS = [
    "unfold",
    "modeltranslation",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "subscriptions",
    "education",
    "progress",
    "mentoring",
    "content",
    "communication",
    "translations",
    "fixture",
]

UNFOLD = {
    "SHOW_LANGUAGES": True,
    "LANGUAGES": {
        "navigation": [
            {
                "code": "en",
                "name": "English",
                "name_local": "English",
                "bidi": False,
            },
            {
                "code": "ru",
                "name": "Russian",
                "name_local": "Русский",
                "bidi": False,
            },
        ]
    },
    "SITE_HEADER": _("Bervinov Academy"),
    "SITE_ICON": {
        "light": lambda request: static("img/logo.ico"),
        "dark": lambda request: static("img/logo.ico"),
    },
    "SITE_URL": "/",
    "STYLES": ["/static/admin/css/base.css"],
    "COLORS": {
        "primary": {
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "show_navigation": True,
        "navigation": [
            {
                "title": _("Users"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": "/admin/users/user/",
                    },
                    {
                        "title": _("Mentors"),
                        "icon": "person",
                        "link": "/admin/users/mentor/",
                    },
                    {
                        "title": _("Students"),
                        "icon": "elderly_woman",
                        "link": "/admin/users/student/",
                    },
                    {
                        "title": _("Specialization"),
                        "icon": "people",
                        "link": "/admin/users/specialization/",
                    },
                    {
                        "title": _("Translation"),
                        "icon": "people",
                        "link": "/admin/translations/translationmemory/",
                    },
                ],
            },
        ],
    },
    "DARK_MODE": True,
    "DASHBOARD_CALLBACK": "school_platform.admin.views.dashboard_callback",
}

AUTH_USER_MODEL = "users.User"

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

ROOT_URLCONF = "school_platform.urls"

TEMPLATE_DIR = BASE_DIR / "templates"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "school_platform.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DB_NAME", default="school_platform"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth."
        "password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth."
        "password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth."
        "password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth."
        "password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = (
    ("en", _("English")),
    ("ru", _("Russian")),
)

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = config(
    "CELERY_RESULT_BACKEND", default="redis://redis:6379/0"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Moscow"

try:
    from school_platform.local_settings import *  # noqa: F403, F401
except ImportError:
    pass
