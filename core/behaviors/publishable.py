# core/behaviors/publishable.py

import datetime
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PublishableQuerySet(QuerySet):
    """
    کوئری‌ست سفارشی برای مدل‌های قابل انتشار.
    این کوئری‌ست متدهایی برای فیلتر کردن آیتم‌ها بر اساس وضعیت انتشار فراهم می‌کند.
    """

    def published(self):
        """
        فیلتر کردن فقط آیتم‌های منتشر شده و در دسترس

        یک آیتم زمانی منتشر شده و در دسترس است که:
        1. وضعیت آن "منتشر شده" باشد
        2. تاریخ انتشار آن گذشته باشد یا برابر با زمان فعلی باشد
        3. تاریخ انقضای آن در آینده باشد یا تنظیم نشده باشد
        """
        now = timezone.now()

        return self.filter(
            models.Q(status='published'),
            models.Q(publish_date__lte=now),
            models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gt=now)
        )

    def draft(self):
        """فیلتر کردن فقط آیتم‌های پیش‌نویس"""
        return self.filter(status='draft')

    def archived(self):
        """فیلتر کردن فقط آیتم‌های بایگانی شده"""
        return self.filter(status='archived')

    def featured(self):
        """فیلتر کردن فقط آیتم‌های ویژه"""
        now = timezone.now()

        return self.filter(
            models.Q(status='published'),
            models.Q(is_featured=True),
            models.Q(publish_date__lte=now),
            models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gt=now)
        )

    def scheduled(self):
        """
        فیلتر کردن آیتم‌هایی که برای انتشار در آینده زمان‌بندی شده‌اند
        """
        now = timezone.now()

        return self.filter(
            models.Q(status='published'),
            models.Q(publish_date__gt=now)
        )

    def expired(self):
        """
        فیلتر کردن آیتم‌هایی که تاریخ انقضای آن‌ها گذشته است
        """
        now = timezone.now()

        return self.filter(
            models.Q(expiry_date__lte=now),
            models.Q(expiry_date__isnull=False)
        )

    def visible(self):
        """
        فیلتر کردن آیتم‌های قابل نمایش (منتشر شده یا ویژه)
        """
        return self.published()

    def upcoming(self, days=None):
        """
        آیتم‌هایی که در آینده منتشر خواهند شد

        Args:
            days: تعداد روزهای آینده برای بررسی (اختیاری)
        """
        now = timezone.now()

        if days is not None:
            end_date = now + datetime.timedelta(days=days)
            return self.filter(
                models.Q(status='published'),
                models.Q(publish_date__gt=now),
                models.Q(publish_date__lte=end_date)
            )

        return self.filter(
            models.Q(status='published'),
            models.Q(publish_date__gt=now)
        )

    def recent(self, days=30):
        """
        آیتم‌های اخیراً منتشر شده

        Args:
            days: تعداد روزهای گذشته برای بررسی (پیش‌فرض: 30)
        """
        now = timezone.now()
        start_date = now - datetime.timedelta(days=days)

        return self.filter(
            models.Q(status='published'),
            models.Q(publish_date__gte=start_date),
            models.Q(publish_date__lte=now),
            models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gt=now)
        )


