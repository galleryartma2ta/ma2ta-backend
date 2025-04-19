"""
تنظیمات محیط تولید Django برای پروژه Ma2tA.
"""

from .base import *  # noqa
import os

# دیباگ غیرفعال در محیط تولید
DEBUG = False

# دامنه‌های مجاز
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# کلید امنیتی از متغیرهای محیطی
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set in environment")

# تنظیمات CORS برای تولید
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# تنظیمات امنیتی
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 سال
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# تنظیمات استاتیک فایل‌ها برای تولید
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# تنظیمات لاگینگ برای محیط تولید
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'ma2ta': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# تنظیمات ایمیل برای محیط تولید
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# تنظیمات کش برای محیط تولید
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# تنظیمات Celery برای محیط تولید
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# تنظیم درگاه پرداخت واقعی برای محیط تولید
MA2TA_SETTINGS.update({
    'ENABLE_DEBUG_TOOLS': False,
    'MOCK_PAYMENT_GATEWAY': False,
    'PAYMENT_GATEWAYS': {
        'zarinpal': {
            'MERCHANT_ID': os.environ.get('ZARINPAL_MERCHANT_ID'),
            'CALLBACK_URL': os.environ.get('ZARINPAL_CALLBACK_URL'),
            'DESCRIPTION': 'پرداخت در گالری هنری Ma2tA',
        },
        'idpay': {
            'API_KEY': os.environ.get('IDPAY_API_KEY'),
            'CALLBACK_URL': os.environ.get('IDPAY_CALLBACK_URL'),
        }
    }
})

# تنظیمات سئو
SEO_SETTINGS = {
    'SITE_NAME': 'Ma2tA - گالری آنلاین هنری',
    'SITE_DESCRIPTION': 'خرید و فروش آثار هنری اصیل ایرانی با امکان مشاهده واقعیت افزوده',
    'DEFAULT_OG_IMAGE': f"{STATIC_URL}images/og-image.jpg",
}

# محدودیت نرخ درخواست‌ها
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
})

# تمیز کردن داده‌های HTML در ورودی‌ها
BLEACH_ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
BLEACH_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
}

# بررسی دوره‌ای وضعیت رویدادها و حراج‌ها
CELERY_BEAT_SCHEDULE = {
    'update_auction_status': {
        'task': 'apps.gallery.tasks.update_auction_status',
        'schedule': timedelta(minutes=10),
    },
    'send_exhibition_reminders': {
        'task': 'apps.gallery.tasks.send_exhibition_reminders',
        'schedule': timedelta(hours=24),
    },
    'cleanup_expired_sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': timedelta(days=7),
    },
}