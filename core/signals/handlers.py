# core/signals/handlers.py

import logging
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.contrib.auth import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# تنظیم لاگر
logger = logging.getLogger('signals')


# -------------------------------------------------------------------------
# سیگنال‌های کاربران
# -------------------------------------------------------------------------

def user_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره کاربر

    این هندلر زمانی که یک کاربر ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (User)
        instance: نمونه مدل کاربر
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی کاربر
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        # اگر کاربر جدید ایجاد شده است
        if created:
            logger.info(f"کاربر جدید ایجاد شد: {instance.username} (ID: {instance.id})")

            # ایجاد پروفایل کاربر
            if hasattr(instance, 'create_profile'):
                instance.create_profile()

            # ارسال ایمیل خوش‌آمدگویی
            if instance.email and getattr(settings, 'SEND_WELCOME_EMAIL', True):
                from core.services import EmailService
                email_service = EmailService()
                try:
                    email_service.send_welcome_email(instance, fail_silently=True)
                    logger.info(f"ایمیل خوش‌آمدگویی برای کاربر {instance.email} ارسال شد")
                except Exception as e:
                    logger.error(f"خطا در ارسال ایمیل خوش‌آمدگویی: {str(e)}")
        else:
            # اگر کاربر به‌روزرسانی شده است
            logger.debug(f"کاربر به‌روزرسانی شد: {instance.username} (ID: {instance.id})")

    except Exception as e:
        logger.error(f"خطا در سیگنال user_post_save: {str(e)}")


def user_logged_in_handler(sender, request, user, **kwargs):
    """
    هندلر سیگنال ورود کاربر

    این هندلر زمانی که یک کاربر وارد سیستم می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال
        request: شیء درخواست HTTP
        user: کاربر وارد شده
    """
    try:
        # ثبت آخرین ورود
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        logger.info(f"کاربر وارد شد: {user.username} (ID: {user.id})")

        # افزودن IP آخرین ورود
        if hasattr(user, 'profile'):
            ip_address = request.META.get('REMOTE_ADDR', '')
            if ip_address:
                user.profile.last_login_ip = ip_address
                user.profile.save(update_fields=['last_login_ip'])

    except Exception as e:
        logger.error(f"خطا در سیگنال user_logged_in_handler: {str(e)}")


def user_logged_out_handler(sender, request, user, **kwargs):
    """
    هندلر سیگنال خروج کاربر

    این هندلر زمانی که یک کاربر از سیستم خارج می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال
        request: شیء درخواست HTTP
        user: کاربر خارج شده
    """
    try:
        if user:
            logger.info(f"کاربر خارج شد: {user.username} (ID: {user.id})")
    except Exception as e:
        logger.error(f"خطا در سیگنال user_logged_out_handler: {str(e)}")


# -------------------------------------------------------------------------
# سیگنال‌های آثار هنری
# -------------------------------------------------------------------------

def artwork_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره اثر هنری

    این هندلر زمانی که یک اثر هنری ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Artwork)
        instance: نمونه مدل اثر هنری
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی اثر هنری
    """
    try:
        # اگر اثر هنری جدید ایجاد شده است
        if created:
            logger.info(f"اثر هنری جدید ایجاد شد: {instance.title} (ID: {instance.id}) - هنرمند: {instance.artist}")

            # به‌روزرسانی تعداد آثار هنرمند
            if hasattr(instance.artist, 'update_artwork_count'):
                instance.artist.update_artwork_count()

            # اگر وضعیت اثر منتشر شده است، اعلان به کاربران علاقه‌مند ارسال کنید
            if instance.status == 'published' and hasattr(instance, 'notify_followers'):
                instance.notify_followers()
        else:
            # اگر اثر هنری به‌روزرسانی شده است
            logger.debug(f"اثر هنری به‌روزرسانی شد: {instance.title} (ID: {instance.id})")

    except Exception as e:
        logger.error(f"خطا در سیگنال artwork_post_save: {str(e)}")


def artwork_status_changed(sender, instance, **kwargs):
    """
    هندلر سیگنال تغییر وضعیت اثر هنری

    این هندلر زمانی که وضعیت یک اثر هنری تغییر می‌کند اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Artwork)
        instance: نمونه مدل اثر هنری
    """
    try:
        # بررسی آیا وضعیت تغییر کرده است
        if not hasattr(instance, '_original_status'):
            return

        original_status = instance._original_status
        current_status = instance.status

        if original_status != current_status:
            logger.info(f"وضعیت اثر هنری تغییر کرد: {instance.title} (ID: {instance.id}) "
                        f"از '{original_status}' به '{current_status}'")

            # اگر اثر فروخته شده است
            if current_status == 'sold' and original_status != 'sold':
                # اطلاع‌رسانی به هنرمند
                if hasattr(instance, 'notify_artist_about_sale'):
                    instance.notify_artist_about_sale()

            # اگر اثر ویژه شده است
            elif current_status == 'featured' and original_status != 'featured':
                # اطلاع‌رسانی به هنرمند
                if hasattr(instance, 'notify_artist_about_featuring'):
                    instance.notify_artist_about_featuring()

    except Exception as e:
        logger.error(f"خطا در سیگنال artwork_status_changed: {str(e)}")


# -------------------------------------------------------------------------
# سیگنال‌های سفارش‌ها
# -------------------------------------------------------------------------

def order_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره سفارش

    این هندلر زمانی که یک سفارش ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Order)
        instance: نمونه مدل سفارش
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی سفارش
    """
    try:
        # اگر سفارش جدید ایجاد شده است
        if created:
            logger.info(f"سفارش جدید ایجاد شد: {instance.order_number} (ID: {instance.id}) - کاربر: {instance.user}")

            # ایجاد فاکتور برای سفارش
            if hasattr(instance, 'create_invoice'):
                instance.create_invoice()

            # ارسال ایمیل تأیید سفارش به کاربر
            if hasattr(instance, 'send_confirmation_email'):
                instance.send_confirmation_email()
        else:
            # اگر سفارش به‌روزرسانی شده است
            logger.debug(f"سفارش به‌روزرسانی شد: {instance.order_number} (ID: {instance.id})")

    except Exception as e:
        logger.error(f"خطا در سیگنال order_post_save: {str(e)}")


