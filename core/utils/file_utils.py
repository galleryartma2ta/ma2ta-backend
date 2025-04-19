# core/utils/file_utils.py

import os
import uuid
import mimetypes
from typing import Optional, List, Tuple
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile


def get_file_extension(filename: str) -> str:
    """
    دریافت پسوند فایل.

    Args:
        filename: نام فایل

    Returns:
        str: پسوند فایل (با نقطه)
    """
    return os.path.splitext(filename)[1].lower()


def get_file_size_formatted(size_bytes: int) -> str:
    """
    تبدیل حجم فایل از بایت به فرمت خوانا.

    Args:
        size_bytes: حجم فایل به بایت

    Returns:
        str: حجم فرمت شده (مثلا: 2.5 MB)
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"

    # کیلوبایت
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.1f} KB"

    # مگابایت
    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.1f} MB"

    # گیگابایت
    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"


def generate_unique_filename(filename: str, prefix: str = '') -> str:
    """
    تولید نام یکتا برای فایل با استفاده از UUID.

    Args:
        filename: نام فایل اصلی
        prefix: پیشوند نام فایل

    Returns:
        str: نام یکتای فایل
    """
    ext = get_file_extension(filename)
    file_id = uuid.uuid4().hex[:8]

    if prefix:
        return f"{prefix}_{file_id}{ext}"

    filename_without_ext = os.path.splitext(os.path.basename(filename))[0]
    return f"{filename_without_ext}_{file_id}{ext}"


def is_valid_file_type(file: UploadedFile, allowed_types: List[str]) -> bool:
    """
    بررسی اینکه آیا نوع فایل در لیست انواع مجاز است یا خیر.

    Args:
        file: فایل آپلود شده
        allowed_types: لیست پسوندهای مجاز (با نقطه، مثلا: ['.jpg', '.png'])

    Returns:
        bool: True اگر نوع فایل مجاز باشد، در غیر این صورت False
    """
    ext = get_file_extension(file.name)
    return ext.lower() in [t.lower() for t in allowed_types]


def get_available_name(storage, name: str, max_length: Optional[int] = None) -> str:
    """
    پیدا کردن نام در دسترس برای ذخیره فایل، در صورت تکراری بودن نام.

    Args:
        storage: سیستم ذخیره‌سازی (مثلا: default_storage)
        name: نام فایل
        max_length: حداکثر طول نام فایل

    Returns:
        str: نام در دسترس برای فایل
    """
    directory_name, file_name = os.path.split(name)
    file_root, file_ext = os.path.splitext(file_name)

    count = 0
    while storage.exists(name):
        count += 1
        name = os.path.join(directory_name, f"{file_root}_{count}{file_ext}")

    return name


def save_uploaded_file(uploaded_file: UploadedFile,
                       directory: str,
                       generate_unique_name: bool = True) -> str:
    """
    ذخیره فایل آپلود شده در مسیر مشخص.

    Args:
        uploaded_file: فایل آپلود شده
        directory: مسیر ذخیره‌سازی نسبت به MEDIA_ROOT
        generate_unique_name: آیا نام یکتا تولید شود یا خیر

    Returns:
        str: مسیر نسبی فایل ذخیره شده
    """
    if generate_unique_name:
        filename = generate_unique_filename(uploaded_file.name)
    else:
        filename = uploaded_file.name

    # مسیر کامل فایل
    file_path = os.path.join(directory, filename)

    # ذخیره فایل
    path = default_storage.save(file_path, uploaded_file)

    return path


def detect_mime_type(file_content: bytes, filename: Optional[str] = None) -> Tuple[str, str]:
    """
    تشخیص نوع MIME فایل بر اساس محتوای آن.

    Args:
        file_content: محتوای فایل
        filename: نام فایل (اختیاری)

    Returns:
        Tuple[str, str]: نوع MIME و پسوند فایل
    """
    mime_type = None
    extension = None

    # اگر نام فایل ارائه شده، از آن استفاده می‌کنیم
    if filename:
        mime_type, _ = mimetypes.guess_type(filename)
        extension = get_file_extension(filename)

    # اگر نوع MIME از نام فایل تشخیص داده نشد، از محتوای فایل استفاده می‌کنیم
    if not mime_type:
        magic_numbers = {
            b'\xff\xd8\xff': ('image/jpeg', '.jpg'),
            b'\x89PNG\r\n\x1a\n': ('image/png', '.png'),
            b'GIF87a': ('image/gif', '.gif'),
            b'GIF89a': ('image/gif', '.gif'),
            b'%PDF': ('application/pdf', '.pdf'),
            b'PK\x03\x04': ('application/zip', '.zip'),
        }

        for magic, (mime, ext) in magic_numbers.items():
            if file_content.startswith(magic):
                mime_type = mime
                extension = ext
                break

    # اگر نوع MIME تشخیص داده نشد، مقدار پیش‌فرض برمی‌گردانیم
    if not mime_type:
        mime_type = 'application/octet-stream'
        extension = '.bin'

    return mime_type, extension


def get_temp_file_path(prefix: str = '', extension: str = '') -> str:
    """
    ایجاد مسیر موقت برای ذخیره فایل.

    Args:
        prefix: پیشوند نام فایل
        extension: پسوند فایل (با نقطه)

    Returns:
        str: مسیر کامل فایل موقت
    """
    # مسیر پوشه موقت
    temp_dir = getattr(settings, 'TEMP_DIR', os.path.join(settings.MEDIA_ROOT, 'temp'))

    # اطمینان از وجود پوشه موقت
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # ایجاد نام فایل یکتا
    filename = f"{prefix}_{uuid.uuid4().hex}"
    if extension:
        filename = f"{filename}{extension}"

    # مسیر کامل فایل
    return os.path.join(temp_dir, filename)