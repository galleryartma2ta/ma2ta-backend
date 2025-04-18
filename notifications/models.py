# notifications/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Notification(models.Model):
    """مدل اطلاع‌رسانی‌ها"""

    TYPE_CHOICES = (
        ('info', _('اطلاعیه')),
        ('success', _('موفقیت')),
        ('warning', _('هشدار')),
        ('error', _('خطا')),
    )

    CATEGORY_CHOICES = (
        ('order', _('سفارش')),
        ('payment', _('پرداخت')),
        ('auction', _('حراجی')),
        ('exhibition', _('نمایشگاه')),
        ('product', _('محصول')),
        ('account', _('حساب کاربری')),
        ('system', _('سیستمی')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('کاربر')
    )

    title = models.CharField(_('عنوان'), max_length=200)
    message = models.TextField(_('پیام'))
    type = models.CharField(_('نوع'), max_length=10, choices=TYPE_CHOICES, default='info')
    category = models.CharField(_('دسته‌بندی'), max_length=20, choices=CATEGORY_CHOICES, default='system')

    is_read = models.BooleanField(_('خوانده شده'), default=False)
    read_at = models.DateTimeField(_('تاریخ خواندن'), null=True, blank=True)

    related_url = models.CharField(_('لینک مرتبط'), max_length=255, blank=True)
    data = models.JSONField(_('داده‌های اضافی'), default=dict, blank=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)

    class Meta:
        verbose_name = _('اطلاع‌رسانی')
        verbose_name_plural = _('اطلاع‌رسانی‌ها')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} - {self.title} - {self.user.email}"

    def mark_as_read(self):
        """علامت‌گذاری اطلاع‌رسانی به عنوان خوانده شده"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class BulkNotification(models.Model):
    """اطلاع‌رسانی گروهی"""

    title = models.CharField(_('عنوان'), max_length=200)
    message = models.TextField(_('پیام'))

    type = models.CharField(
        _('نوع'),
        max_length=10,
        choices=Notification.TYPE_CHOICES,
        default='info'
    )
    category = models.CharField(
        _('دسته‌بندی'),
        max_length=20,
        choices=Notification.CATEGORY_CHOICES,
        default='system'
    )

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='bulk_notifications',
        verbose_name=_('کاربران'),
        blank=True
    )

    is_sent = models.BooleanField(_('ارسال شده'), default=False)
    sent_at = models.DateTimeField(_('تاریخ ارسال'), null=True, blank=True)

    related_url = models.CharField(_('لینک مرتبط'), max_length=255, blank=True)
    data = models.JSONField(_('داده‌های اضافی'), default=dict, blank=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)

    class Meta:
        verbose_name = _('اطلاع‌رسانی گروهی')
        verbose_name_plural = _('اطلاع‌رسانی‌های گروهی')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} - {self.title}"

    def send_notifications(self):
        """ارسال اطلاع‌رسانی به تمام کاربران"""
        from django.utils import timezone

        # Check if already sent
        if self.is_sent:
            return

        # Create individual notifications for each user
        for user in self.users.all():
            Notification.objects.create(
                user=user,
                title=self.title,
                message=self.message,
                type=self.type,
                category=self.category,
                related_url=self.related_url,
                data=self.data
            )

        # Mark as sent
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()


class EmailSubscription(models.Model):
    """اشتراک خبرنامه ایمیلی"""

    email = models.EmailField(_('ایمیل'), unique=True)
    is_active = models.BooleanField(_('فعال'), default=True)
    first_name = models.CharField(_('نام'), max_length=100, blank=True)
    last_name = models.CharField(_('نام خانوادگی'), max_length=100, blank=True)

    interests = models.JSONField(_('علاقه‌مندی‌ها'), default=list, blank=True)
    subscription_date = models.DateTimeField(_('تاریخ اشتراک'), auto_now_add=True)
    unsubscribe_date = models.DateTimeField(_('تاریخ لغو اشتراک'), null=True, blank=True)

    class Meta:
        verbose_name = _('اشتراک خبرنامه')
        verbose_name_plural = _('اشتراک‌های خبرنامه')
        ordering = ['-subscription_date']

    def __str__(self):
        return self.email


class EmailTemplate(models.Model):
    """قالب‌های ایمیل"""

    USAGE_CHOICES = (
        ('order_confirmation', _('تایید سفارش')),
        ('payment_success', _('پرداخت موفق')),
        ('shipping_confirmation', _('تایید ارسال')),
        ('account_activation', _('فعال‌سازی حساب کاربری')),
        ('password_reset', _('بازیابی رمز عبور')),
        ('newsletter', _('خبرنامه')),
        ('auction_invitation', _('دعوت به حراجی')),
        ('exhibition_invitation', _('دعوت به نمایشگاه')),
        ('custom', _('سفارشی')),
    )

    name = models.CharField(_('نام'), max_length=100)
    code = models.CharField(_('کد'), max_length=50, unique=True)
    usage = models.CharField(_('مورد استفاده'), max_length=30, choices=USAGE_CHOICES)

    subject = models.CharField(_('موضوع'), max_length=200)
    content = models.TextField(_('محتوا'))

    is_active = models.BooleanField(_('فعال'), default=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('قالب ایمیل')
        verbose_name_plural = _('قالب‌های ایمیل')

    def __str__(self):
        return self.name


class SMSTemplate(models.Model):
    """قالب‌های پیامک"""

    USAGE_CHOICES = (
        ('order_confirmation', _('تایید سفارش')),
        ('payment_success', _('پرداخت موفق')),
        ('shipping_confirmation', _('تایید ارسال')),
        ('verification_code', _('کد تایید')),
        ('password_reset', _('بازیابی رمز عبور')),
        ('auction_notification', _('اطلاع‌رسانی حراجی')),
        ('exhibition_notification', _('اطلاع‌رسانی نمایشگاه')),
        ('custom', _('سفارشی')),
    )

    name = models.CharField(_('نام'), max_length=100)
    code = models.CharField(_('کد'), max_length=50, unique=True)
    usage = models.CharField(_('مورد استفاده'), max_length=30, choices=USAGE_CHOICES)

    content = models.TextField(_('محتوا'))

    is_active = models.BooleanField(_('فعال'), default=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('قالب پیامک')
        verbose_name_plural = _('قالب‌های پیامک')

    def __str__(self):
        return self.name