def order_status_changed(sender, instance, **kwargs):
    """
    هندلر سیگنال تغییر وضعیت سفارش

    این هندلر زمانی که وضعیت یک سفارش تغییر می‌کند اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Order)
        instance: نمونه مدل سفارش
    """
    try:
        # بررسی آیا وضعیت تغییر کرده است
        if not hasattr(instance, '_original_status'):
            return

        original_status = instance._original_status
        current_status = instance.status

        if original_status != current_status:
            logger.info(f"وضعیت سفارش تغییر کرد: {instance.order_number} (ID: {instance.id}) "
                        f"از '{original_status}' به '{current_status}'")

            # اطلاع‌رسانی به کاربر
            if hasattr(instance, 'notify_user_about_status_change'):
                instance.notify_user_about_status_change(original_status, current_status)

            # اگر سفارش تحویل داده شده است
            if current_status == 'delivered' and original_status != 'delivered':
                # ارسال ایمیل درخواست نظرسنجی
                if hasattr(instance, 'send_feedback_request'):
                    instance.send_feedback_request()

                # وضعیت آثار هنری را به "فروخته شده" تغییر دهید
                if hasattr(instance, 'mark_artworks_as_sold'):
                    instance.mark_artworks_as_sold()

            # اگر سفارش لغو شده است
            elif current_status == 'canceled' and original_status != 'canceled':
                # بازگرداندن آثار هنری به وضعیت قبلی
                if hasattr(instance, 'revert_artworks_status'):
                    instance.revert_artworks_status()

    except Exception as e:
        logger.error(f"خطا در سیگنال order_status_changed: {str(e)}")


def order_paid_handler(sender, instance, **kwargs):
    """
    هندلر سیگنال پرداخت سفارش

    این هندلر زمانی که یک سفارش پرداخت می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال
        instance: نمونه مدل سفارش
    """
    try:
        logger.info(f"سفارش پرداخت شد: {instance.order_number} (ID: {instance.id})")

        # تغییر وضعیت سفارش به "در حال پردازش"
        if instance.status == 'pending':
            instance.status = 'processing'
            instance.save(update_fields=['status'])

        # ارسال تأییدیه پرداخت به کاربر
        if hasattr(instance, 'send_payment_confirmation'):
            instance.send_payment_confirmation()

        # اطلاع‌رسانی به هنرمندان
        if hasattr(instance, 'notify_artists'):
            instance.notify_artists()

    except Exception as e:
        logger.error(f"خطا در سیگنال order_paid_handler: {str(e)}")


# -------------------------------------------------------------------------
# سیگنال‌های پرداخت
# -------------------------------------------------------------------------

