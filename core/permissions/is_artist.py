# core/permissions/is_artist.py

from rest_framework import permissions


class IsArtist(permissions.BasePermission):
    """
    مجوز دسترسی برای هنرمندان.
    کاربر باید هنرمند باشد تا دسترسی داشته باشد.
    """
    message = 'فقط هنرمندان می‌توانند به این بخش دسترسی داشته باشند.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی وجود پروفایل هنرمند
        return hasattr(request.user, 'artist_profile') and request.user.artist_profile is not None


class IsApprovedArtist(permissions.BasePermission):
    """
    مجوز دسترسی برای هنرمندان تأیید شده.
    کاربر باید هنرمند باشد و وضعیت پروفایلش تأیید شده باشد.
    """
    message = 'فقط هنرمندان تأیید شده می‌توانند به این بخش دسترسی داشته باشند.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی وجود پروفایل هنرمند
        if not hasattr(request.user, 'artist_profile') or request.user.artist_profile is None:
            return False

        # بررسی تأیید شده بودن هنرمند
        return request.user.artist_profile.is_approved


class IsVerifiedArtist(permissions.BasePermission):
    """
    مجوز دسترسی برای هنرمندان تأیید هویت شده.
    کاربر باید هنرمند باشد و تأیید هویت شده باشد.
    """
    message = 'فقط هنرمندان تأیید هویت شده می‌توانند به این بخش دسترسی داشته باشند.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی وجود پروفایل هنرمند
        if not hasattr(request.user, 'artist_profile') or request.user.artist_profile is None:
            return False

        # بررسی تأیید هویت شده بودن هنرمند
        return request.user.artist_profile.is_verified


class HasArtistSubscription(permissions.BasePermission):
    """
    مجوز دسترسی برای هنرمندان دارای اشتراک.
    کاربر باید هنرمند باشد و اشتراک فعال داشته باشد.
    """
    message = 'برای دسترسی به این بخش، نیاز به اشتراک هنرمند دارید.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی وجود پروفایل هنرمند
        if not hasattr(request.user, 'artist_profile') or request.user.artist_profile is None:
            return False

        # بررسی اشتراک فعال
        return request.user.artist_profile.has_active_subscription()