"""
تنظیمات ASGI برای پروژه Ma2tA.

این فایل برای اجرای برنامه توسط سرورهای ASGI مانند Daphne استفاده می‌شود.
برای پشتیبانی از WebSocket و وظایف آسنکرون از ASGI استفاده می‌شود.
برای اطلاعات بیشتر به مستندات Django مراجعه کنید:
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.gallery.routing
import apps.notifications.routing

# تنظیم متغیر محیطی برای تنظیمات جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# تنظیم برنامه اصلی ASGI با پشتیبانی از WebSocket
application = ProtocolTypeRouter({
    # برنامه HTTP معمولی Django
    "http": get_asgi_application(),

    # برنامه WebSocket با پشتیبانی از احراز هویت
    "websocket": AuthMiddlewareStack(
        URLRouter(
            # اضافه کردن مسیرهای WebSocket برای ماژول‌های مختلف
            apps.gallery.routing.websocket_urlpatterns +
            apps.notifications.routing.websocket_urlpatterns
        )
    ),
})