class PublishableMixin(models.Model):
    """
    میکسین مدل برای محتوای قابل انتشار

    این میکسین فیلدهای مورد نیاز برای مدیریت وضعیت انتشار را اضافه می‌کند:
    - وضعیت (پیش‌نویس، منتشر شده، بایگانی شده)
    - تاریخ انتشار
    - تاریخ انقضا
    - ویژگی ویژه بودن
    """
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (DRAFT, _('پیش‌نویس')),
        (PUBLISHED, _('منتشر شده')),
        (ARCHIVED, _('بایگانی شده')),
    ]

    # فیلدهای وضعیت انتشار
    status = models.CharField(
        _('وضعیت'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
        db_index=True
    )

    publish_date = models.DateTimeField(
        _('تاریخ انتشار'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('تاریخ و زمانی که این محتوا باید منتشر شود')
    )

    expiry_date = models.DateTimeField(
        _('تاریخ انقضا'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('تاریخ و زمانی که این محتوا باید منقضی شود')
    )

    is_featured = models.BooleanField(
        _('ویژه'),
        default=False,
        help_text=_('آیا این محتوا ویژه است')
    )

    # استفاده از کوئری‌ست سفارشی
    objects = PublishableQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ['-publish_date']

    def save(self, *args, **kwargs):
        """
        ذخیره و تنظیم خودکار تاریخ انتشار
        """
        # اگر وضعیت به منتشر شده تغییر کرده و تاریخ انتشار تنظیم نشده، آن را به زمان فعلی تنظیم می‌کنیم
        if self.status == self.PUBLISHED and not self.publish_date:
            self.publish_date = timezone.now()

        super().save(*args, **kwargs)

    def publish(self, commit=True):
        """
        انتشار محتوا

        تنظیم وضعیت به "منتشر شده" و تنظیم تاریخ انتشار به زمان فعلی (اگر تنظیم نشده باشد)

        Args:
            commit: ذخیره تغییرات در پایگاه داده (پیش‌فرض: True)
        """
        self.status = self.PUBLISHED

        if not self.publish_date:
            self.publish_date = timezone.now()

        if commit:
            self.save()

    def unpublish(self, commit=True):
        """
        لغو انتشار محتوا

        تغییر وضعیت به "پیش‌نویس" و حفظ تاریخ انتشار

        Args:
            commit: ذخیره تغییرات در پایگاه داده (پیش‌فرض: True)
        """
        self.status = self.DRAFT

        if commit:
            self.save()

    def archive(self, commit=True):
        """
        بایگانی محتوا

        تغییر وضعیت به "بایگانی شده"

        Args:
            commit: ذخیره تغییرات در پایگاه داده (پیش‌فرض: True)
        """
        self.status = self.ARCHIVED

        if commit:
            self.save()

    def feature(self, commit=True):
        """
        تنظیم محتوا به عنوان ویژه

        Args:
            commit: ذخیره تغییرات در پایگاه داده (پیش‌فرض: True)
        """
        self.is_featured = True

        if commit:
            self.save()

    def unfeature(self, commit=True):
        """
        حذف ویژگی ویژه بودن محتوا

        Args:
            commit: ذخیره تغییرات در پایگاه داده (پیش‌فرض: True)
        """
        self.is_featured = False

        if commit:
            self.save()

    def schedule_publish(self, publish_date, expiry_date=None, commit=True):
        """
        زمان‌بندی انتشار محتوا برای تاریخ مشخص

        Args:
            publish_date: تاریخ انتشار
            expiry_date: تاریخ انقضا (اختیاری)
            commit: ذخیره تغییرات در پایگاه داده (پیش‌فرض: True)
        """
        self.status = self.PUBLISHED
        self.publish_date = publish_date

        if expiry_date:
            self.expiry_date = expiry_date

        if commit:
            self.save()

    def set_expiry(self, expiry_date, commit=True):
        """
        تنظیم تاریخ انقضای محتوا

        Args:
            expiry_date: تاریخ انقضا
            commit: ذخیره تغییرات در پایگاه داده (پیش‌فرض: True)
        """
        self.expiry_date = expiry_date

        if commit:
            self.save()

    @property
    def is_published(self):
        """
        آیا این محتوا منتشر شده و در دسترس است؟

        یک محتوا در صورتی منتشر شده است که:
        1. وضعیت آن "منتشر شده" باشد
        2. تاریخ انتشار آن گذشته باشد یا برابر با زمان فعلی باشد
        3. تاریخ انقضای آن در آینده باشد یا تنظیم نشده باشد
        """
        now = timezone.now()

        if self.status != self.PUBLISHED:
            return False

        if self.publish_date and self.publish_date > now:
            return False

        if self.expiry_date and self.expiry_date <= now:
            return False

        return True

    @property
    def is_draft(self):
        """آیا این محتوا در وضعیت پیش‌نویس است؟"""
        return self.status == self.DRAFT

    @property
    def is_archived(self):
        """آیا این محتوا بایگانی شده است؟"""
        return self.status == self.ARCHIVED

    @property
    def is_scheduled(self):
        """آیا این محتوا برای انتشار در آینده زمان‌بندی شده است؟"""
        now = timezone.now()
        return self.status == self.PUBLISHED and self.publish_date and self.publish_date > now

    @property
    def is_expired(self):
        """آیا تاریخ انقضای این محتوا گذشته است؟"""
        now = timezone.now()
        return self.expiry_date and self.expiry_date <= now

    @property
    def is_visible(self):
        """آیا این محتوا قابل نمایش است؟"""
        return self.is_published