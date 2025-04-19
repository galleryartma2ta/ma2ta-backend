"""
تنظیمات محیط توسعه Django برای پروژه Ma2tA.
"""

from .base import *  # noqa
import os
from corsheaders.defaults import default_headers

# رفع محدودیت CORS در محیط توسعه
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:.*$",
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    "Access-Control-Allow-Origin",
]

# فعال کردن دیباگ در محیط توسعه
DEBUG = True

# اجازه دسترسی به لوکال‌هاست
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# تنظیمات پایگاه داده برای محیط توسعه (می‌تواند SQLite باشد)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'ma2ta_db_dev'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# اضافه کردن Django Debug Toolbar
INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

# تنظیمات Django Debug Toolbar
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

INTERNAL_IPS = [
    '127.0.0.1',
]

# اضافه کردن محیط‌های مجازی برای ایمیل
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# REST Framework تنظیمات برای محیط توسعه
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

# تنظیمات لاگینگ برای محیط توسعه
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'ma2ta': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if os.getenv('SQL_DEBUG', False) else 'INFO',
            'propagate': False,
        },
    },
}

# غیرفعال کردن کش در محیط توسعه
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# فعال‌سازی سیستم debug برای static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# غیرفعال کردن SSL در محیط توسعه
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# تنظیمات JWT برای محیط توسعه (مدت زمان بیشتر)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
})

# تنظیمات Celery برای محیط توسعه
CELERY_TASK_ALWAYS_EAGER = True  # اجرای همزمان تسک‌ها بدون صف
CELERY_TASK_EAGER_PROPAGATES = True

# تنظیمات سفارشی برای محیط توسعه
MA2TA_SETTINGS.update({
    'ENABLE_DEBUG_TOOLS': True,
    'MOCK_PAYMENT_GATEWAY': True,  # شبیه‌سازی درگاه پرداخت در محیط توسعه
})