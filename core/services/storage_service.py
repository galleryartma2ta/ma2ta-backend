# core/services/storage_service.py

import os
import uuid
import logging
import mimetypes
from io import BytesIO
from typing import Dict, List, Optional, Union, BinaryIO
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.base import ContentFile
from PIL import Image
from core.exceptions import InvalidFileUpload, FileTooLarge, InvalidFileType
from core.services.image_service import ImageService

logger = logging.getLogger('storage')


class StorageService:
    """
    سرویس ذخیره‌سازی فایل.
    این کلاس عملیات مربوط به فایل‌ها (آپلود، ذخیره، حذف) را مدیریت می‌کند.
    """

    def __init__(self, storage=None):
        """
        مقداردهی اولیه سرویس ذخیره‌سازی.

        Args:
            storage: ذخیره‌ساز اختیاری. اگر ارائه نشود، از default_storage استفاده می‌شود.
        """
        self.storage = storage or default_storage
        self.image_service = ImageService()

        # پوشه‌های ذخیره‌سازی
        self.artwork_path = 'artworks'
        self.artist_path = 'artists'
        self.user_path = 'users'
        self.gallery_path = 'galleries'
        self.exhibition_path = 'exhibitions'
        self.temp_path = 'temp'

        # پسوندهای مجاز
        self.allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        self.allowed_document_extensions = ['.pdf', '.doc', '.docx', '.txt']
        self.allowed_artwork_extensions = self.allowed_image_extensions + ['.tiff', '.tif', '.psd']

        # محدودیت حجم فایل
        self.max_filesize = {
            'image': 10 * 1024 * 1024,  # 10 مگابایت
            'artwork': 50 * 1024 * 1024,  # 50 مگابایت
            'document': 5 * 1024 * 1024,  # 5 مگابایت
            'avatar': 2 * 1024 * 1024,  # 2 مگابایت
        }

    def save_file(self,
                  file: Union[BinaryIO, ContentFile],
                  path: str,
                  file_type: str = 'image',
                  check_extensions: bool = True,
                  generate_unique_name: bool = True,
                  max_filesize: Optional[int] = None,
                  allowed_extensions: Optional[List[str]] = None) -> str:
        """
        ذخیره فایل در سیستم ذخیره‌سازی.

        Args:
            file: شیء فایل برای ذخیره
            path: مسیر ذخیره‌سازی
            file_type: نوع فایل (image, artwork, document, avatar)
            check_extensions: بررسی پسوند فایل
            generate_unique_name: تولید نام یکتا برای فایل
            max_filesize: حداکثر حجم فایل (اختیاری)
            allowed_extensions: لیست پسوندهای مجاز (اختیاری)

        Returns:
            str: مسیر کامل فایل ذخیره شده
        """
        # بررسی حجم فایل
        if max_filesize is None:
            max_filesize = self.max_filesize.get(file_type, 10 * 1024 * 1024)

        if hasattr(file, 'size') and file.size > max_filesize:
            raise FileTooLarge(f"حجم فایل بیش از حد مجاز است. حداکثر {max_filesize // (1024 * 1024)} مگابایت")

        # بررسی پسوند فایل
        if check_extensions:
            # تعیین پسوندهای مجاز
            if allowed_extensions is None:
                if file_type == 'image':
                    allowed_extensions = self.allowed_image_extensions
                elif file_type == 'artwork':
                    allowed_extensions = self.allowed_artwork_extensions
                elif file_type == 'document':
                    allowed_extensions = self.allowed_document_extensions
                elif file_type == 'avatar':
                    allowed_extensions = self.allowed_image_extensions

            # دریافت پسوند فایل
            original_filename = getattr(file, 'name', 'unknown.jpg')
            file_ext = os.path.splitext(original_filename)[1].lower()

            if file_ext not in allowed_extensions:
                raise InvalidFileType(f"پسوند فایل مجاز نیست. پسوندهای مجاز: {', '.join(allowed_extensions)}")

        # ساخت نام یکتا
        if generate_unique_name:
            # دریافت نام و پسوند فایل
            if hasattr(file, 'name'):
                original_filename = file.name
                file_name, file_ext = os.path.splitext(original_filename)
            else:
                # تشخیص نوع فایل برای ContentFile
                file_ext = self._guess_extension(file) or '.jpg'
                file_name = str(uuid.uuid4())

            # ساخت نام یکتا
            unique_filename = f"{file_name}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = os.path.join(path, unique_filename)
        else:
            # استفاده از نام اصلی فایل
            file_path = os.path.join(path, getattr(file, 'name', str(uuid.uuid4())))

        try:
            # ذخیره فایل در سیستم ذخیره‌سازی
            saved_path = self.storage.save(file_path, file)
            logger.info(f"فایل با موفقیت در مسیر {saved_path} ذخیره شد")
            return saved_path
        except Exception as e:
            logger.error(f"خطا در ذخیره فایل: {str(e)}")
            raise

    def delete_file(self, file_path: str) -> bool:
        """
        حذف فایل از سیستم ذخیره‌سازی.

        Args:
            file_path: مسیر فایل برای حذف

        Returns:
            bool: نتیجه حذف فایل (موفق یا ناموفق)
        """
        if not file_path:
            return False

        try:
            if self.storage.exists(file_path):
                self.storage.delete(file_path)
                logger.info(f"فایل با موفقیت از مسیر {file_path} حذف شد")
                return True
            else:
                logger.warning(f"فایل {file_path} برای حذف یافت نشد")
                return False
        except Exception as e:
            logger.error(f"خطا در حذف فایل {file_path}: {str(e)}")
            return False

    def save_artwork_image(self, image_file: Union[BinaryIO, ContentFile], artist_id: int) -> str:
        """
        ذخیره تصویر اثر هنری.

        Args:
            image_file: فایل تصویر اثر هنری
            artist_id: شناسه هنرمند

        Returns:
            str: مسیر کامل تصویر ذخیره شده
        """
        path = os.path.join(self.artwork_path, str(artist_id))
        return self.save_file(
            file=image_file,
            path=path,
            file_type='artwork',
            check_extensions=True,
            generate_unique_name=True
        )

    def save_artist_avatar(self, image_file: Union[BinaryIO, ContentFile], artist_id: int) -> str:
        """
        ذخیره تصویر پروفایل هنرمند.

        Args:
            image_file: فایل تصویر پروفایل
            artist_id: شناسه هنرمند

        Returns:
            str: مسیر کامل تصویر ذخیره شده
        """
        # بهینه‌سازی تصویر پروفایل
        optimized_image = self.image_service.optimize_avatar(image_file)

        path = os.path.join(self.artist_path, str(artist_id))
        return self.save_file(
            file=optimized_image,
            path=path,
            file_type='avatar',
            check_extensions=True,
            generate_unique_name=True
        )

    def save_user_avatar(self, image_file: Union[BinaryIO, ContentFile], user_id: int) -> str:
        """
        ذخیره تصویر پروفایل کاربر.

        Args:
            image_file: فایل تصویر پروفایل
            user_id: شناسه کاربر

        Returns:
            str: مسیر کامل تصویر ذخیره شده
        """
        # بهینه‌سازی تصویر پروفایل
        optimized_image = self.image_service.optimize_avatar(image_file)

        path = os.path.join(self.user_path, str(user_id))
        return self.save_file(
            file=optimized_image,
            path=path,
            file_type='avatar',
            check_extensions=True,
            generate_unique_name=True
        )

    def save_gallery_image(self, image_file: Union[BinaryIO, ContentFile], gallery_id: int) -> str:
        """
        ذخیره تصویر گالری.

        Args:
            image_file: فایل تصویر گالری
            gallery_id: شناسه گالری

        Returns:
            str: مسیر کامل تصویر ذخیره شده
        """
        path = os.path.join(self.gallery_path, str(gallery_id))
        return self.save_file(
            file=image_file,
            path=path,
            file_type='image',
            check_extensions=True,
            generate_unique_name=True
        )

    def save_exhibition_image(self, image_file: Union[BinaryIO, ContentFile], exhibition_id: int) -> str:
        """
        ذخیره تصویر نمایشگاه.

        Args:
            image_file: فایل تصویر نمایشگاه
            exhibition_id: شناسه نمایشگاه

        Returns:
            str: مسیر کامل تصویر ذخیره شده
        """
        path = os.path.join(self.exhibition_path, str(exhibition_id))
        return self.save_file(
            file=image_file,
            path=path,
            file_type='image',
            check_extensions=True,
            generate_unique_name=True
        )

    def save_temp_file(self, file: Union[BinaryIO, ContentFile], prefix: str = '') -> str:
        """
        ذخیره فایل موقت.

        Args:
            file: فایل برای ذخیره موقت
            prefix: پیشوند نام فایل

        Returns:
            str: مسیر کامل فایل ذخیره شده
        """
        path = os.path.join(self.temp_path, prefix)
        return self.save_file(
            file=file,
            path=path,
            check_extensions=False,
            generate_unique_name=True
        )

    def _guess_extension(self, file: Union[BinaryIO, ContentFile]) -> Optional[str]:
        """
        حدس پسوند فایل بر اساس محتوای آن.

        Args:
            file: فایل برای حدس پسوند

        Returns:
            Optional[str]: پسوند حدس زده شده یا None
        """
        # اگر فایل یک ContentFile است
        if isinstance(file, ContentFile):
            # خواندن چند بایت اول فایل
            content = file.read(1024)
            file.seek(0)  # بازگشت به ابتدای فایل

            # حدس نوع فایل بر اساس محتوا
            mime_type = mimetypes.guess_type('', strict=False)[0]

            if mime_type:
                return mimetypes.guess_extension(mime_type)

            # احتمالاً یک تصویر JPEG است
            if content.startswith(b'\xff\xd8'):
                return '.jpg'
            # احتمالاً یک تصویر PNG است
            elif content.startswith(b'\x89PNG'):
                return '.png'
            # احتمالاً یک تصویر GIF است
            elif content.startswith(b'GIF'):
                return '.gif'
            # احتمالاً یک فایل PDF است
            elif content.startswith(b'%PDF'):
                return '.pdf'

        return None