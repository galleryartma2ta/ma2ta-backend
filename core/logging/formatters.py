# core/logging/formatters.py

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from django.utils import timezone
from django.conf import settings


class ColoredFormatter(logging.Formatter):
    """
    فرمت‌دهنده لاگ با رنگ‌های مختلف برای سطوح مختلف لاگ.
    مناسب برای استفاده در کنسول و محیط توسعه.
    """
    # کدهای رنگ ANSI
    COLORS = {
        'DEBUG': '\033[36m',  # آبی فیروزه‌ای
        'INFO': '\033[32m',  # سبز
        'WARNING': '\033[33m',  # زرد
        'ERROR': '\033[31m',  # قرمز
        'CRITICAL': '\033[41m',  # پس‌زمینه قرمز
        'RESET': '\033[0m'  # بازنشانی رنگ
    }

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, use_colors: bool = True):
        """
        مقداردهی اولیه فرمت‌دهنده.

        Args:
            fmt: قالب پیام لاگ
            datefmt: قالب تاریخ
            use_colors: استفاده از رنگ‌ها
        """
        if fmt is None:
            fmt = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s'
        if datefmt is None:
            datefmt = '%d/%b/%Y %H:%M:%S'

        self.use_colors = use_colors
        super().__init__(fmt, datefmt)

    def format(self, record):
        """
        فرمت‌دهی رکورد لاگ.

        Args:
            record: رکورد لاگ

        Returns:
            str: پیام لاگ فرمت‌شده
        """
        levelname = record.levelname
        message = super().format(record)

        if self.use_colors:
            color = self.COLORS.get(levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            message = f"{color}{message}{reset}"

        return message


class JsonFormatter(logging.Formatter):
    """
    فرمت‌دهنده لاگ به صورت JSON.
    مناسب برای لاگ‌هایی که قرار است توسط سرویس‌های تحلیل لاگ پردازش شوند.
    """

    def __init__(self, include_extra: bool = True):
        """
        مقداردهی اولیه فرمت‌دهنده.

        Args:
            include_extra: شامل فیلدهای اضافی
        """
        self.include_extra = include_extra
        super().__init__()

    def format(self, record):
        """
        فرمت‌دهی رکورد لاگ به صورت JSON.

        Args:
            record: رکورد لاگ

        Returns:
            str: پیام لاگ به صورت JSON
        """
        log_dict = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'line': record.lineno
        }

        # افزودن اطلاعات خطا در صورت وجود
        if record.exc_info:
            log_dict['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # افزودن اطلاعات اضافی در صورت وجود
        if self.include_extra and hasattr(record, 'extra'):
            log_dict['extra'] = record.extra

        # افزودن اطلاعات درخواست HTTP در صورت وجود
        if hasattr(record, 'request_data'):
            log_dict['request'] = record.request_data

        # افزودن اطلاعات پاسخ HTTP در صورت وجود
        if hasattr(record, 'response_data'):
            log_dict['response'] = record.response_data

        # افزودن اطلاعات عملکرد در صورت وجود
        if hasattr(record, 'performance'):
            log_dict['performance'] = record.performance

        return json.dumps(log_dict, ensure_ascii=False)


class DetailedExceptionFormatter(logging.Formatter):
    """
    فرمت‌دهنده لاگ با جزئیات بیشتر برای خطاها.
    بهینه برای گزارش‌های خطا در محیط توسعه و یا بررسی دقیق مشکلات.
    """

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """
        مقداردهی اولیه فرمت‌دهنده.

        Args:
            fmt: قالب پیام لاگ
            datefmt: قالب تاریخ
        """
        if fmt is None:
            fmt = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s'
        if datefmt is None:
            datefmt = '%d/%b/%Y %H:%M:%S'

        super().__init__(fmt, datefmt)

    def format(self, record):
        """
        فرمت‌دهی رکورد لاگ با جزئیات بیشتر برای خطاها.

        Args:
            record: رکورد لاگ

        Returns:
            str: پیام لاگ فرمت‌شده
        """
        message = super().format(record)

        # افزودن جزئیات استثنا در صورت وجود
        if record.exc_info:
            exception_type = record.exc_info[0].__name__
            exception_message = str(record.exc_info[1])

            # فرمت‌دهی استک تریس
            stack_trace = '\n'.join(traceback.format_exception(*record.exc_info))

            # ساخت پیام نهایی
            divider = '-' * 80
            message = f"{message}\n{divider}\nException: {exception_type}: {exception_message}\n{stack_trace}\n{divider}"

        # افزودن اطلاعات اضافی در صورت وجود
        if hasattr(record, 'extra'):
            extra_info = '\n'.join([f"  {k}: {v}" for k, v in record.extra.items()])
            message = f"{message}\nExtra Data:\n{extra_info}"

        return message


class RequestFormatter(logging.Formatter):
    """
    فرمت‌دهنده لاگ برای درخواست‌های HTTP.
    بهینه برای لاگ کردن درخواست‌های API و وب.
    """

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None,
                 include_user_info: bool = True, include_headers: bool = True):
        """
        مقداردهی اولیه فرمت‌دهنده.

        Args:
            fmt: قالب پیام لاگ
            datefmt: قالب تاریخ
            include_user_info: شامل اطلاعات کاربر
            include_headers: شامل هدرهای درخواست
        """
        if fmt is None:
            fmt = '[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
        if datefmt is None:
            datefmt = '%d/%b/%Y %H:%M:%S'

        self.include_user_info = include_user_info
        self.include_headers = include_headers
        super().__init__(fmt, datefmt)

    def format(self, record):
        """
        فرمت‌دهی رکورد لاگ برای درخواست‌های HTTP.

        Args:
            record: رکورد لاگ

        Returns:
            str: پیام لاگ فرمت‌شده
        """
        message = super().format(record)

        # افزودن اطلاعات درخواست HTTP در صورت وجود
        if hasattr(record, 'request'):
            request = record.request
            method = request.method
            path = request.path

            # ساخت بخش اصلی پیام
            request_msg = f"Request: {method} {path}"

            # افزودن شناسه ردیابی در صورت وجود
            if hasattr(request, 'trace_id'):
                request_msg = f"{request_msg} [Trace: {request.trace_id}]"

            # افزودن اطلاعات کاربر
            if self.include_user_info and hasattr(request, 'user'):
                user = request.user
                user_info = "Anonymous"

                if user.is_authenticated:
                    user_info = f"User: {user.username} (ID: {user.id})"
                    if user.is_staff:
                        user_info = f"{user_info} [Staff]"
                    if user.is_superuser:
                        user_info = f"{user_info} [Superuser]"

                request_msg = f"{request_msg} {user_info}"

            # افزودن اطلاعات IP
            client_ip = self.get_client_ip(request)
            request_msg = f"{request_msg} from {client_ip}"

            # افزودن هدرهای درخواست
            if self.include_headers and hasattr(request, 'META'):
                headers = "\n  Headers:"
                for key, value in request.META.items():
                    if key.startswith('HTTP_'):
                        header_name = key[5:].replace('_', '-').title()
                        # حذف اطلاعات حساس
                        if 'AUTHORIZATION' in header_name or 'COOKIE' in header_name:
                            value = '[REDACTED]'
                        headers = f"{headers}\n    {header_name}: {value}"

                request_msg = f"{request_msg}{headers}"

            # افزودن اطلاعات درخواست به پیام اصلی
            message = f"{message}\n{request_msg}"

            # افزودن زمان پاسخ در صورت وجود
            if hasattr(record, 'response_time'):
                message = f"{message}\nResponse Time: {record.response_time:.2f} ms"

        return message

    def get_client_ip(self, request):
        """
        استخراج آدرس IP واقعی کاربر.

        Args:
            request: درخواست HTTP

        Returns:
            str: آدرس IP کاربر
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # اولین IP در لیست، IP واقعی کاربر است
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class RTLFormatter(logging.Formatter):
    """
    فرمت‌دهنده لاگ با پشتیبانی از متون راست به چپ (RTL).
    بهینه برای لاگ‌های فارسی و عربی.
    """

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None,
                 add_rtl_markers: bool = True):
        """
        مقداردهی اولیه فرمت‌دهنده.

        Args:
            fmt: قالب پیام لاگ
            datefmt: قالب تاریخ
            add_rtl_markers: افزودن نشانگرهای RTL
        """
        if fmt is None:
            fmt = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s'
        if datefmt is None:
            datefmt = '%d/%b/%Y %H:%M:%S'

        self.add_rtl_markers = add_rtl_markers
        super().__init__(fmt, datefmt)

    def format(self, record):
        """
        فرمت‌دهی رکورد لاگ با پشتیبانی از RTL.

        Args:
            record: رکورد لاگ

        Returns:
            str: پیام لاگ فرمت‌شده
        """
        # تغییر پیام لاگ برای پشتیبانی از RTL
        if self.add_rtl_markers:
            # افزودن نشانگرهای RTL به پیام
            record.msg = f"\u200F{record.msg}\u200F"

        return super().format(record)


class DatabaseActionFormatter(logging.Formatter):
    """
    فرمت‌دهنده لاگ برای عملیات‌های پایگاه داده.
    بهینه برای ثبت عملیات‌های CRUD روی پایگاه داده.
    """

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """
        مقداردهی اولیه فرمت‌دهنده.

        Args:
            fmt: قالب پیام لاگ
            datefmt: قالب تاریخ
        """
        if fmt is None:
            fmt = '[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
        if datefmt is None:
            datefmt = '%d/%b/%Y %H:%M:%S'

        super().__init__(fmt, datefmt)

    def format(self, record):
        """
        فرمت‌دهی رکورد لاگ برای عملیات‌های پایگاه داده.

        Args:
            record: رکورد لاگ

        Returns:
            str: پیام لاگ فرمت‌شده
        """
        message = super().format(record)

        # افزودن اطلاعات عملیات پایگاه داده در صورت وجود
        if hasattr(record, 'db_action'):
            action = record.db_action
            model = getattr(record, 'model_name', 'Unknown')
            object_id = getattr(record, 'object_id', 'Unknown')

            # تنظیم رنگ برای عملیات‌های مختلف (در کنسول)
            action_color = ''
            reset_color = '\033[0m'

            if action == 'CREATE':
                action_color = '\033[32m'  # سبز
            elif action == 'UPDATE':
                action_color = '\033[33m'  # زرد
            elif action == 'DELETE':
                action_color = '\033[31m'  # قرمز
            elif action == 'READ':
                action_color = '\033[36m'  # آبی فیروزه‌ای

            # ساخت بخش عملیات DB
            db_msg = f"{action_color}{action}{reset_color} {model} (ID: {object_id})"

            # افزودن اطلاعات کاربر انجام‌دهنده عملیات
            if hasattr(record, 'user_info'):
                db_msg = f"{db_msg} by {record.user_info}"

            # افزودن تغییرات در صورت وجود
            if hasattr(record, 'changes') and record.changes:
                changes = record.changes
                changes_str = ", ".join([f"{k}: {v}" for k, v in changes.items()])
                db_msg = f"{db_msg}\n  Changes: {changes_str}"

            # افزودن اطلاعات عملیات DB به پیام اصلی
            message = f"{message}\nDB Operation: {db_msg}"

        return message


def get_log_config(log_level: str = 'INFO', log_file: Optional[str] = None,
                   enable_console: bool = True, enable_json: bool = False,
                   enable_sentry: bool = False) -> Dict:
    """
    دریافت پیکربندی لاگینگ بر اساس پارامترهای ورودی.

    Args:
        log_level: سطح لاگ
        log_file: مسیر فایل لاگ
        enable_console: فعال‌سازی لاگ در کنسول
        enable_json: فعال‌سازی لاگ به فرمت JSON
        enable_sentry: فعال‌سازی لاگ در Sentry

    Returns:
        Dict: پیکربندی لاگینگ
    """
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                '()': 'core.logging.formatters.ColoredFormatter',
                'fmt': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
                'datefmt': '%d/%b/%Y %H:%M:%S',
                'use_colors': True,
            },
            'simple': {
                'format': '%(levelname)s %(message)s',
            },
            'json': {
                '()': 'core.logging.formatters.JsonFormatter',
                'include_extra': True,
            },
            'exception': {
                '()': 'core.logging.formatters.DetailedExceptionFormatter',
            },
            'request': {
                '()': 'core.logging.formatters.RequestFormatter',
                'include_user_info': True,
                'include_headers': True,
            },
        },
        'handlers': {
            'null': {
                'class': 'logging.NullHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': [],
                'level': log_level,
                'propagate': True,
            },
            'django.request': {
                'handlers': [],
                'level': 'INFO',
                'propagate': True,
            },
            'django.db.backends': {
                'handlers': [],
                'level': 'WARNING',
                'propagate': True,
            },
            'ma2ta': {
                'handlers': [],
                'level': log_level,
                'propagate': True,
            },
            'ma2ta.api': {
                'handlers': [],
                'level': 'INFO',
                'propagate': True,
            },
            'ma2ta.payment': {
                'handlers': [],
                'level': 'INFO',
                'propagate': True,
            },
            'request': {
                'handlers': [],
                'level': 'INFO',
                'propagate': True,
            },
            'performance': {
                'handlers': [],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }

    handlers = []

    # افزودن هندلر کنسول
    if enable_console:
        log_config['handlers']['console'] = {
            'level': log_level,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
        handlers.append('console')

    # افزودن هندلر فایل
    if log_file:
        log_config['handlers']['file'] = {
            'level': log_level,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': log_file,
            'maxBytes': 1024 * 1024 * 10,  # 10 مگابایت
            'backupCount': 5,
            'formatter': 'verbose',
        }
        handlers.append('file')

    # افزودن هندلر JSON
    if enable_json:
        if log_file:
            json_log_file = log_file.replace('.log', '.json.log')
            log_config['handlers']['json_file'] = {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': json_log_file,
                'maxBytes': 1024 * 1024 * 10,  # 10 مگابایت
                'backupCount': 5,
                'formatter': 'json',
            }
            handlers.append('json_file')

    # افزودن هندلر Sentry
    if enable_sentry:
        log_config['handlers']['sentry'] = {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        }
        handlers.append('sentry')

    # افزودن هندلرها به لاگرها
    for logger_name in log_config['loggers']:
        log_config['loggers'][logger_name]['handlers'] = handlers

    return log_config