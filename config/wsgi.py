"""
تنظیمات WSGI برای پروژه Ma2tA.

این فایل برای اجرای برنامه توسط سرورهای WSGI مانند Gunicorn استفاده می‌شود.
برای اطلاعات بیشتر به مستندات Django مراجعه کنید:
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# تنظیم متغیر محیطی برای تنظیمات جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# ایجاد و تنظیم برنامه WSGI
application = get_wsgi_application()