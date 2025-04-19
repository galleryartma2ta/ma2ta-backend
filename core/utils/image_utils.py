# core/utils/image_utils.py

import os
import io
import uuid
from typing import Tuple, Optional, Union, List
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageEnhance
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile


def resize_image(image: Image.Image, size: Tuple[int, int],
                 keep_ratio: bool = True) -> Image.Image:
    """
    تغییر اندازه تصویر.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        size: اندازه جدید (عرض، ارتفاع)
        keep_ratio: حفظ نسبت ابعاد تصویر

    Returns:
        Image.Image: تصویر تغییر اندازه یافته
    """
    if keep_ratio:
        image = ImageOps.contain(image, size, method=Image.LANCZOS)
    else:
        image = image.resize(size, Image.LANCZOS)

    return image


def create_thumbnail(image: Image.Image, size: Tuple[int, int],
                     crop: bool = False) -> Image.Image:
    """
    ایجاد تصویر بندانگشتی.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        size: اندازه تصویر بندانگشتی (عرض، ارتفاع)
        crop: برش تصویر برای رسیدن به اندازه دقیق

    Returns:
        Image.Image: تصویر بندانگشتی
    """
    if crop:
        # برش و تغییر اندازه برای رسیدن به اندازه دقیق
        image = ImageOps.fit(image, size, method=Image.LANCZOS)
    else:
        # تغییر اندازه با حفظ نسبت ابعاد
        image = ImageOps.contain(image, size, method=Image.LANCZOS)

    return image


