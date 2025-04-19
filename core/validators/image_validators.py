# core/validators/image_validators.py

import os
from typing import List, Tuple, Optional, Union
from PIL import Image
from io import BytesIO
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.core.files.uploadedfile import UploadedFile


def validate_image_extension(file: UploadedFile,
                             allowed_extensions: Optional[List[str]] = None) -> None:
    """
    اعتبارسنجی پسوند فایل تصویری.

    Args:
        file: فایل آپلود شده
        allowed_extensions: لیست پسوندهای مجاز (پیش‌فرض: ['.jpg', '.jpeg', '.png', '.gif', '.webp'])

    Raises:
        ValidationError: اگر پسوند فایل مجاز نباشد
    """
    if allowed_extensions is None:
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _('پسوند فایل تصویری مجاز نیست. پسوندهای مجاز: %(extensions)s') % {
                'extensions': ', '.join(allowed_extensions),
            }
        )


def validate_image_size(file: UploadedFile, max_size: int = 5242880) -> None:
    """
    اعتبارسنجی اندازه فایل تصویری.

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 5 مگابایت)

    Raises:
        ValidationError: اگر اندازه فایل بیش از حد مجاز باشد
    """
    if file.size > max_size:
        raise ValidationError(
            _('حجم تصویر نباید بیشتر از %(max_size)s باشد. حجم فعلی %(current_size)s است.') % {
                'max_size': filesizeformat(max_size),
                'current_size': filesizeformat(file.size),
            }
        )


def validate_image_dimensions(file: UploadedFile,
                              min_width: Optional[int] = None,
                              min_height: Optional[int] = None,
                              max_width: Optional[int] = None,
                              max_height: Optional[int] = None) -> None:
    """
    اعتبارسنجی ابعاد تصویر.

    Args:
        file: فایل آپلود شده
        min_width: حداقل عرض مجاز (پیکسل)
        min_height: حداقل ارتفاع مجاز (پیکسل)
        max_width: حداکثر عرض مجاز (پیکسل)
        max_height: حداکثر ارتفاع مجاز (پیکسل)

    Raises:
        ValidationError: اگر ابعاد تصویر خارج از محدوده مجاز باشد
    """
    try:
        img = Image.open(file)
        width, height = img.size

        # بازگرداندن نشانگر فایل به ابتدا
        file.seek(0)

        if min_width is not None and width < min_width:
            raise ValidationError(
                _('عرض تصویر نباید کمتر از %(min_width)d پیکسل باشد.') % {
                    'min_width': min_width,
                }
            )

        if min_height is not None and height < min_height:
            raise ValidationError(
                _('ارتفاع تصویر نباید کمتر از %(min_height)d پیکسل باشد.') % {
                    'min_height': min_height,
                }
            )

        if max_width is not None and width > max_width:
            raise ValidationError(
                _('عرض تصویر نباید بیشتر از %(max_width)d پیکسل باشد.') % {
                    'max_width': max_width,
                }
            )

        if max_height is not None and height > max_height:
            raise ValidationError(
                _('ارتفاع تصویر نباید بیشتر از %(max_height)d پیکسل باشد.') % {
                    'max_height': max_height,
                }
            )

    except Exception as e:
        raise ValidationError(_('خطا در پردازش تصویر: %(error)s') % {'error': str(e)})


def validate_image_aspect_ratio(file: UploadedFile,
                                min_ratio: Optional[float] = None,
                                max_ratio: Optional[float] = None,
                                exact_ratio: Optional[float] = None,
                                tolerance: float = 0.01) -> None:
    """
    اعتبارسنجی نسبت ابعاد تصویر (عرض به ارتفاع).

    Args:
        file: فایل آپلود شده
        min_ratio: حداقل نسبت مجاز
        max_ratio: حداکثر نسبت مجاز
        exact_ratio: نسبت دقیق مورد نظر
        tolerance: حداکثر اختلاف مجاز برای نسبت دقیق

    Raises:
        ValidationError: اگر نسبت ابعاد تصویر خارج از محدوده مجاز باشد
    """
    try:
        img = Image.open(file)
        width, height = img.size

        # بازگرداندن نشانگر فایل به ابتدا
        file.seek(0)

        # محاسبه نسبت ابعاد (عرض به ارتفاع)
        ratio = width / height

        if exact_ratio is not None:
            if abs(ratio - exact_ratio) > tolerance:
                raise ValidationError(
                    _('نسبت ابعاد تصویر باید %(exact_ratio).2f باشد (با تلرانس %(tolerance).2f). نسبت فعلی: %(ratio).2f') % {
                        'exact_ratio': exact_ratio,
                        'tolerance': tolerance,
                        'ratio': ratio,
                    }
                )
        else:
            if min_ratio is not None and ratio < min_ratio:
                raise ValidationError(
                    _('نسبت ابعاد تصویر (عرض به ارتفاع) نباید کمتر از %(min_ratio).2f باشد. نسبت فعلی: %(ratio).2f') % {
                        'min_ratio': min_ratio,
                        'ratio': ratio,
                    }
                )

            if max_ratio is not None and ratio > max_ratio:
                raise ValidationError(
                    _('نسبت ابعاد تصویر (عرض به ارتفاع) نباید بیشتر از %(max_ratio).2f باشد. نسبت فعلی: %(ratio).2f') % {
                        'max_ratio': max_ratio,
                        'ratio': ratio,
                    }
                )

    except Exception as e:
        raise ValidationError(_('خطا در پردازش تصویر: %(error)s') % {'error': str(e)})


