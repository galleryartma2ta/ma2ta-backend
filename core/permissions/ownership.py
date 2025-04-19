# core/permissions/ownership.py

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    مجوز دسترسی برای مالک شیء.
    کاربر باید مالک شیء باشد تا به آن دسترسی داشته باشد.
    """
    message = 'شما مالک این محتوا نیستید.'

    # نام فیلد در مدل که باید با کاربر مطابقت داشته باشد
    owner_field = 'user'

    def has_object_permission(self, request, view, obj):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # مدیران سایت همیشه دسترسی دارند
        if request.user.is_staff:
            return True

        # بررسی مالکیت با استفاده از فیلد مشخص شده
        owner = getattr(obj, self.owner_field, None)

        # اگر owner یک User است، آن را با کاربر مقایسه کنید
        if hasattr(owner, 'pk'):
            return owner.pk == request.user.pk

        # در غیر این صورت، مستقیماً مقایسه کنید
        return owner == request.user


class IsArtworkOwner(IsOwner):
    """
    مجوز دسترسی برای مالک اثر هنری.
    کاربر باید هنرمند مالک اثر باشد.
    """
    message = 'شما مالک این اثر هنری نیستید.'
    owner_field = 'artist'

    def has_object_permission(self, request, view, obj):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # مدیران سایت همیشه دسترسی دارند
        if request.user.is_staff:
            return True

        # بررسی مالکیت با استفاده از فیلد artist
        artist = getattr(obj, self.owner_field, None)

        # بررسی اینکه آیا کاربر همان هنرمند است یا خیر
        if hasattr(request.user, 'artist_profile'):
            return artist == request.user.artist_profile

        return False


class IsGalleryOwner(IsOwner):
    """
    مجوز دسترسی برای مالک گالری.
    کاربر باید مالک گالری باشد.
    """
    message = 'شما مالک این گالری نیستید.'
    owner_field = 'owner'


class IsExhibitionOwner(IsOwner):
    """
    مجوز دسترسی برای مالک نمایشگاه.
    کاربر باید مالک نمایشگاه باشد.
    """
    message = 'شما مالک این نمایشگاه نیستید.'
    owner_field = 'curator'

    def has_object_permission(self, request, view, obj):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # مدیران سایت همیشه دسترسی دارند
        if request.user.is_staff:
            return True

        # بررسی مالکیت مستقیم
        curator = getattr(obj, self.owner_field, None)
        if curator == request.user:
            return True

        # بررسی اینکه آیا نمایشگاه متعلق به گالری است که کاربر مالک آن است
        gallery = getattr(obj, 'gallery', None)
        if gallery and gallery.owner == request.user:
            return True

        return False


class ReadOnly(permissions.BasePermission):
    """
    مجوز دسترسی فقط خواندنی.
    فقط اجازه دسترسی به متدهای GET، HEAD و OPTIONS را می‌دهد.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS