# core/logging/handlers.py

import logging
import json
import datetime
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from django.db import models
from django.utils import timezone


class DatabaseLogHandler(logging.Handler):
    """
    هندلر لاگینگ برای ذخیره لاگ‌ها در پایگاه داده.
    """

    def __init__(self, model=None):
        """
        مقداردهی اولیه هندلر.

        Args:
            model: مدل لاگ
        """
        super().__init__()
        self.model = model

    def emit(self, record):
        """
        ثبت رکورد لاگ در پایگاه داده.

        Args:
            record: رکورد لاگ
        """
        if not self.model:
            return

        try:
            # تبدیل رکورد به دیکشنری
            log_entry = {
                'level': record.levelname,
                'message': self.format(record),
                'logger_name': record.name,
                'timestamp': timezone.now(),
                'path': record.pathname,
                'line_number': record.lineno,
                'function_name': record.funcName,
            }

            # اضافه کردن اطلاعات استثنا در صورت وجود
            if record.exc_info:
                log_entry['exception_type'] = record.exc_info[0].__name__
                log_entry['exception_message'] = str(record.exc_info[1])

            # اضافه کردن اطلاعات درخواست در صورت وجود
            if hasattr(record, 'request'):
                if hasattr(record.request, 'user') and record.request.user.is_authenticated:
                    log_entry['user_id'] = record.request.user.id
                    log_entry['username'] = record.request.user.username

                log_entry['request_method'] = record.request.method
                log_entry['request_path'] = record.request.path

                if hasattr(record.request, 'trace_id'):
                    log_entry['trace_id'] = record.request.trace_id

            # ذخیره در پایگاه داده
            self.model.objects.create(**log_entry)

        except Exception as e:
            # در صورت خطا، لاگ را به کنسول می‌فرستیم
            print(f"Error saving log to database: {str(e)}")


class SlackLogHandler(logging.Handler):
    """
    هندلر لاگینگ برای ارسال لاگ‌ها به Slack.
    """

    def __init__(self, webhook_url: Optional[str] = None, channel: Optional[str] = None,
                 username: Optional[str] = None, icon_emoji: Optional[str] = None,
                 environment: Optional[str] = None):
        """
        مقداردهی اولیه هندلر.

        Args:
            webhook_url: آدرس وب‌هوک Slack
            channel: کانال Slack
            username: نام کاربری برای نمایش
            icon_emoji: ایموجی آیکون
            environment: محیط (توسعه، تولید و...)
        """
        super().__init__()
        self.webhook_url = webhook_url or getattr(settings, 'SLACK_LOGGING_WEBHOOK_URL', None)
        self.channel = channel or getattr(settings, 'SLACK_LOGGING_CHANNEL', '#errors')
        self.username = username or getattr(settings, 'SLACK_LOGGING_USERNAME', 'Ma2tA Error Bot')
        self.icon_emoji = icon_emoji or getattr(settings, 'SLACK_LOGGING_ICON_EMOJI', ':warning:')
        self.environment = environment or getattr(settings, 'ENVIRONMENT', 'development')

    def emit(self, record):
        """
        ارسال رکورد لاگ به Slack.

        Args:
            record: رکورد لاگ
        """
        if not self.webhook_url:
            return

        try:
            # تنظیم رنگ بر اساس سطح لاگ
            color = self._get_color_for_level(record.levelname)

            # ساخت متن پیام
            message = self.format(record)

            # ساخت اطلاعات اضافی
            fields = [
                {
                    'title': 'زمان',
                    'value': datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
                    'short': True
                },
                {
                    'title': 'محیط',
                    'value': self.environment,
                    'short': True
                },
                {
                    'title': 'لاگر',
                    'value': record.name,
                    'short': True
                },
                {
                    'title': 'سطح',
                    'value': record.levelname,
                    'short': True
                }
            ]

            # اضافه کردن اطلاعات استثنا در صورت وجود
            if record.exc_info:
                fields.append({
                    'title': 'استثنا',
                    'value': f"{record.exc_info[0].__name__}: {str(record.exc_info[1])}",
                    'short': False
                })

            # ساخت پیام Slack
            payload = {
                'channel': self.channel,
                'username': self.username,
                'icon_emoji': self.icon_emoji,
                'attachments': [
                    {
                        'fallback': message,
                        'color': color,
                        'title': f"خطا در برنامه Ma2tA ({self.environment})",
                        'text': message,
                        'fields': fields,
                        'ts': record.created
                    }
                ]
            }

            # ارسال به Slack
            requests.post(self.webhook_url, json=payload)

        except Exception as e:
            # در صورت خطا، لاگ را به کنسول می‌فرستیم
            print(f"Error sending log to Slack: {str(e)}")

    def _get_color_for_level(self, level: str) -> str:
        """
        دریافت رنگ متناسب با سطح لاگ.

        Args:
            level: سطح لاگ

        Returns:
            str: کد رنگ
        """
        colors = {
            'DEBUG': '#3AA3E3',  # آبی روشن
            'INFO': '#2EB886',  # سبز
            'WARNING': '#ECB22E',  # زرد
            'ERROR': '#E01E5A',  # قرمز
            'CRITICAL': '#8B1E3F',  # قرمز تیره
        }

        return colors.get(level, '#9B9B9B')  # رنگ پیش‌فرض: خاکستری


