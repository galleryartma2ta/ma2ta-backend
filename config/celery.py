# config/celery.py

import os
from celery import Celery

# تنظیم متغیر محیطی DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# ایجاد نمونه از اپلیکیشن Celery
app = Celery('ma2ta')

# بارگذاری تنظیمات از تنظیمات جنگو
app.config_from_object('django.conf:settings', namespace='CELERY')

# اسکن تسک‌ها بصورت خودکار از برنامه‌های ثبت شده
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')