def validate_image_square(file: UploadedFile, tolerance: float = 0.01) -> None:
    """
    اعتبارسنجی مربعی بودن تصویر.

    Args:
        file: فایل آپلود شده
        tolerance: حداکثر اختلاف مجاز

    Raises:
        ValidationError: اگر تصویر مربعی نباشد
    """
    validate_image_aspect_ratio(file, exact_ratio=1.0, tolerance=tolerance)


def validate_image_content(file: UploadedFile) -> None:
    """
    اعتبارسنجی محتوای فایل تصویری (بررسی اینکه آیا فایل واقعاً یک تصویر است).

    Args:
        file: فایل آپلود شده

    Raises:
        ValidationError: اگر فایل یک تصویر معتبر نباشد
    """
    try:
        # سعی در بازکردن فایل به عنوان تصویر
        img = Image.open(file)
        img.verify()  # بررسی اینکه آیا فایل تصویر معتبر است

        # بازگرداندن نشانگر فایل به ابتدا
        file.seek(0)

    except Exception:
        raise ValidationError(_('فایل آپلود شده یک تصویر معتبر نیست.'))


def validate_profile_image(file: UploadedFile, max_size: Optional[int] = None) -> None:
    """
    اعتبارسنجی تصویر پروفایل.

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 2 مگابایت)

    Raises:
        ValidationError: اگر تصویر پروفایل معتبر نباشد
    """
    if max_size is None:
        max_size = 2 * 1024 * 1024  # 2 مگابایت

    # بررسی اندازه فایل
    validate_image_size(file, max_size)

    # بررسی پسوند فایل
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    validate_image_extension(file, allowed_extensions)

    # بررسی ابعاد تصویر
    validate_image_dimensions(file, min_width=200, min_height=200, max_width=5000, max_height=5000)

    # بررسی محتوای تصویر
    validate_image_content(file)


def validate_artwork_image(file: UploadedFile, max_size: Optional[int] = None) -> None:
    """
    اعتبارسنجی تصویر اثر هنری.

    Args:
        file: فایل آپلود شده
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 10 مگابایت)

    Raises:
        ValidationError: اگر تصویر اثر هنری معتبر نباشد
    """
    if max_size is None:
        max_size = 10 * 1024 * 1024  # 10 مگابایت

    # بررسی اندازه فایل
    validate_image_size(file, max_size)

    # بررسی پسوند فایل
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.tiff', '.tif']
    validate_image_extension(file, allowed_extensions)

    # بررسی ابعاد تصویر
    validate_image_dimensions(file, min_width=800, min_height=600, max_width=10000, max_height=10000)

    # بررسی محتوای تصویر
    validate_image_content(file)


def validate_banner_image(file: UploadedFile,
                          required_dimensions: Optional[Tuple[int, int]] = None,
                          max_size: Optional[int] = None) -> None:
    """
    اعتبارسنجی تصویر بنر.

    Args:
        file: فایل آپلود شده
        required_dimensions: ابعاد مورد نیاز (عرض، ارتفاع) (پیش‌فرض: None)
        max_size: حداکثر اندازه مجاز (پیش‌فرض: 5 مگابایت)

    Raises:
        ValidationError: اگر تصویر بنر معتبر نباشد
    """
    if max_size is None:
        max_size = 5 * 1024 * 1024  # 5 مگابایت

    # بررسی اندازه فایل
    validate_image_size(file, max_size)

    # بررسی پسوند فایل
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    validate_image_extension(file, allowed_extensions)

    if required_dimensions:
        # بررسی ابعاد دقیق
        try:
            img = Image.open(file)
            width, height = img.size

            # بازگرداندن نشانگر فایل به ابتدا
            file.seek(0)

            required_width, required_height = required_dimensions

            if width != required_width or height != required_height:
                raise ValidationError(
                    _('ابعاد تصویر بنر باید دقیقاً %(width)d×%(height)d پیکسل باشد. ابعاد فعلی: %(current_width)d×%(current_height)d') % {
                        'width': required_width,
                        'height': required_height,
                        'current_width': width,
                        'current_height': height,
                    }
                )

        except Exception as e:
            raise ValidationError(_('خطا در پردازش تصویر: %(error)s') % {'error': str(e)})
    else:
        # بررسی محدوده ابعاد
        validate_image_dimensions(file, min_width=800, min_height=200, max_width=5000, max_height=3000)

    # بررسی محتوای تصویر
    validate_image_content(file)