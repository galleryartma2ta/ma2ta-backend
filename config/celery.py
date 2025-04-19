"""
تنظیمات و پیکربندی Celery برای پروژه Ma2tA.
Celery برای انجام وظایف غیرهمزمان مانند ارسال ایمیل، پردازش تصاویر و غیره استفاده می‌شود.
"""

import os
from celery import Celery
from celery.schedules import crontab

# تنظیم متغیر محیطی برای تنظیمات جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# ایجاد نمونه اصلی سلری
app = Celery('ma2ta')

# استفاده از تنظیمات جنگو برای پیکربندی سلری
app.config_from_object('django.conf:settings', namespace='CELERY')

# ثبت خودکار تسک‌ها از همه برنامه‌های ثبت شده جنگو
app.autodiscover_tasks()

# تنظیم زمان‌بندی وظایف دوره‌ای
app.conf.beat_schedule = {
    # بروزرسانی وضعیت حراج‌ها (هر ده دقیقه)
    'update-auction-status': {
        'task': 'apps.gallery.tasks.update_auction_status',
        'schedule': 10 * 60,  # هر 10 دقیقه
    },

    # ارسال یادآوری رویدادها (هر روز ساعت 8 صبح)
    'send-exhibition-reminders': {
        'task': 'apps.gallery.tasks.send_exhibition_reminders',
        'schedule': crontab(hour=8, minute=0),
    },

    # سیستم پیشنهاد خودکار محصولات (هر شب نیمه شب)
    'generate-product-recommendations': {
        'task': 'apps.recommendations.tasks.generate_product_recommendations',
        'schedule': crontab(hour=0, minute=0),
    },

    # پاکسازی سشن‌های منقضی (یکشنبه‌ها ساعت 2 بامداد)
    'cleanup-expired-sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },

    # پشتیبان‌گیری از پایگاه داده (هر هفته دوشنبه ساعت 3 بامداد)
    'database-backup': {
        'task': 'apps.core.tasks.database_backup',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
    },
}

# تنظیمات روت‌های سلری
app.conf.task_routes = {
    'apps.gallery.tasks.*': {'queue': 'gallery'},
    'apps.orders.tasks.*': {'queue': 'orders'},
    'apps.notifications.tasks.*': {'queue': 'notifications'},
    'apps.core.tasks.*': {'queue': 'default'},
}

# اولویت‌های پیش‌فرض برای صف‌ها
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5


@app.task(bind=True)
def debug_task(self):
    """تسک تست برای اطمینان از صحت کارکرد سلری"""
    print(f'Request: {self.request!r}')