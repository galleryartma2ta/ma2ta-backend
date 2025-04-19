# core/middlewares/throttling.py

import time
import hashlib
import ipaddress
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from django.utils.translation import gettext as _
from django.utils.deprecation import MiddlewareMixin
import json


class CustomThrottlingMiddleware(MiddlewareMixin):
    """
    میدل‌ویر محدودیت درخواست‌ها برای جلوگیری از حملات و سوءاستفاده.
    این میدل‌ویر نرخ درخواست‌ها را محدود می‌کند و برای مسیرهای مختلف،
    قوانین متفاوتی را اعمال می‌کند.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

        # تنظیمات پیش‌فرض
        self.THROTTLE_ENABLED = getattr(settings, 'THROTTLE_ENABLED', True)
        self.THROTTLE_EXEMPT_NETWORKS = getattr(settings, 'THROTTLE_EXEMPT_NETWORKS', [
            '127.0.0.1/32',  # localhost
            '10.0.0.0/8',  # private network
            '172.16.0.0/12',  # private network
            '192.168.0.0/16'  # private network
        ])

        # تبدیل آدرس‌های IP به شبکه‌ها
        self.exempt_networks = [ipaddress.ip_network(net) for net in self.THROTTLE_EXEMPT_NETWORKS]

        # قوانین محدودیت برای مسیرهای مختلف (مسیر: [تعداد درخواست‌ها, دوره زمانی به ثانیه])
        self.THROTTLE_RULES = getattr(settings, 'THROTTLE_RULES', {
            # API های عمومی
            'api/': [60, 60],  # 60 درخواست در دقیقه

            # API های احراز هویت
            'api/auth/token/': [5, 60],  # 5 درخواست در دقیقه
            'api/auth/register/': [5, 300],  # 5 درخواست در 5 دقیقه
            'api/auth/password/reset/': [3, 300],  # 3 درخواست در 5 دقیقه

            # API های پرداخت
            'api/payments/': [20, 60],  # 20 درخواست در دقیقه

            # درخواست‌های ویژه
            'api/artworks/upload/': [30, 300],  # 30 درخواست در 5 دقیقه

            # حراجی‌ها
            'api/auctions/bid/': [20, 30],  # 20 درخواست در 30 ثانیه
        })

        # قانون پیش‌فرض برای همه مسیرها
        self.DEFAULT_RULE = getattr(settings, 'THROTTLE_DEFAULT_RULE', [100, 60])  # 100 درخواست در دقیقه

        # مسیرهایی که از محدودیت نرخ معاف هستند
        self.THROTTLE_EXEMPT_PATHS = getattr(settings, 'THROTTLE_EXEMPT_PATHS', [
            '/admin/',
            '/static/',
            '/media/',
        ])

        super().__init__(get_response)

    def process_request(self, request):
        """بررسی و اعمال محدودیت نرخ درخواست‌ها"""
        if not self.THROTTLE_ENABLED:
            return None

        # بررسی مسیرهای معاف
        if any(request.path.startswith(path) for path in self.THROTTLE_EXEMPT_PATHS):
            return None

        # بررسی شبکه‌های معاف
        client_ip = self.get_client_ip(request)
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            for network in self.exempt_networks:
                if client_ip_obj in network:
                    return None
        except ValueError:
            # اگر IP نامعتبر باشد، محدودیت را اعمال می‌کنیم
            pass

        # یافتن قانون مناسب برای مسیر فعلی
        rule = self.DEFAULT_RULE
        for path, path_rule in self.THROTTLE_RULES.items():
            if request.path.startswith(f"/{path}"):
                rule = path_rule
                break

        # اعمال محدودیت
        return self.apply_throttling(request, client_ip, rule)

    def apply_throttling(self, request, client_ip, rule):
        """اعمال محدودیت نرخ بر اساس قانون مشخص شده"""
        requests_allowed, time_period = rule

        # ایجاد کلید منحصر به فرد برای کاربر و مسیر
        user_id = self.get_user_identifier(request, client_ip)
        path_hash = hashlib.md5(request.path.encode()).hexdigest()[:8]
        cache_key = f"throttle:{user_id}:{path_hash}"

        # بررسی تعداد درخواست‌های قبلی
        request_history = cache.get(cache_key)
        if request_history is None:
            # اولین درخواست
            request_history = [time.time()]
            cache.set(cache_key, request_history, time_period)
            return None

        # حذف درخواست‌های قدیمی‌تر از دوره زمانی
        current_time = time.time()
        request_history = [t for t in request_history if current_time - t < time_period]

        # بررسی محدودیت
        if len(request_history) >= requests_allowed:
            # محدودیت نقض شده است
            remaining_seconds = int(time_period - (current_time - min(request_history)))
            return self.throttled_response(request, remaining_seconds)

        # افزودن درخواست جدید و ذخیره
        request_history.append(current_time)
        cache.set(cache_key, request_history, time_period)
        return None

    def get_user_identifier(self, request, client_ip):
        """تشخیص شناسه منحصر به فرد کاربر"""
        # اگر کاربر وارد شده باشد، از شناسه کاربر استفاده می‌کنیم
        if request.user.is_authenticated:
            return f"user:{request.user.id}"

        # از آدرس IP به عنوان شناسه استفاده می‌کنیم
        return f"ip:{client_ip}"

    def get_client_ip(self, request):
        """استخراج آدرس IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # اولین IP در لیست، IP واقعی کاربر است
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    def throttled_response(self, request, wait_seconds):
        """ایجاد پاسخ برای درخواست‌های محدود شده"""
        response = HttpResponseTooManyRequests()

        # افزودن هدرهای استاندارد برای محدودیت نرخ
        response['Retry-After'] = str(wait_seconds)

        # ایجاد پیام مناسب
        message = _("درخواست‌های بیش از حد ارسال شده است. لطفاً {wait} ثانیه صبر کنید.").format(wait=wait_seconds)

        # تنظیم نوع محتوا بر اساس درخواست
        content_type = request.META.get('HTTP_ACCEPT', '')

        if 'application/json' in content_type:
            # پاسخ JSON برای درخواست‌های API
            response.content = json.dumps({
                'detail': message,
                'code': 'throttled',
                'wait': wait_seconds
            })
            response['Content-Type'] = 'application/json'
        else:
            # پاسخ HTML برای سایر درخواست‌ها
            response.content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{_('محدودیت درخواست')}</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; }}
                    .container {{ max-width: 600px; margin: 100px auto; padding: 20px; text-align: center; }}
                    h1 {{ color: #e74c3c; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>{_('درخواست‌های بیش از حد')}</h1>
                    <p>{message}</p>
                </div>
            </body>
            </html>
            """.encode('utf-8')
            response['Content-Type'] = 'text/html; charset=utf-8'

        return response