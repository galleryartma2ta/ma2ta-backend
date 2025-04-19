# core/validators/file_validators.py

import os
import magic
from typing import List, Union, Optional
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.core.files.uploadedfile import UploadedFile


def validate_file_size(file: UploadedFile, max_size: int = 5242880) -> None:
    """
    اعتبارسنجی اندازه فایل.

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 5 مگابایت)

    Raises:
        ValidationError: اگر اندازه فایل بیش از حد مجاز باشد
    """
    if file.size > max_size:
        raise ValidationError(
            _('حجم فایل نباید بیشتر از %(max_size)s باشد. حجم فعلی %(current_size)s است.') % {
                'max_size': filesizeformat(max_size),
                'current_size': filesizeformat(file.size),
            }
        )


def validate_file_extension(file: UploadedFile,
                            allowed_extensions: List[str]) -> None:
    """
    اعتبارسنجی پسوند فایل.

    Args:
        file: فایل آپلود شده
        allowed_extensions: لیست پسوندهای مجاز (مثلا: ['.pdf', '.doc'])

    Raises:
        ValidationError: اگر پسوند فایل مجاز نباشد
    """
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _('پسوند فایل مجاز نیست. پسوندهای مجاز: %(extensions)s') % {
                'extensions': ', '.join(allowed_extensions),
            }
        )


def validate_file_content_type(file: UploadedFile,
                               allowed_content_types: List[str]) -> None:
    """
    اعتبارسنجی نوع محتوای فایل.

    Args:
        file: فایل آپلود شده
        allowed_content_types: لیست انواع محتوای مجاز (مثلا: ['application/pdf'])

    Raises:
        ValidationError: اگر نوع محتوای فایل مجاز نباشد
    """
    # استفاده از python-magic برای تشخیص نوع محتوا
    try:
        content_type = magic.from_buffer(file.read(1024), mime=True)
        # بازگرداندن نشانگر فایل به ابتدا
        file.seek(0)

        if content_type not in allowed_content_types:
            raise ValidationError(
                _('نوع محتوای فایل مجاز نیست. انواع مجاز: %(content_types)s') % {
                    'content_types': ', '.join(allowed_content_types),
                }
            )
    except ImportError:
        # اگر python-magic نصب نباشد، از نوع محتوای اعلام شده توسط مرورگر استفاده می‌کنیم
        content_type = file.content_type
        if content_type not in allowed_content_types:
            raise ValidationError(
                _('نوع محتوای فایل مجاز نیست. انواع مجاز: %(content_types)s') % {
                    'content_types': ', '.join(allowed_content_types),
                }
            )


def validate_document_file(file: UploadedFile, max_size: Optional[int] = None) -> None:
    """
    اعتبارسنجی فایل‌های اسناد (PDF، Word، Excel).

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 10 مگابایت)

    Raises:
        ValidationError: اگر فایل اعتبارسنجی نشود
    """
    if max_size is None:
        max_size = 10 * 1024 * 1024  # 10 مگابایت

    # اعتبارسنجی اندازه
    validate_file_size(file, max_size)

    # پسوندهای مجاز
    allowed_extensions = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.ppt', '.pptx', '.txt', '.rtf'
    ]

    # اعتبارسنجی پسوند
    validate_file_extension(file, allowed_extensions)

    # انواع محتوای مجاز
    allowed_content_types = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'application/rtf'
    ]

    # اعتبارسنجی نوع محتوا
    try:
        validate_file_content_type(file, allowed_content_types)
    except (ImportError, AttributeError):
        # اگر امکان بررسی نوع محتوا نباشد، فقط به بررسی پسوند اکتفا می‌کنیم
        pass


def validate_audio_file(file: UploadedFile, max_size: Optional[int] = None) -> None:
    """
    اعتبارسنجی فایل‌های صوتی.

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 30 مگابایت)

    Raises:
        ValidationError: اگر فایل اعتبارسنجی نشود
    """
    if max_size is None:
        max_size = 30 * 1024 * 1024  # 30 مگابایت

    # اعتبارسنجی اندازه
    validate_file_size(file, max_size)

    # پسوندهای مجاز
    allowed_extensions = [
        '.mp3', '.wav', '.ogg', '.m4a', '.flac'
    ]

    # اعتبارسنجی پسوند
    validate_file_extension(file, allowed_extensions)

    # انواع محتوای مجاز
    allowed_content_types = [
        'audio/mpeg',
        'audio/wav',
        'audio/ogg',
        'audio/mp4',
        'audio/flac'
    ]

    # اعتبارسنجی نوع محتوا
    try:
        validate_file_content_type(file, allowed_content_types)
    except (ImportError, AttributeError):
        # اگر امکان بررسی نوع محتوا نباشد، فقط به بررسی پسوند اکتفا می‌کنیم
        pass


def validate_video_file(file: UploadedFile, max_size: Optional[int] = None) -> None:
    """
    اعتبارسنجی فایل‌های ویدیویی.

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 100 مگابایت)

    Raises:
        ValidationError: اگر فایل اعتبارسنجی نشود
    """
    if max_size is None:
        max_size = 100 * 1024 * 1024  # 100 مگابایت

    # اعتبارسنجی اندازه
    validate_file_size(file, max_size)

    # پسوندهای مجاز
    allowed_extensions = [
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'
    ]

    # اعتبارسنجی پسوند
    validate_file_extension(file, allowed_extensions)

    # انواع محتوای مجاز
    allowed_content_types = [
        'video/mp4',
        'video/x-msvideo',
        'video/quicktime',
        'video/x-ms-wmv',
        'video/x-flv',
        'video/x-matroska',
        'video/webm'
    ]

    # اعتبارسنجی نوع محتوا
    try:
        validate_file_content_type(file, allowed_content_types)
    except (ImportError, AttributeError):
        # اگر امکان بررسی نوع محتوا نباشد، فقط به بررسی پسوند اکتفا می‌کنیم
        pass


def validate_archive_file(file: UploadedFile, max_size: Optional[int] = None) -> None:
    """
    اعتبارسنجی فایل‌های آرشیوی.

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 50 مگابایت)

    Raises:
        ValidationError: اگر فایل اعتبارسنجی نشود
    """
    if max_size is None:
        max_size = 50 * 1024 * 1024  # 50 مگابایت

    # اعتبارسنجی اندازه
    validate_file_size(file, max_size)

    # پسوندهای مجاز
    allowed_extensions = [
        '.zip', '.rar', '.7z', '.tar', '.gz'
    ]

    # اعتبارسنجی پسوند
    validate_file_extension(file, allowed_extensions)

    # انواع محتوای مجاز
    allowed_content_types = [
        'application/zip',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
        'application/x-tar',
        'application/gzip'
    ]

    # اعتبارسنجی نوع محتوا
    try:
        validate_file_content_type(file, allowed_content_types)
    except (ImportError, AttributeError):
        # اگر امکان بررسی نوع محتوا نباشد، فقط به بررسی پسوند اکتفا می‌کنیم
        pass