# core/storage/custom_storage.py

import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class OverwriteStorage(FileSystemStorage):
    """
    سیستم ذخیره‌سازی فایل با قابلیت بازنویسی فایل‌های قبلی.
    هنگام آپلود فایل با نام تکراری، فایل قبلی حذف می‌شود.
    """

    def get_available_name(self, name, max_length=None):
        """
        بررسی وجود فایل و حذف آن در صورت وجود.
        """
        if self.exists(name):
            self.delete(name)
        return name


class PrivateMediaStorage(FileSystemStorage):
    """
    سیستم ذخیره‌سازی برای فایل‌های خصوصی (با دسترسی محدود).
    """

    def __init__(self, *args, **kwargs):
        location = getattr(settings, 'PRIVATE_MEDIA_ROOT', os.path.join(settings.MEDIA_ROOT, 'private'))
        super().__init__(location=location, *args, **kwargs)


class PublicMediaStorage(FileSystemStorage):
    """
    سیستم ذخیره‌سازی برای فایل‌های عمومی (با دسترسی عمومی).
    """

    def __init__(self, *args, **kwargs):
        location = getattr(settings, 'PUBLIC_MEDIA_ROOT', settings.MEDIA_ROOT)
        base_url = getattr(settings, 'PUBLIC_MEDIA_URL', settings.MEDIA_URL)
        super().__init__(location=location, base_url=base_url, *args, **kwargs)


class ArtworkStorage(FileSystemStorage):
    """
    سیستم ذخیره‌سازی برای آثار هنری.
    می‌تواند برای ذخیره تصاویر آثار هنری و فایل‌های مرتبط با آن استفاده شود.
    """

    def __init__(self, *args, **kwargs):
        location = os.path.join(settings.MEDIA_ROOT, 'artworks')
        base_url = f"{settings.MEDIA_URL}artworks/"
        super().__init__(location=location, base_url=base_url, *args, **kwargs)


class ProfileImageStorage(FileSystemStorage):
    """
    سیستم ذخیره‌سازی برای تصاویر پروفایل کاربران و هنرمندان.
    """

    def __init__(self, *args, **kwargs):
        location = os.path.join(settings.MEDIA_ROOT, 'profiles')
        base_url = f"{settings.MEDIA_URL}profiles/"
        super().__init__(location=location, base_url=base_url, *args, **kwargs)


# سیستم ذخیره‌سازی در Amazon S3 (در صورت نیاز)
if getattr(settings, 'USE_S3_STORAGE', False):
    class S3PublicMediaStorage(S3Boto3Storage):
        """
        ذخیره‌سازی مدیا عمومی در Amazon S3.
        """
        location = 'media/public'
        file_overwrite = False
        default_acl = 'public-read'


    class S3PrivateMediaStorage(S3Boto3Storage):
        """
        ذخیره‌سازی مدیا خصوصی در Amazon S3.
        """
        location = 'media/private'
        file_overwrite = False
        default_acl = 'private'
        custom_domain = False