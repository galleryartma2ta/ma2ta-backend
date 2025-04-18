# recommendations/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from products.models import ArtProduct, ArtCategory, ArtStyle
from artists.models import Artist


class UserInteraction(models.Model):
    """مدل تعاملات کاربر با محصولات"""

    TYPE_CHOICES = (
        ('view', _('بازدید')),
        ('like', _('علاقه‌مندی')),
        ('add_to_cart', _('افزودن به سبد خرید')),
        ('purchase', _('خرید')),
        ('review', _('نظر')),
        ('bid', _('پیشنهاد در حراجی')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interactions',
        verbose_name=_('کاربر')
    )
    product = models.ForeignKey(
        ArtProduct,
        on_delete=models.CASCADE,
        related_name='user_interactions',
        verbose_name=_('محصول')
    )

    type = models.CharField(_('نوع تعامل'), max_length=15, choices=TYPE_CHOICES)
    value = models.FloatField(_('ارزش'), default=1.0)
    timestamp = models.DateTimeField(_('زمان ثبت'), auto_now_add=True)

    # اطلاعات تکمیلی
    session_id = models.CharField(_('شناسه نشست'), max_length=100, blank=True)
    source = models.CharField(_('منبع'), max_length=100, blank=True)
    extra_data = models.JSONField(_('داده‌های اضافی'), default=dict, blank=True)

    class Meta:
        verbose_name = _('تعامل کاربر')
        verbose_name_plural = _('تعاملات کاربر')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['product', 'type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_type_display()} - {self.product.title}"


class UserPreference(models.Model):
    """ترجیحات کاربر"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preference',
        verbose_name=_('کاربر')
    )

    # ترجیحات دسته‌بندی
    preferred_categories = models.ManyToManyField(
        ArtCategory,
        through='CategoryPreference',
        related_name='interested_users',
        verbose_name=_('دسته‌بندی‌های مورد علاقه')
    )

    # ترجیحات سبک
    preferred_styles = models.ManyToManyField(
        ArtStyle,
        through='StylePreference',
        related_name='interested_users',
        verbose_name=_('سبک‌های مورد علاقه')
    )

    # ترجیحات هنرمند
    preferred_artists = models.ManyToManyField(
        Artist,
        through='ArtistPreference',
        related_name='fan_users',
        verbose_name=_('هنرمندان مورد علاقه')
    )

    # محدوده قیمت
    min_price_preference = models.DecimalField(
        _('حداقل قیمت مورد نظر (تومان)'),
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True
    )
    max_price_preference = models.DecimalField(
        _('حداکثر قیمت مورد نظر (تومان)'),
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True
    )

    # ترجیحات متفرقه
    prefers_original = models.BooleanField(_('ترجیح آثار اصل'), null=True, blank=True)
    prefers_signed = models.BooleanField(_('ترجیح آثار امضا شده'), null=True, blank=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('ترجیح کاربر')
        verbose_name_plural = _('ترجیحات کاربر')

    def __str__(self):
        return f"ترجیحات {self.user.email}"


class CategoryPreference(models.Model):
    """ترجیح دسته‌بندی"""

    user_preference = models.ForeignKey(
        UserPreference,
        on_delete=models.CASCADE,
        verbose_name=_('ترجیح کاربر')
    )
    category = models.ForeignKey(
        ArtCategory,
        on_delete=models.CASCADE,
        verbose_name=_('دسته‌بندی')
    )
    weight = models.FloatField(_('وزن'), default=1.0)

    class Meta:
        verbose_name = _('ترجیح دسته‌بندی')
        verbose_name_plural = _('ترجیحات دسته‌بندی')
        unique_together = ('user_preference', 'category')

    def __str__(self):
        return f"{self.user_preference.user.email} - {self.category.name}"


class StylePreference(models.Model):
    """ترجیح سبک هنری"""

    user_preference = models.ForeignKey(
        UserPreference,
        on_delete=models.CASCADE,
        verbose_name=_('ترجیح کاربر')
    )
    style = models.ForeignKey(
        ArtStyle,
        on_delete=models.CASCADE,
        verbose_name=_('سبک هنری')
    )
    weight = models.FloatField(_('وزن'), default=1.0)

    class Meta:
        verbose_name = _('ترجیح سبک هنری')
        verbose_name_plural = _('ترجیحات سبک هنری')
        unique_together = ('user_preference', 'style')

    def __str__(self):
        return f"{self.user_preference.user.email} - {self.style.name}"


class ArtistPreference(models.Model):
    """ترجیح هنرمند"""

    user_preference = models.ForeignKey(
        UserPreference,
        on_delete=models.CASCADE,
        verbose_name=_('ترجیح کاربر')
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        verbose_name=_('هنرمند')
    )
    weight = models.FloatField(_('وزن'), default=1.0)

    class Meta:
        verbose_name = _('ترجیح هنرمند')
        verbose_name_plural = _('ترجیحات هنرمند')
        unique_together = ('user_preference', 'artist')

    def __str__(self):
        return f"{self.user_preference.user.email} - {self.artist.full_name}"


class ProductSimilarity(models.Model):
    """شباهت بین محصولات"""

    product1 = models.ForeignKey(
        ArtProduct,
        on_delete=models.CASCADE,
        related_name='similarities_as_first',
        verbose_name=_('محصول اول')
    )
    product2 = models.ForeignKey(
        ArtProduct,
        on_delete=models.CASCADE,
        related_name='similarities_as_second',
        verbose_name=_('محصول دوم')
    )

    similarity_score = models.FloatField(_('نمره شباهت'))

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('شباهت محصول')
        verbose_name_plural = _('شباهت‌های محصول')
        unique_together = ('product1', 'product2')
        indexes = [
            models.Index(fields=['product1', 'similarity_score']),
            models.Index(fields=['product2', 'similarity_score']),
        ]

    def __str__(self):
        return f"{self.product1.title} - {self.product2.title} ({self.similarity_score})"


class Recommendation(models.Model):
    """توصیه‌های محصول به کاربر"""

    TYPE_CHOICES = (
        ('content_based', _('بر اساس محتوا')),
        ('collaborative', _('مشارکتی')),
        ('hybrid', _('ترکیبی')),
        ('trending', _('پرطرفدار')),
        ('personalized', _('شخصی‌سازی شده')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name=_('کاربر')
    )
    product = models.ForeignKey(
        ArtProduct,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name=_('محصول')
    )

    score = models.FloatField(_('نمره توصیه'))
    type = models.CharField(_('نوع توصیه'), max_length=20, choices=TYPE_CHOICES)

    is_seen = models.BooleanField(_('دیده شده'), default=False)
    is_clicked = models.BooleanField(_('کلیک شده'), default=False)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)

    class Meta:
        verbose_name = _('توصیه')
        verbose_name_plural = _('توصیه‌ها')
        ordering = ['-score']
        indexes = [
            models.Index(fields=['user', 'score']),
            models.Index(fields=['is_seen']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.product.title} ({self.score})"