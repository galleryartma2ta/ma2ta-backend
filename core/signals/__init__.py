# core/signals/__init__.py

from core.signals.handlers import (
    # سیگنال‌های کاربران
    user_post_save,
    user_logged_in_handler,
    user_logged_out_handler,

    # سیگنال‌های آثار هنری
    artwork_post_save,
    artwork_status_changed,

    # سیگنال‌های سفارش‌ها
    order_post_save,
    order_status_changed,
    order_paid_handler,

    # سیگنال‌های پرداخت
    payment_post_save,
    payment_succeeded,
    payment_failed,

    # سیگنال‌های هنرمندان
    artist_profile_post_save,
    artist_verified_handler,

    # سیگنال‌های گالری و نمایشگاه
    exhibition_post_save,
    exhibition_about_to_start,

    # سیگنال‌های وبلاگ
    blogpost_post_save,

    # سیگنال‌های اعلان‌ها
    notification_post_save,
)


# وصل کردن سیگنال‌ها به هندلرها
def connect_signals():
    """متصل کردن تمام سیگنال‌ها به هندلرهای مربوطه"""
    from django.contrib.auth import signals as auth_signals
    from django.db.models.signals import post_save, pre_save, pre_delete, post_delete, m2m_changed
    from django.dispatch import receiver

    # واردسازی مدل‌ها
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        from apps.products.models import Artwork
        from apps.orders.models import Order
        from apps.payments.models import Payment
        from apps.artists.models import ArtistProfile
        from apps.gallery.models import Exhibition
        from apps.blog.models import BlogPost
        from apps.notifications.models import Notification
    except ImportError:
        # در صورتی که مدل‌ها هنوز تعریف نشده‌اند،
        # سیگنال‌ها را متصل نمی‌کنیم
        return

    # سیگنال‌های کاربران
    post_save.connect(user_post_save, sender=User)
    auth_signals.user_logged_in.connect(user_logged_in_handler)
    auth_signals.user_logged_out.connect(user_logged_out_handler)

    # سیگنال‌های آثار هنری
    post_save.connect(artwork_post_save, sender=Artwork)

    # سیگنال‌های سفارش‌ها
    post_save.connect(order_post_save, sender=Order)

    # سیگنال‌های پرداخت
    post_save.connect(payment_post_save, sender=Payment)

    # سیگنال‌های هنرمندان
    post_save.connect(artist_profile_post_save, sender=ArtistProfile)

    # سیگنال‌های گالری و نمایشگاه
    post_save.connect(exhibition_post_save, sender=Exhibition)

    # سیگنال‌های وبلاگ
    post_save.connect(blogpost_post_save, sender=BlogPost)

    # سیگنال‌های اعلان‌ها
    post_save.connect(notification_post_save, sender=Notification)