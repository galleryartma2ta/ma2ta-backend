# core/middlewares/trace.py

import time
import uuid
import logging
import json
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('request_trace')


class RequestTraceMiddleware(MiddlewareMixin):
    """
    میدل‌ویر ثبت و ردیابی درخواست‌ها.
    این میدل‌ویر اطلاعات درخواست‌ها را لاگ می‌کند و زمان پاسخگویی را محاسبه می‌کند.
    همچنین شناسه منحصر به فرد برای هر درخواست ایجاد می‌کند.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.TRACE_ENABLED = getattr(settings, 'REQUEST_TRACE_ENABLED', settings.DEBUG)
        self.TRACE_SENSITIVE_FIELDS = getattr(settings, 'REQUEST_TRACE_SENSITIVE_FIELDS', [
            'password', 'token', 'access', 'refresh', 'auth', 'key', 'secret', 'credential'
        ])
        self.TRACE_EXCLUDE_PATHS = getattr(settings, 'REQUEST_TRACE_EXCLUDE_PATHS', [
            '/static/', '/media/', '/admin/jsi18n/', '/favicon.ico'
        ])
        super().__init__(get_response)

    def process_request(self, request):
        """پردازش و ثبت اطلاعات درخواست"""
        if not self.TRACE_ENABLED:
            return None

        # بررسی مسیرهای مستثنی
        if any(request.path.startswith(path) for path in self.TRACE_EXCLUDE_PATHS):
            return None

        # ایجاد شناسه درخواست
        request.trace_id = str(uuid.uuid4())
        request.start_time = time.time()

        # لاگ اطلاعات درخواست
        if logger.isEnabledFor(logging.DEBUG):
            # ثبت اطلاعات درخواست
            request_data = {}

            # ثبت اطلاعات پارامترهای GET
            if request.GET:
                request_data['GET'] = self.sanitize_data(dict(request.GET))

            # ثبت اطلاعات پارامترهای POST
            if request.POST:
                request_data['POST'] = self.sanitize_data(dict(request.POST))

            # ثبت اطلاعات JSON
            if request.content_type and 'application/json' in request.content_type:
                try:
                    body = request.body.decode('utf-8')
                    if body:
                        json_data = json.loads(body)
                        request_data['BODY'] = self.sanitize_data(json_data)
                except (ValueError, UnicodeDecodeError):
                    request_data['BODY'] = "(invalid JSON)"

            # ثبت اطلاعات هدرها
            headers = {}
            for key, value in request.META.items():
                if key.startswith('HTTP_'):
                    header_key = key[5:].replace('_', '-').title()
                    headers[header_key] = value

            request_data['HEADERS'] = self.sanitize_data(headers)

            logger.debug(
                "Request %s: %s %s",
                request.trace_id,
                request.method,
                request.path,
                extra={'request_data': request_data}
            )

    def process_response(self, request, response):
        """پردازش و ثبت اطلاعات پاسخ"""
        if not self.TRACE_ENABLED or not hasattr(request, 'trace_id'):
            return response

        # بررسی مسیرهای مستثنی
        if any(request.path.startswith(path) for path in self.TRACE_EXCLUDE_PATHS):
            return response

        # محاسبه زمان پاسخگویی
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Request-Trace-ID'] = request.trace_id
            response['X-Request-Duration'] = str(int(duration * 1000))  # تبدیل به میلی‌ثانیه

            # لاگ اطلاعات پاسخ
            if logger.isEnabledFor(logging.DEBUG):
                response_data = {
                    'status_code': response.status_code,
                    'content_type': response.get('Content-Type', ''),
                    'duration_ms': int(duration * 1000),
                }

                # ثبت محتوای پاسخ برای API
                if (response.get('Content-Type', '').startswith('application/json') and
                        hasattr(response, 'content')):
                    try:
                        content = response.content.decode('utf-8')
                        if content:
                            json_data = json.loads(content)
                            response_data['content'] = self.sanitize_data(json_data)
                    except (ValueError, UnicodeDecodeError):
                        response_data['content'] = "(invalid JSON)"

                logger.debug(
                    "Response %s: %s completed in %dms",
                    request.trace_id,
                    request.path,
                    int(duration * 1000),
                    extra={'response_data': response_data}
                )

        return response

    def sanitize_data(self, data):
        """حذف اطلاعات حساس از داده‌ها"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                lower_key = key.lower()
                if any(sensitive in lower_key for sensitive in self.TRACE_SENSITIVE_FIELDS):
                    sanitized[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self.sanitize_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self.sanitize_data(item) if isinstance(item, (dict, list)) else item for item in data]
        else:
            return data