def payment_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره پرداخت

    این هندلر زمانی که یک پرداخت ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Payment)
        instance: نمونه مدل پرداخت
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی پرداخت
    """
    try:
        # اگر پرداخت جدید ایجاد شده است
        if created:
            logger.info(f"پرداخت جدید ایجاد شد: {instance.payment_id} (ID: {instance.id}) - "
                        f"مبلغ: {instance.amount} - وضعیت: {instance.status}")
        else:
            # اگر پرداخت به‌روزرسانی شده است
            logger.debug(f"پرداخت به‌روزرسانی شد: {instance.payment_id} (ID: {instance.id}) - "
                         f"وضعیت: {instance.status}")

    except Exception as e:
        logger.error(f"خطا در سیگنال payment_post_save: {str(e)}")


def payment_succeeded(sender, instance, **kwargs):
    """
    هندلر سیگنال موفقیت پرداخت

    این هندلر زمانی که یک پرداخت موفقیت‌آمیز است اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Payment)
        instance: نمونه مدل پرداخت
    """
    try:
        logger.info(f"پرداخت موفق: {instance.payment_id} (ID: {instance.id}) - "
                    f"مبلغ: {instance.amount}")

        # بررسی آیا پرداخت مربوط به سفارش است
        if hasattr(instance, 'order') and instance.order:
            # اجرای هندلر پرداخت سفارش
            order_paid_handler(sender, instance.order)

    except Exception as e:
        logger.error(f"خطا در سیگنال payment_succeeded: {str(e)}")


def payment_failed(sender, instance, **kwargs):
    """
    هندلر سیگنال شکست پرداخت

    این هندلر زمانی که یک پرداخت ناموفق است اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Payment)
        instance: نمونه مدل پرداخت
    """
    try:
        logger.warning(f"پرداخت ناموفق: {instance.payment_id} (ID: {instance.id}) - "
                       f"مبلغ: {instance.amount} - خطا: {instance.error_message}")

        # اطلاع‌رسانی به کاربر
        if hasattr(instance, 'notify_user_about_failure'):
            instance.notify_user_about_failure()

    except Exception as e:
        logger.error(f"خطا در سیگنال payment_failed: {str(e)}")


# -------------------------------------------------------------------------
# سیگنال‌های هنرمندان
# -------------------------------------------------------------------------

def artist_profile_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره پروفایل هنرمند

    این هندلر زمانی که یک پروفایل هنرمند ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (ArtistProfile)
        instance: نمونه مدل پروفایل هنرمند
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی پروفایل هنرمند
    """
    try:
        # اگر پروفایل هنرمند جدید ایجاد شده است
        if created:
            logger.info(f"پروفایل هنرمند جدید ایجاد شد: {instance.user.username} (ID: {instance.id})")

            # ایجاد گالری پیش‌فرض برای هنرمند
            if hasattr(instance, 'create_default_gallery'):
                instance.create_default_gallery()

            # ارسال ایمیل خوش‌آمدگویی به هنرمند
            if hasattr(instance.user, 'email') and getattr(settings, 'SEND_ARTIST_WELCOME_EMAIL', True):
                from core.services import EmailService
                email_service = EmailService()
                try:
                    # فرض می‌کنیم یک متد send_artist_welcome_email در EmailService وجود دارد
                    if hasattr(email_service, 'send_artist_welcome_email'):
                        email_service.send_artist_welcome_email(instance.user, fail_silently=True)
                        logger.info(f"ایمیل خوش‌آمدگویی هنرمند برای کاربر {instance.user.email} ارسال شد")
                except Exception as e:
                    logger.error(f"خطا در ارسال ایمیل خوش‌آمدگویی هنرمند: {str(e)}")
        else:
            # اگر پروفایل هنرمند به‌روزرسانی شده است
            logger.debug(f"پروفایل هنرمند به‌روزرسانی شد: {instance.user.username} (ID: {instance.id})")

    except Exception as e:
        logger.error(f"خطا در سیگنال artist_profile_post_save: {str(e)}")


def artist_verified_handler(sender, instance, **kwargs):
    """
    هندلر سیگنال تأیید هنرمند

    این هندلر زمانی که یک هنرمند تأیید می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (ArtistProfile)
        instance: نمونه مدل پروفایل هنرمند
    """
    try:
        # بررسی آیا وضعیت تأیید تغییر کرده است
        if not hasattr(instance, '_original_is_verified'):
            return

        original_is_verified = instance._original_is_verified
        current_is_verified = instance.is_verified

        if not original_is_verified and current_is_verified:
            logger.info(f"هنرمند تأیید شد: {instance.user.username} (ID: {instance.id})")

            # ارسال ایمیل تبریک به هنرمند
            if hasattr(instance.user, 'email'):
                from core.services import EmailService
                email_service = EmailService()
                try:
                    # فرض می‌کنیم یک متد send_artist_verification_email در EmailService وجود دارد
                    if hasattr(email_service, 'send_artist_verification_email'):
                        email_service.send_artist_verification_email(instance.user, fail_silently=True)
                        logger.info(f"ایمیل تأیید هنرمند برای کاربر {instance.user.email} ارسال شد")
                except Exception as e:
                    logger.error(f"خطا در ارسال ایمیل تأیید هنرمند: {str(e)}")

    except Exception as e:
        logger.error(f"خطا در سیگنال artist_verified_handler: {str(e)}")


