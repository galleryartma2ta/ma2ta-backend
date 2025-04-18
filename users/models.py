# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """مدیریت‌کننده سفارشی برای مدل کاربر"""

    def create_user(self, email, password=None, **extra_fields):
        """ایجاد و ذخیره یک کاربر جدید با ایمیل و رمز عبور داده شده."""
        if not email:
            raise ValueError(_('کاربر باید یک آدرس ایمیل داشته باشد'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """ایجاد و ذخیره یک کاربر ادمین با ایمیل و رمز عبور داده شده."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('ادمین باید is_staff=True داشته باشد.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('ادمین باید is_superuser=True داشته باشد.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """مدل سفارشی کاربر که از ایمیل به جای نام کاربری استفاده می‌کند"""

    username = None
    email = models.EmailField(_('آدرس ایمیل'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message=_("شماره تلفن باید در قالب 09XXXXXXXXX وارد شود.")
    )
    phone_number = models.CharField(
        _('شماره تلفن'),
        validators=[phone_regex],
        max_length=11,
        blank=True
    )
    is_verified = models.BooleanField(_('تأیید شده'), default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('کاربر')
        verbose_name_plural = _('کاربران')

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """پروفایل کاربر با اطلاعات تکمیلی"""

    GENDER_CHOICES = (
        ('M', _('مرد')),
        ('F', _('زن')),
        ('O', _('سایر')),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('کاربر')
    )
    first_name_fa = models.CharField(_('نام (فارسی)'), max_length=50, blank=True)
    last_name_fa = models.CharField(_('نام خانوادگی (فارسی)'), max_length=50, blank=True)
    bio = models.TextField(_('درباره من'), blank=True)
    birth_date = models.DateField(_('تاریخ تولد'), null=True, blank=True)
    gender = models.CharField(_('جنسیت'), max_length=1, choices=GENDER_CHOICES, blank=True)
    national_id = models.CharField(_('کد ملی'), max_length=10, blank=True)
    address = models.TextField(_('آدرس'), blank=True)
    postal_code = models.CharField(_('کد پستی'), max_length=10, blank=True)
    avatar = models.ImageField(_('تصویر پروفایل'), upload_to='avatars/', null=True, blank=True)
    newsletter = models.BooleanField(_('عضویت در خبرنامه'), default=False)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('پروفایل کاربر')
        verbose_name_plural = _('پروفایل‌های کاربران')

    def __str__(self):
        return f"{self.user.email} - پروفایل"

    @property
    def full_name_fa(self):
        """نام کامل کاربر به فارسی"""
        return f"{self.first_name_fa} {self.last_name_fa}".strip()