# core/services/email_service.py

import logging
import threading
from typing import Dict, List, Optional, Union
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger('email')


class EmailService:
    """
    سرویس ارسال ایمیل.
    این کلاس انواع مختلف ایمیل‌ها را با پشتیبانی از قالب‌های HTML ارسال می‌کند.
    """

    def __init__(self, connection: Optional[EmailBackend] = None):
        """
        مقداردهی اولیه سرویس ایمیل.

        Args:
            connection: اتصال SMTP اختیاری. اگر ارائه نشود، از تنظیمات پروژه استفاده می‌شود.
        """
        self.connection = connection
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.async_mode = getattr(settings, 'ASYNC_EMAIL_SENDING', True)

        # تنظیمات ایمیل جایگزین برای زمانی که سرویس اصلی در دسترس نیست
        self.fallback_settings = getattr(settings, 'EMAIL_FALLBACK_SETTINGS', None)

    def send_email(self,
                   subject: str,
                   to_emails: Union[str, List[str]],
                   message: str,
                   html_message: Optional[str] = None,
                   from_email: Optional[str] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   attachments: Optional[List[Dict]] = None,
                   fail_silently: bool = False) -> bool:
        """
        ارسال ایمیل ساده یا HTML.

        Args:
            subject: موضوع ایمیل
            to_emails: آدرس یا لیستی از آدرس‌های ایمیل گیرندگان
            message: متن ساده ایمیل
            html_message: نسخه HTML ایمیل (اختیاری)
            from_email: آدرس فرستنده (اختیاری، پیش‌فرض از تنظیمات)
            cc: لیست آدرس‌های رونوشت (اختیاری)
            bcc: لیست آدرس‌های رونوشت مخفی (اختیاری)
            attachments: لیست پیوست‌ها (اختیاری)
            fail_silently: اگر True باشد، خطاها را نادیده می‌گیرد

        Returns:
            bool: نتیجه ارسال ایمیل (موفق یا ناموفق)
        """
        if not to_emails:
            logger.warning("تلاش برای ارسال ایمیل بدون گیرنده")
            return False

        # تبدیل تک ایمیل به لیست
        if isinstance(to_emails, str):
            to_emails = [to_emails]

        # تنظیم ایمیل فرستنده
        if not from_email:
            from_email = self.from_email

        try:
            # اگر پیام HTML موجود است، از EmailMultiAlternatives استفاده کنید
            if html_message:
                if self.async_mode:
                    # ارسال ایمیل به صورت غیرهمزمان
                    thread = threading.Thread(
                        target=self._send_html_email,
                        args=(
                        subject, message, html_message, from_email, to_emails, cc, bcc, attachments, fail_silently)
                    )
                    thread.start()
                    return True
                else:
                    # ارسال ایمیل به صورت همزمان
                    return self._send_html_email(subject, message, html_message, from_email, to_emails, cc, bcc,
                                                 attachments, fail_silently)
            else:
                # ارسال ایمیل متنی ساده
                if self.async_mode:
                    # ارسال ایمیل به صورت غیرهمزمان
                    thread = threading.Thread(
                        target=self._send_plain_email,
                        args=(subject, message, from_email, to_emails, fail_silently)
                    )
                    thread.start()
                    return True
                else:
                    # ارسال ایمیل به صورت همزمان
                    return self._send_plain_email(subject, message, from_email, to_emails, fail_silently)
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل: {str(e)}")

            # تلاش مجدد با تنظیمات جایگزین
            if self.fallback_settings and not self.connection:
                return self._send_with_fallback(subject, to_emails, message, html_message, from_email, cc, bcc,
                                                attachments, fail_silently)

            if not fail_silently:
                raise

            return False

    def _send_plain_email(self, subject, message, from_email, to_emails, fail_silently=False):
        """ارسال ایمیل متنی ساده"""
        try:
            sent = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=to_emails,
                connection=self.connection,
                fail_silently=fail_silently
            )
            success = sent > 0
            if success:
                logger.info(f"ایمیل با موضوع '{subject}' به {', '.join(to_emails)} ارسال شد")
            else:
                logger.warning(f"ارسال ایمیل با موضوع '{subject}' به {', '.join(to_emails)} ناموفق بود")
            return success
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل متنی: {str(e)}")
            if not fail_silently:
                raise
            return False

    def _send_html_email(self, subject, text_content, html_content, from_email, to_emails, cc=None, bcc=None,
                         attachments=None, fail_silently=False):
        """ارسال ایمیل HTML"""
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_emails,
                cc=cc,
                bcc=bcc,
                connection=self.connection
            )

            email.attach_alternative(html_content, "text/html")

            # افزودن پیوست‌ها
            if attachments:
                for attachment in attachments:
                    # پیوست می‌تواند دیکشنری با کلیدهای content, filename و mimetype باشد
                    email.attach(
                        filename=attachment.get('filename'),
                        content=attachment.get('content'),
                        mimetype=attachment.get('mimetype')
                    )

            success = email.send(fail_silently=fail_silently) > 0
            if success:
                logger.info(f"ایمیل HTML با موضوع '{subject}' به {', '.join(to_emails)} ارسال شد")
            else:
                logger.warning(f"ارسال ایمیل HTML با موضوع '{subject}' به {', '.join(to_emails)} ناموفق بود")
            return success
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل HTML: {str(e)}")
            if not fail_silently:
                raise
            return False

    def _send_with_fallback(self, subject, to_emails, message, html_message, from_email, cc, bcc, attachments,
                            fail_silently):
        """تلاش مجدد با تنظیمات جایگزین"""
        try:
            logger.info("تلاش برای ارسال ایمیل با تنظیمات جایگزین")

            # ایجاد اتصال با تنظیمات جایگزین
            connection = get_connection(
                backend=self.fallback_settings.get('EMAIL_BACKEND'),
                host=self.fallback_settings.get('EMAIL_HOST'),
                port=self.fallback_settings.get('EMAIL_PORT'),
                username=self.fallback_settings.get('EMAIL_HOST_USER'),
                password=self.fallback_settings.get('EMAIL_HOST_PASSWORD'),
                use_tls=self.fallback_settings.get('EMAIL_USE_TLS', False),
                fail_silently=fail_silently
            )

            # ایجاد نمونه جدید با اتصال جایگزین
            fallback_service = EmailService(connection=connection)

            # ارسال ایمیل با اتصال جایگزین
            return fallback_service.send_email(
                subject=subject,
                to_emails=to_emails,
                message=message,
                html_message=html_message,
                from_email=from_email,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                fail_silently=fail_silently
            )
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل با تنظیمات جایگزین: {str(e)}")
            if not fail_silently:
                raise
            return False

    def send_template_email(self,
                            subject: str,
                            to_emails: Union[str, List[str]],
                            template_name: str,
                            context: Dict = None,
                            from_email: Optional[str] = None,
                            cc: Optional[List[str]] = None,
                            bcc: Optional[List[str]] = None,
                            attachments: Optional[List[Dict]] = None,
                            fail_silently: bool = False) -> bool:
        """
        ارسال ایمیل با استفاده از قالب Django.

        Args:
            subject: موضوع ایمیل
            to_emails: آدرس یا لیستی از آدرس‌های ایمیل گیرندگان
            template_name: نام قالب (بدون پسوند .html)
            context: داده‌های مورد نیاز قالب (اختیاری)
            from_email: آدرس فرستنده (اختیاری، پیش‌فرض از تنظیمات)
            cc: لیست آدرس‌های رونوشت (اختیاری)
            bcc: لیست آدرس‌های رونوشت مخفی (اختیاری)
            attachments: لیست پیوست‌ها (اختیاری)
            fail_silently: اگر True باشد، خطاها را نادیده می‌گیرد

        Returns:
            bool: نتیجه ارسال ایمیل (موفق یا ناموفق)
        """
        if context is None:
            context = {}

        # افزودن نام سایت به context
        context['site_name'] = getattr(settings, 'SITE_NAME', 'Ma2tA')
        context['site_url'] = getattr(settings, 'SITE_URL', 'https://ma2ta.com')

        try:
            # ساخت محتوای HTML از قالب
            html_message = render_to_string(f'emails/{template_name}.html', context)

            # ایجاد نسخه متنی از محتوای HTML
            plain_message = strip_tags(html_message)

            # ارسال ایمیل
            return self.send_email(
                subject=subject,
                to_emails=to_emails,
                message=plain_message,
                html_message=html_message,
                from_email=from_email,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                fail_silently=fail_silently
            )
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل قالب '{template_name}': {str(e)}")
            if not fail_silently:
                raise
            return False

    # روش‌های کاربردی برای انواع خاص ایمیل‌ها

    def send_welcome_email(self, user, fail_silently=False):
        """ارسال ایمیل خوش‌آمدگویی به کاربر جدید"""
        context = {
            'user': user,
            'login_url': f"{settings.SITE_URL}/login/",
        }

        return self.send_template_email(
            subject="به Ma2tA خوش آمدید!",
            to_emails=user.email,
            template_name="welcome",
            context=context,
            fail_silently=fail_silently
        )

    def send_verification_email(self, user, verification_token, fail_silently=False):
        """ارسال ایمیل تأیید حساب کاربری"""
        verification_url = f"{settings.SITE_URL}/verify-email/{verification_token}/"

        context = {
            'user': user,
            'verification_url': verification_url,
            'token': verification_token,
            'expiry_hours': 24,  # زمان انقضای توکن
        }

        return self.send_template_email(
            subject="تأیید حساب کاربری Ma2tA",
            to_emails=user.email,
            template_name="email_verification",
            context=context,
            fail_silently=fail_silently
        )

    def send_password_reset_email(self, user, reset_token, fail_silently=False):
        """ارسال ایمیل بازیابی رمز عبور"""
        reset_url = f"{settings.SITE_URL}/reset-password/{reset_token}/"

        context = {
            'user': user,
            'reset_url': reset_url,
            'token': reset_token,
            'expiry_hours': 1,  # زمان انقضای توکن
        }

        return self.send_template_email(
            subject="بازیابی رمز عبور Ma2tA",
            to_emails=user.email,
            template_name="password_reset",
            context=context,
            fail_silently=fail_silently
        )

    def send_order_confirmation_email(self, order, fail_silently=False):
        """ارسال ایمیل تأیید سفارش"""
        context = {
            'user': order.user,
            'order': order,
            'order_items': order.items.all(),
            'order_url': f"{settings.SITE_URL}/orders/{order.id}/",
        }

        return self.send_template_email(
            subject=f"تأیید سفارش #{order.order_number}",
            to_emails=order.user.email,
            template_name="order_confirmation",
            context=context,
            fail_silently=fail_silently
        )

    def send_artist_new_sale_email(self, artist, order_item, fail_silently=False):
        """ارسال ایمیل اطلاع‌رسانی فروش جدید به هنرمند"""
        context = {
            'artist': artist,
            'artwork': order_item.artwork,
            'order_item': order_item,
            'order': order_item.order,
            'dashboard_url': f"{settings.SITE_URL}/artist/dashboard/sales/",
        }

        return self.send_template_email(
            subject="فروش جدید اثر هنری در Ma2tA",
            to_emails=artist.user.email,
            template_name="artist_new_sale",
            context=context,
            fail_silently=fail_silently
        )