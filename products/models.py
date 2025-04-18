# products/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from artists.models import Artist


class ArtCategory(models.Model):
    """دسته‌بندی آثار هنری"""

    name = models.CharField(_('نام'), max_length=100)
    slug = models.SlugField(_('اسلاگ'), max_length=120, unique=True)
    description = models.TextField(_('توضیحات'), blank=True)
    icon = models.CharField(_('آیکون'), max_length=50, blank=True)
    image = models.ImageField(_('تصویر'), upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        verbose_name=_('دسته‌بندی والد'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    order = models.PositiveIntegerField(_('ترتیب نمایش'), default=0)
    is_active = models.BooleanField(_('فعال'), default=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('دسته‌بندی هنری')
        verbose_name_plural = _('دسته‌بندی‌های هنری')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ArtStyle(models.Model):
    """سبک‌های هنری"""

    name = models.CharField(_('نام'), max_length=100)
    slug = models.SlugField(_('اسلاگ'), max_length=120, unique=True)
    description = models.TextField(_('توضیحات'), blank=True)
    period = models.CharField(_('دوره تاریخی'), max_length=100, blank=True)

    class Meta:
        verbose_name = _('سبک هنری')
        verbose_name_plural = _('سبک‌های هنری')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ArtProduct(models.Model):
    """محصولات هنری"""

    STATUS_CHOICES = (
        ('draft', _('پیش‌نویس')),
        ('published', _('منتشر شده')),
        ('sold', _('فروخته شده')),
        ('hidden', _('مخفی')),
    )

    title = models.CharField(_('عنوان'), max_length=200)
    slug = models.SlugField(_('اسلاگ'), max_length=250, unique=True)
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('هنرمند')
    )
    category = models.ForeignKey(
        ArtCategory,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('دسته‌بندی')
    )
    style = models.ForeignKey(
        ArtStyle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('سبک هنری')
    )
    description = models.TextField(_('توضیحات'))
    technical_details = models.TextField(_('جزئیات فنی'), blank=True)
    history = models.TextField(_('تاریخچه اثر'), blank=True)
    created_year = models.PositiveIntegerField(_('سال خلق اثر'), null=True, blank=True)

    dimensions = models.CharField(_('ابعاد'), max_length=100, blank=True)
    height = models.PositiveIntegerField(_('ارتفاع (سانتی‌متر)'), null=True, blank=True)
    width = models.PositiveIntegerField(_('عرض (سانتی‌متر)'), null=True, blank=True)
    depth = models.PositiveIntegerField(_('عمق (سانتی‌متر)'), null=True, blank=True)
    weight = models.DecimalField(_('وزن (کیلوگرم)'), max_digits=6, decimal_places=2, null=True, blank=True)

    materials = models.CharField(_('مواد و متریال'), max_length=255, blank=True)
    is_original = models.BooleanField(_('اثر اصل'), default=True)
    is_signed = models.BooleanField(_('امضا شده'), default=True)
    is_framed = models.BooleanField(_('قاب شده'), default=False)
    edition_number = models.CharField(_('شماره نسخه'), max_length=50, blank=True)

    price = models.DecimalField(_('قیمت (تومان)'), max_digits=12, decimal_places=0)
    discount_price = models.DecimalField(_('قیمت با تخفیف (تومان)'), max_digits=12, decimal_places=0, null=True,
                                         blank=True)
    inventory = models.PositiveIntegerField(_('موجودی'), default=1)

    has_authenticity_certificate = models.BooleanField(_('دارای گواهی اصالت'), default=True)
    has_insurance = models.BooleanField(_('دارای بیمه'), default=False)
    has_360_view = models.BooleanField(_('دارای نمای ۳۶۰ درجه'), default=False)
    has_ar_view = models.BooleanField(_('دارای واقعیت افزوده'), default=False)

    status = models.CharField(_('وضعیت'), max_length=20, choices=STATUS_CHOICES, default='draft')
    featured = models.BooleanField(_('محصول ویژه'), default=False)
    view_count = models.PositiveIntegerField(_('تعداد بازدید'), default=0)

    meta_keywords = models.CharField(_('کلمات کلیدی متا'), max_length=255, blank=True)
    meta_description = models.TextField(_('توضیحات متا'), blank=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)
    published_at = models.DateTimeField(_('تاریخ انتشار'), null=True, blank=True)

    class Meta:
        verbose_name = _('محصول هنری')
        verbose_name_plural = _('محصولات هنری')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """قیمت فعلی با در نظر گرفتن تخفیف"""
        if self.discount_price:
            return self.discount_price
        return self.price

    @property
    def discount_percentage(self):
        """درصد تخفیف"""
        if self.discount_price and self.price > 0:
            return int(100 - (self.discount_price * 100 / self.price))
        return 0

    @property
    def is_available(self):
        """بررسی موجود بودن محصول"""
        return self.status == 'published' and self.inventory > 0


class ProductImage(models.Model):
    """تصاویر محصولات هنری"""

    product = models.ForeignKey(
        ArtProduct,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('محصول')
    )
    image = models.ImageField(_('تصویر'), upload_to='products/')
    alt_text = models.CharField(_('متن جایگزین'), max_length=255, blank=True)
    is_primary = models.BooleanField(_('تصویر اصلی'), default=False)
    order = models.PositiveIntegerField(_('ترتیب نمایش'), default=0)

    class Meta:
        verbose_name = _('تصویر محصول')
        verbose_name_plural = _('تصاویر محصولات')
        ordering = ['order']

    def __str__(self):
        return f"تصویر {self.order} - {self.product.title}"


class ProductView(models.Model):
    """ثبت بازدیدهای محصول"""

    product = models.ForeignKey(
        ArtProduct,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name=_('محصول')
    )
    user_ip = models.GenericIPAddressField(_('آی‌پی کاربر'))
    user_agent = models.CharField(_('مرورگر کاربر'), max_length=255, blank=True)
    viewed_at = models.DateTimeField(_('تاریخ بازدید'), auto_now_add=True)

    class Meta:
        verbose_name = _('بازدید محصول')
        verbose_name_plural = _('بازدیدهای محصولات')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"بازدید {self.product.title} - {self.viewed_at}"