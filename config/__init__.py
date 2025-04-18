# config/__init__.py

# این فایل برای بارگذاری Celery استفاده می‌شود
from .celery import app as celery_app

__all__ = ('celery_app',)