# -------------------------------------------------------------------------
# سیگنال‌های گالری و نمایشگاه
# -------------------------------------------------------------------------

def exhibition_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره نمایشگاه

    این هندلر زمانی که یک نمایشگاه ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Exhibition)
        instance: نمونه مدل نمایشگاه
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی نمایشگاه
    """
    try:
        # اگر نمایشگاه جدید ایجاد شده است
        if created:
            logger.info(f"نمایشگاه جدید ایجاد شد: {instance.title} (ID: {instance.id})")

            # زمان‌بندی یادآوری‌های نمایشگاه
            if hasattr(instance, 'schedule_reminders'):
                instance.schedule_reminders()

            # اطلاع‌رسانی به هنرمندان شرکت‌کننده
            if hasattr(instance, 'notify_participating_artists'):
                instance.notify_participating_artists()
        else:
            # اگر نمایشگاه به‌روزرسانی شده است
            logger.debug(f"نمایشگاه به‌روزرسانی شد: {instance.title} (ID: {instance.id})")

    except Exception as e:
        logger.error(f"خطا در سیگنال exhibition_post_save: {str(e)}")


def exhibition_about_to_start(sender, instance, **kwargs):
    """
    هندلر سیگنال شروع قریب‌الوقوع نمایشگاه

    این هندلر زمانی که یک نمایشگاه در آستانه شروع است اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Exhibition)
        instance: نمونه مدل نمایشگاه
    """
    try:
        logger.info(f"نمایشگاه در آستانه شروع: {instance.title} (ID: {instance.id}) - "
                    f"تاریخ شروع: {instance.start_date}")

        # ارسال یادآوری به کاربران علاقه‌مند
        if hasattr(instance, 'send_reminders_to_interested_users'):
            instance.send_reminders_to_interested_users()

    except Exception as e:
        logger.error(f"خطا در سیگنال exhibition_about_to_start: {str(e)}")


# -------------------------------------------------------------------------
# سیگنال‌های وبلاگ
# -------------------------------------------------------------------------

def blogpost_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره پست وبلاگ

    این هندلر زمانی که یک پست وبلاگ ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (BlogPost)
        instance: نمونه مدل پست وبلاگ
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی پست وبلاگ
    """
    try:
        # اگر پست وبلاگ جدید ایجاد شده است
        if created:
            logger.info(f"پست وبلاگ جدید ایجاد شد: {instance.title} (ID: {instance.id})")
        else:
            # اگر پست وبلاگ به‌روزرسانی شده است
            logger.debug(f"پست وبلاگ به‌روزرسانی شد: {instance.title} (ID: {instance.id})")

            # اگر وضعیت از پیش‌نویس به منتشر شده تغییر کرده، اعلان به دنبال‌کنندگان ارسال کنید
            if hasattr(instance, '_original_status') and hasattr(instance, 'status'):
                original_status = instance._original_status
                current_status = instance.status

                if original_status == 'draft' and current_status == 'published':
                    logger.info(f"پست وبلاگ منتشر شد: {instance.title} (ID: {instance.id})")

                    # اعلان به دنبال‌کنندگان
                    if hasattr(instance, 'notify_subscribers'):
                        instance.notify_subscribers()

    except Exception as e:
        logger.error(f"خطا در سیگنال blogpost_post_save: {str(e)}")


# -------------------------------------------------------------------------
# سیگنال‌های اعلان‌ها
# -------------------------------------------------------------------------

def notification_post_save(sender, instance, created, **kwargs):
    """
    هندلر سیگنال پس از ذخیره اعلان

    این هندلر زمانی که یک اعلان ایجاد یا به‌روزرسانی می‌شود اجرا می‌شود.

    Args:
        sender: مدل ارسال‌کننده سیگنال (Notification)
        instance: نمونه مدل اعلان
        created: بولین نشان‌دهنده ایجاد یا به‌روزرسانی اعلان
    """
    try:
        # اگر اعلان جدید ایجاد شده است
        if created:
            logger.debug(f"اعلان جدید ایجاد شد (ID: {instance.id}) - "
                         f"کاربر: {instance.user} - نوع: {instance.notification_type}")

            # ارسال اعلان به کاربر از طریق وب‌سوکت
            if hasattr(instance, 'send_ws_notification'):
                instance.send_ws_notification()

            # ارسال ایمیل برای اعلان‌های مهم
            if instance.is_important and hasattr(instance.user, 'email') and instance.user.email:
                # ارسال ایمیل اعلان به کاربر
                if hasattr(instance, 'send_email_notification'):
                    instance.send_email_notification()

    except Exception as e:
        logger.error(f"خطا در سیگنال notification_post_save: {str(e)}")