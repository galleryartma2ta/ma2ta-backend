"""
تنظیمات محیط تست Django برای پروژه Ma2tA.
"""

from .base import *  # noqa

# تنظیمات دیباگ برای محیط تست
DEBUG = False
TEMPLATE_DEBUG = False

# کلید رمزنگاری ثابت برای تست‌ها
SECRET_KEY = 'test-key-not-for-production'

# اجازه دسترسی به لوکال‌هاست
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# پایگاه داده سریع برای تست
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# غیرفعال کردن کش در تست‌ها
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# تنظیمات فایل‌های استاتیک برای تست
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# تنظیمات ایمیل برای تست
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# تنظیمات Celery برای تست
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# تنظیمات REST Framework برای محیط تست
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# غیرفعال کردن محدودیت نرخ درخواست در تست‌ها
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {
        'anon': None,
        'user': None,
    }
})

# غیرفعال کردن CSRF برای تست‌های API
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'django.middleware.csrf.CsrfViewMiddleware']

# افزایش سرعت هش رمز در تست‌ها
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# تنظیمات لاگ برای تست
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'CRITICAL',
        },
        'ma2ta': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'CRITICAL',
        },
    },
}

# تنظیمات مخصوص تست برای پروژه Ma2tA
MA2TA_SETTINGS.update({
    'ENABLE_DEBUG_TOOLS': False,
    'MOCK_PAYMENT_GATEWAY': True,  # استفاده از درگاه پرداخت شبیه‌سازی شده برای تست
    'SKIP_AR_VALIDATION': True,  # رد کردن اعتبارسنجی AR در تست‌ها
})

# تنظیمات file uploads برای تست
FILE_UPLOAD_TEMP_DIR = BASE_DIR / 'temp_test_uploads'

# تنظیمات JWT برای تست‌ها (مدت زمان کمتر)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=1),
})

# غیرفعال کردن ارسال واقعی ایمیل‌ها در تست
DJOSER.update({
    'SEND_ACTIVATION_EMAIL': False,
    'SEND_CONFIRMATION_EMAIL': False,
})