class SentryLogHandler(logging.Handler):
    """
    هندلر لاگینگ برای ارسال لاگ‌ها به Sentry.
    نیازمند نصب پکیج sentry-sdk.
    """

    def __init__(self, sentry_dsn: Optional[str] = None,
                 minimum_level: str = 'ERROR'):
        """
        مقداردهی اولیه هندلر.

        Args:
            sentry_dsn: آدرس DSN سنتری
            minimum_level: حداقل سطح لاگ برای ارسال به سنتری
        """
        super().__init__()
        self.sentry_dsn = sentry_dsn or getattr(settings, 'SENTRY_DSN', None)
        self.minimum_level = getattr(logging, minimum_level, logging.ERROR)

        # بررسی نصب بودن sentry-sdk
        try:
            import sentry_sdk
            self.sentry_sdk = sentry_sdk

            # اگر sentry تنظیم نشده باشد، آن را تنظیم می‌کنیم
            if self.sentry_dsn and not sentry_sdk.Hub.current.client:
                sentry_sdk.init(
                    dsn=self.sentry_dsn,
                    environment=getattr(settings, 'ENVIRONMENT', 'development'),
                    release=getattr(settings, 'VERSION', '0.1.0'),
                )
        except ImportError:
            self.sentry_sdk = None
            print("sentry_sdk is not installed. Please install it with 'pip install sentry-sdk'.")

    def emit(self, record):
        """
        ارسال رکورد لاگ به Sentry.

        Args:
            record: رکورد لاگ
        """
        if not self.sentry_sdk or not self.sentry_dsn:
            return

        # بررسی سطح لاگ
        if record.levelno < self.minimum_level:
            return

        try:
            # ساخت اطلاعات اضافی
            with self.sentry_sdk.push_scope() as scope:
                # افزودن تگ‌ها
                scope.set_tag('logger', record.name)
                scope.set_tag('level', record.levelname)

                # افزودن اطلاعات اضافی
                if hasattr(record, 'request'):
                    request = record.request
                    scope.set_context('request', {
                        'method': request.method,
                        'url': request.path,
                        'query_string': request.META.get('QUERY_STRING', ''),
                    })

                    # افزودن اطلاعات کاربر
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        scope.set_user({
                            'id': request.user.id,
                            'username': request.user.username,
                            'email': getattr(request.user, 'email', ''),
                        })

                # افزودن خطای اصلی در صورت وجود
                if record.exc_info:
                    self.sentry_sdk.capture_exception(record.exc_info)
                else:
                    # ارسال پیام
                    self.sentry_sdk.capture_message(
                        self.format(record),
                        level=self._get_sentry_level(record.levelname)
                    )

        except Exception as e:
            # در صورت خطا، لاگ را به کنسول می‌فرستیم
            print(f"Error sending log to Sentry: {str(e)}")

    def _get_sentry_level(self, level: str) -> str:
        """
        تبدیل سطح لاگ به فرمت سنتری.

        Args:
            level: سطح لاگ

        Returns:
            str: سطح لاگ در فرمت سنتری
        """
        levels = {
            'DEBUG': 'debug',
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'error',
            'CRITICAL': 'fatal',
        }

        return levels.get(level, 'error')