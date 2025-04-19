# core/mixins/models.py

import uuid
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class TimeStampedMixin(models.Model):
    """
    میکسین برای اضافه کردن فیلدهای created_at و updated_at به مدل.
    """
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("تاریخ بروزرسانی"), auto_now=True)

    class Meta:
        abstract = True


class SlugMixin(models.Model):
    """
    میکسین برای اضافه کردن فیلد slug به مدل.
    این میکسین به صورت خودکار از فیلد title یا name، یک slug ایجاد می‌کند.
    """
    slug = models.SlugField(_("اسلاگ"), max_length=255, unique=True, allow_unicode=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            # استفاده از UUID برای اطمینان از یکتا بودن اسلاگ
            random_suffix = uuid.uuid4().hex[:8]
            title_field = getattr(self, 'title', None) or getattr(self, 'name', '')
            self.slug = slugify(f"{title_field}-{random_suffix}", allow_unicode=True)
        super().save(*args, **kwargs)


class PublishableMixin(models.Model):
    """
    میکسین برای مدل‌هایی که می‌توانند منتشر یا پیش‌نویس باشند.
    شامل فیلدهای وضعیت، تاریخ انتشار و تاریخ پایان انتشار است.
    """
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (DRAFT, _('پیش‌نویس')),
        (PUBLISHED, _('منتشر شده')),
        (ARCHIVED, _('بایگانی شده')),
    ]

    status = models.CharField(_("وضعیت"), max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    publish_date = models.DateTimeField(_("تاریخ انتشار"), null=True, blank=True)
    expiry_date = models.DateTimeField(_("تاریخ پایان انتشار"), null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.status == self.PUBLISHED and not self.publish_date:
            self.publish_date = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        """بررسی اینکه آیا مطلب منتشر شده و در بازه زمانی معتبر است یا خیر"""
        now = timezone.now()

        # اگر وضعیت منتشر شده نباشد، منتشر نشده است
        if self.status != self.PUBLISHED:
            return False

        # اگر تاریخ انتشار ندارد، منتشر نشده است
        if not self.publish_date:
            return False

        # اگر تاریخ انتشار در آینده است، هنوز منتشر نشده است
        if self.publish_date > now:
            return False

        # اگر تاریخ پایان دارد و از تاریخ پایان گذشته است، منتشر نشده است
        if self.expiry_date and self.expiry_date < now:
            return False

        # در غیر این صورت منتشر شده است
        return True


class ViewCountMixin(models.Model):
    """
    میکسین برای اضافه کردن فیلد شمارش بازدید و متد افزایش آن.
    """
    view_count = models.PositiveIntegerField(_("تعداد بازدید"), default=0)

    class Meta:
        abstract = True

    def increase_view_count(self, request=None):
        """افزایش شمارش بازدید با قابلیت بررسی IP برای جلوگیری از شمارش تکراری"""
        if request:
            # استفاده از نشست برای جلوگیری از شمارش مجدد در یک نشست
            viewed_items = request.session.get('viewed_items', {})
            item_key = f"{self.__class__.__name__.lower()}_viewed_{self.id}"

            if item_key not in viewed_items:
                self.view_count += 1
                self.save(update_fields=['view_count'])

                # ذخیره در نشست برای 24 ساعت (86400 ثانیه)
                viewed_items[item_key] = True
                request.session['viewed_items'] = viewed_items
                request.session.set_expiry(86400)
        else:
            # اگر request ارسال نشده، فقط افزایش دهید
            self.view_count += 1
            self.save(update_fields=['view_count'])


class SoftDeleteMixin(models.Model):
    """
    میکسین برای حذف نرم داده‌ها.
    به جای حذف کامل رکورد، فقط آن را علامت‌گذاری می‌کند.
    """
    is_deleted = models.BooleanField(_("حذف شده"), default=False)
    deleted_at = models.DateTimeField(_("تاریخ حذف"), null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard_delete=False):
        """
        حذف نرم یا سخت رکورد.
        اگر hard_delete=True باشد، رکورد به طور کامل حذف می‌شود.
        """
        if hard_delete:
            return super().delete(using, keep_parents)

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class OrderableMixin(models.Model):
    """
    میکسین برای اضافه کردن فیلد ترتیب به مدل‌ها.
    """
    order = models.PositiveIntegerField(_("ترتیب"), default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ['order']


class TranslatableMixin(models.Model):
    """
    میکسین برای پشتیبانی از چندزبانه‌سازی مدل‌ها.
    فیلدهای مورد نظر برای ترجمه باید در TRANSLATABLE_FIELDS مشخص شوند.
    """
    # دیکشنری فیلدهای ترجمه شده (به صورت { 'en': { 'title': 'English Title', ... }, ... })
    translations = models.JSONField(_("ترجمه‌ها"), default=dict, blank=True)

    # زبان‌های پشتیبانی شده
    LANGUAGES = settings.LANGUAGES

    # فیلدهایی که باید ترجمه شوند (باید در کلاس فرزند تعریف شود)
    TRANSLATABLE_FIELDS = []

    class Meta:
        abstract = True

    def get_translation(self, field_name, language=None):
        """
        دریافت ترجمه یک فیلد در زبان مشخص.
        اگر ترجمه وجود نداشته باشد، مقدار اصلی فیلد را برمی‌گرداند.
        """
        if language is None:
            language = settings.LANGUAGE_CODE

        if field_name not in self.TRANSLATABLE_FIELDS:
            return getattr(self, field_name)

        translations = self.translations.get(language, {})
        if field_name in translations and translations[field_name]:
            return translations[field_name]

        return getattr(self, field_name)

    def set_translation(self, field_name, value, language=None):
        """
        تنظیم ترجمه یک فیلد در زبان مشخص.
        """
        if language is None:
            language = settings.LANGUAGE_CODE

        if field_name not in self.TRANSLATABLE_FIELDS:
            raise ValueError(f"فیلد {field_name} قابل ترجمه نیست.")

        translations = self.translations.copy()
        lang_dict = translations.get(language, {})
        lang_dict[field_name] = value
        translations[language] = lang_dict

        self.translations = translations