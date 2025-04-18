# blog/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from artists.models import Artist


class BlogCategory(models.Model):
    """دسته‌بندی مطالب بلاگ"""

    name = models.CharField(_('نام'), max_length=100)
    slug = models.SlugField(_('اسلاگ'), max_length=120, unique=True)
    description = models.TextField(_('توضیحات'), blank=True)
    icon = models.CharField(_('آیکون'), max_length=50, blank=True)
    image = models.ImageField(_('تصویر'), upload_to='blog/categories/', blank=True, null=True)
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
        verbose_name = _('دسته‌بندی بلاگ')
        verbose_name_plural = _('دسته‌بندی‌های بلاگ')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogTag(models.Model):
    """برچسب‌های بلاگ"""

    name = models.CharField(_('نام'), max_length=50)
    slug = models.SlugField(_('اسلاگ'), max_length=60, unique=True)

    class Meta:
        verbose_name = _('برچسب بلاگ')
        verbose_name_plural = _('برچسب‌های بلاگ')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    """پست‌های بلاگ"""

    STATUS_CHOICES = (
        ('draft', _('پیش‌نویس')),
        ('published', _('منتشر شده')),
        ('featured', _('ویژه')),
        ('archived', _('بایگانی شده')),
    )

    title = models.CharField(_('عنوان'), max_length=200)
    slug = models.SlugField(_('اسلاگ'), max_length=250, unique=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts',
        verbose_name=_('نویسنده')
    )

    categories = models.ManyToManyField(
        BlogCategory,
        related_name='posts',
        verbose_name=_('دسته‌بندی‌ها')
    )

    tags = models.ManyToManyField(
        BlogTag,
        related_name='posts',
        verbose_name=_('برچسب‌ها'),
        blank=True
    )

    content = models.TextField(_('محتوا'))
    excerpt = models.TextField(_('خلاصه'), blank=True)

    featured_image = models.ImageField(_('تصویر شاخص'), upload_to='blog/featured/')

    related_artists = models.ManyToManyField(
        Artist,
        related_name='blog_posts',
        verbose_name=_('هنرمندان مرتبط'),
        blank=True
    )

    status = models.CharField(_('وضعیت'), max_length=10, choices=STATUS_CHOICES, default='draft')
    is_comments_enabled = models.BooleanField(_('نظرات فعال'), default=True)

    meta_keywords = models.CharField(_('کلمات کلیدی متا'), max_length=255, blank=True)
    meta_description = models.TextField(_('توضیحات متا'), blank=True)

    view_count = models.PositiveIntegerField(_('تعداد بازدید'), default=0)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)
    published_at = models.DateTimeField(_('تاریخ انتشار'), null=True, blank=True)

    class Meta:
        verbose_name = _('پست بلاگ')
        verbose_name_plural = _('پست‌های بلاگ')
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt and self.content:
            # ایجاد خلاصه اتوماتیک از 150 کاراکتر اول محتوا
            self.excerpt = self.content[:150] + '...' if len(self.content) > 150 else self.content
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        """بررسی منتشر شدن پست"""
        return self.status in ['published', 'featured']

    @property
    def reading_time(self):
        """محاسبه زمان تقریبی مطالعه بر اساس تعداد کلمات"""
        word_count = len(self.content.split())
        minutes = word_count // 200  # فرض متوسط سرعت خواندن 200 کلمه در دقیقه
        return max(1, minutes)  # حداقل 1 دقیقه


class BlogComment(models.Model):
    """نظرات پست‌های بلاگ"""

    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('پست')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_comments',
        verbose_name=_('کاربر'),
        null=True,
        blank=True
    )

    name = models.CharField(_('نام'), max_length=100)
    email = models.EmailField(_('ایمیل'))
    content = models.TextField(_('محتوا'))

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_('نظر والد'),
        null=True,
        blank=True
    )

    is_approved = models.BooleanField(_('تایید شده'), default=False)
    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)

    class Meta:
        verbose_name = _('نظر بلاگ')
        verbose_name_plural = _('نظرات بلاگ')
        ordering = ['-created_at']

    def __str__(self):
        return f"نظر {self.name} بر روی {self.post.title}"

    @property
    def is_reply(self):
        """بررسی اینکه آیا نظر پاسخ به یک نظر دیگر است"""
        return self.parent is not None