def add_watermark(image: Image.Image, text: str,
                  opacity: float = 0.5,
                  position: str = 'center') -> Image.Image:
    """
    افزودن متن واترمارک به تصویر.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        text: متن واترمارک
        opacity: میزان شفافیت واترمارک (0 تا 1)
        position: موقعیت واترمارک (center, topleft, topright, bottomleft, bottomright)

    Returns:
        Image.Image: تصویر با واترمارک
    """
    # ایجاد یک تصویر جدید با کانال آلفا برای واترمارک
    watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)

    # تلاش برای بارگذاری فونت
    font_path = getattr(settings, 'WATERMARK_FONT', None)
    font_size = int(min(image.size) / 20)  # اندازه فونت متناسب با اندازه تصویر

    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # محاسبه ابعاد متن
    text_width, text_height = draw.textsize(text, font=font)

    # تعیین موقعیت واترمارک
    if position == 'center':
        position = ((image.width - text_width) // 2, (image.height - text_height) // 2)
    elif position == 'topleft':
        position = (10, 10)
    elif position == 'topright':
        position = (image.width - text_width - 10, 10)
    elif position == 'bottomleft':
        position = (10, image.height - text_height - 10)
    elif position == 'bottomright':
        position = (image.width - text_width - 10, image.height - text_height - 10)

    # رسم متن روی واترمارک
    draw.text(position, text, font=font, fill=(255, 255, 255, int(255 * opacity)))

    # ادغام تصویر اصلی و واترمارک
    return Image.alpha_composite(image.convert('RGBA'), watermark).convert('RGB')


def add_image_watermark(image: Image.Image, watermark_image: Image.Image,
                        opacity: float = 0.5,
                        position: str = 'center',
                        scale: float = 0.25) -> Image.Image:
    """
    افزودن تصویر واترمارک به تصویر.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        watermark_image: تصویر واترمارک (شیء PIL Image)
        opacity: میزان شفافیت واترمارک (0 تا 1)
        position: موقعیت واترمارک (center, topleft, topright, bottomleft, bottomright)
        scale: مقیاس واترمارک نسبت به تصویر اصلی (0 تا 1)

    Returns:
        Image.Image: تصویر با واترمارک
    """
    # تبدیل تصاویر به RGBA
    image = image.convert('RGBA')
    watermark_image = watermark_image.convert('RGBA')

    # تغییر اندازه واترمارک
    watermark_width = int(image.width * scale)
    watermark_height = int(watermark_image.height * (watermark_width / watermark_image.width))
    watermark_image = watermark_image.resize((watermark_width, watermark_height), Image.LANCZOS)

    # تنظیم شفافیت واترمارک
    watermark_image = ImageEnhance.Brightness(watermark_image).enhance(opacity)

    # تعیین موقعیت واترمارک
    if position == 'center':
        position = ((image.width - watermark_width) // 2, (image.height - watermark_height) // 2)
    elif position == 'topleft':
        position = (10, 10)
    elif position == 'topright':
        position = (image.width - watermark_width - 10, 10)
    elif position == 'bottomleft':
        position = (10, image.height - watermark_height - 10)
    elif position == 'bottomright':
        position = (image.width - watermark_width - 10, image.height - watermark_height - 10)

    # ادغام تصویر اصلی و واترمارک
    transparent = Image.new('RGBA', image.size, (0, 0, 0, 0))
    transparent.paste(watermark_image, position)

    return Image.alpha_composite(image, transparent).convert('RGB')


def optimize_image(image: Image.Image, quality: int = 85,
                   max_size: Optional[Tuple[int, int]] = None,
                   format: str = 'JPEG') -> Image.Image:
    """
    بهینه‌سازی تصویر برای استفاده در وب.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        quality: کیفیت تصویر خروجی (0 تا 100)
        max_size: حداکثر اندازه تصویر (عرض، ارتفاع)
        format: قالب تصویر خروجی (JPEG، PNG، WebP)

    Returns:
        Image.Image: تصویر بهینه‌سازی شده
    """
    # تغییر اندازه تصویر در صورت نیاز
    if max_size and (image.width > max_size[0] or image.height > max_size[1]):
        image = resize_image(image, max_size)

    # حذف اطلاعات exif
    image_without_exif = Image.new(image.mode, image.size)
    image_without_exif.putdata(list(image.getdata()))

    # تبدیل به فرمت خروجی
    if format.upper() == 'JPEG':
        if image.mode != 'RGB':
            image_without_exif = image_without_exif.convert('RGB')
    elif format.upper() == 'PNG':
        # بهینه‌سازی برای PNG
        pass  # اضافه کردن کدهای بهینه‌سازی PNG در صورت نیاز
    elif format.upper() == 'WEBP':
        # بهینه‌سازی برای WebP
        pass  # اضافه کردن کدهای بهینه‌سازی WebP در صورت نیاز

    return image_without_exif


def convert_image_to_webp(image: Image.Image, quality: int = 80) -> Image.Image:
    """
    تبدیل تصویر به فرمت WebP.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        quality: کیفیت تصویر خروجی (0 تا 100)

    Returns:
        Image.Image: تصویر با فرمت WebP
    """
    # تبدیل به RGB اگر لازم باشد
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # بازگرداندن تصویر (تبدیل به WebP هنگام ذخیره انجام می‌شود)
    return image


def convert_image_to_bytes(image: Image.Image, format: str = 'JPEG',
                           quality: int = 85) -> bytes:
    """
    تبدیل تصویر به آرایه بایت.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        format: قالب تصویر خروجی (JPEG، PNG، WebP)
        quality: کیفیت تصویر خروجی (0 تا 100)

    Returns:
        bytes: آرایه بایت تصویر
    """
    output = io.BytesIO()

    # تبدیل به RGB برای JPEG
    if format.upper() == 'JPEG' and image.mode != 'RGB':
        image = image.convert('RGB')

    # ذخیره تصویر در حافظه
    image.save(output, format=format, quality=quality, optimize=True)

    # بازگرداندن آرایه بایت
    output.seek(0)
    return output.getvalue()


def save_image_to_memory(image: Image.Image, filename: str,
                         format: str = 'JPEG', quality: int = 85) -> InMemoryUploadedFile:
    """
    ذخیره تصویر در حافظه به صورت یک فایل آپلودی.

    Args:
        image: تصویر اصلی (شیء PIL Image)
        filename: نام فایل خروجی
        format: قالب تصویر خروجی (JPEG، PNG، WebP)
        quality: کیفیت تصویر خروجی (0 تا 100)

    Returns:
        InMemoryUploadedFile: فایل آپلودی در حافظه
    """
    from io import BytesIO
    from django.core.files.uploadedfile import InMemoryUploadedFile
    import sys

    # تبدیل به RGB برای JPEG
    if format.upper() == 'JPEG' and image.mode != 'RGB':
        image = image.convert('RGB')

    # تعیین نوع محتوا
    content_types = {
        'JPEG': 'image/jpeg',
        'PNG': 'image/png',
        'WEBP': 'image/webp',
        'GIF': 'image/gif'
    }
    content_type = content_types.get(format.upper(), 'image/jpeg')

    # ذخیره تصویر در حافظه
    temp_file = BytesIO()
    image.save(temp_file, format=format, quality=quality, optimize=True)

    # برگرداندن به ابتدای فایل و ایجاد InMemoryUploadedFile
    temp_file.seek(0)
    return InMemoryUploadedFile(
        temp_file,
        None,
        filename,
        content_type,
        sys.getsizeof(temp_file),
        None
    )