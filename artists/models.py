# artists/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings


class Artist(models.Model):
    """مدل هنرمند"""

    ACTIVITY_STATUS_CHOICES = (
        ('active', _('فعال')),
        ('inactive', _('غیرفعال')),
        ('pending', _('در انتظار تأیید')),
        ('rejected', _('رد شده')),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='artist_profile',
        verbose_name=_('کاربر'),
        null=True,
        blank=True
    )

    # اطلاعات اصلی
    first_name = models.CharField(_('نام'), max_length=100)
    last_name = models.CharField(_('نام خانوادگی'), max_length=100)
    artistic_name = models.CharField(_('نام هنری'), max_length=150, blank=True)
    slug = models.SlugField(_('اسلاگ'), max_length=200, unique=True)

    email = models.EmailField(_('ایمیل'), blank=True)
    phone = models.CharField(_('تلفن'), max_length=20, blank=True)

    # اطلاعات هنری
    bio = models.TextField(_('بیوگرافی'))
    short_bio = models.CharField(_('بیوگرافی کوتاه'), max_length=255, blank=True)
    birth_year = models.PositiveIntegerField(_('سال تولد'), null=True, blank=True)
    death_year = models.PositiveIntegerField(_('سال وفات'), null=True, blank=True)
    birth_place = models.CharField(_('محل تولد'), max_length=100, blank=True)
    nationality = models.CharField(_('ملیت'), max_length=100, blank=True)

    # تصاویر
    profile_image = models.ImageField(_('تصویر پروفایل'), upload_to='artists/profile/', blank=True, null=True)
    banner_image = models.ImageField(_('تصویر بنر'), upload_to='artists/banner/', blank=True, null=True)

    # شبکه‌های اجتماعی
    website = models.URLField(_('وب‌سایت'), blank=True)
    instagram = models.CharField(_('اینستاگرام'), max_length=100, blank=True)
    twitter = models.CharField(_('توییتر'), max_length=100, blank=True)
    facebook = models.CharField(_('فیسبوک'), max_length=100, blank=True)
    linkedin = models.CharField(_('لینکدین'), max_length=100, blank=True)

    # آمار و وضعیت
    featured = models.BooleanField(_('هنرمند ویژه'), default=False)
    verified = models.BooleanField(_('تأیید شده'), default=False)
    activity_status = models.CharField(_('وضعیت فعالیت'), max_length=20, choices=ACTIVITY_STATUS_CHOICES,
                                       default='pending')
    commission_rate = models.DecimalField(_('نرخ کمیسیون (درصد)'), max_digits=5, decimal_places=2, default=15.00)

    # تنظیمات SEO
    meta_keywords = models.CharField(_('کلمات کلیدی متا'), max_length=255, blank=True)
    meta_description = models.TextField(_('توضیحات متا'), blank=True)

    # اطلاعات زمانی
    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('هنرمند')
        verbose_name_plural = _('هنرمندان')
        ordering = ['-featured', 'last_name', 'first_name']

    def __str__(self):
        if self.artistic_name:
            return self.artistic_name
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            name_to_slugify = self.artistic_name if self.artistic_name else f"{self.first_name} {self.last_name}"
            self.slug = slugify(name_to_slugify)
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """نام کامل هنرمند"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self):
        """بررسی فعال بودن هنرمند"""
        return self.activity_status == 'active'

    @property
    def is_contemporary(self):
        """بررسی اینکه آیا هنرمند معاصر است"""
        return self.death_year is None


class ArtistEducation(models.Model):
    """تحصیلات هنرمند"""

    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='education',
        verbose_name=_('هنرمند')
    )
    degree = models.CharField(_('مدرک'), max_length=100)
    institution = models.CharField(_('موسسه/دانشگاه'), max_length=200)
    field = models.CharField(_('رشته'), max_length=100)
    start_year = models.PositiveIntegerField(_('سال شروع'), null=True, blank=True)
    end_year = models.PositiveIntegerField(_('سال پایان'), null=True, blank=True)
    description = models.TextField(_('توضیحات'), blank=True)

    class Meta:
        verbose_name = _('تحصیلات هنرمند')
        verbose_name_plural = _('تحصیلات هنرمندان')
        ordering = ['-end_year']

    def __str__(self):
        return f"{self.degree} - {self.institution} ({self.artist})"


class ArtistExhibition(models.Model):
    """نمایشگاه‌های هنرمند"""

    EXHIBITION_TYPE_CHOICES = (
        ('solo', _('انفرادی')),
        ('group', _('گروهی')),
        ('biennale', _('دوسالانه')),
        ('fair', _('آرت فر')),
    )

    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='exhibitions',
        verbose_name=_('هنرمند')
    )
    title = models.CharField(_('عنوان نمایشگاه'), max_length=200)
    gallery = models.CharField(_('گالری'), max_length=200)
    location = models.CharField(_('مکان'), max_length=200)
    year = models.PositiveIntegerField(_('سال'))
    exhibition_type = models.CharField(_('نوع نمایشگاه'), max_length=20, choices=EXHIBITION_TYPE_CHOICES,
                                       default='group')
    description = models.TextField(_('توضیحات'), blank=True)

    class Meta:
        verbose_name = _('نمایشگاه هنرمند')
        verbose_name_plural = _('نمایشگاه‌های هنرمندان')
        ordering = ['-year']

    def __str__(self):
        return f"{self.title} - {self.gallery} ({self.year})"


class ArtistAward(models.Model):
    """جوایز و افتخارات هنرمند"""

    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='awards',
        verbose_name=_('هنرمند')
    )
    title = models.CharField(_('عنوان جایزه'), max_length=200)
    organization = models.CharField(_('سازمان اعطاکننده'), max_length=200)
    year = models.PositiveIntegerField(_('سال'))
    description = models.TextField(_('توضیحات'), blank=True)

    class Meta:
        verbose_name = _('جایزه هنرمند')
        verbose_name_plural = _('جوایز هنرمندان')
        ordering = ['-year']

    def __str__(self):
        return f"{self.title} - {self.year} ({self.artist})"