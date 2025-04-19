# core/permissions/admin.py

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    مجوز دسترسی برای مدیران سایت.
    فقط کاربران با دسترسی is_staff=True می‌توانند دسترسی داشته باشند.
    """
    message = 'فقط مدیران سایت می‌توانند به این بخش دسترسی داشته باشند.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsModeratorUser(permissions.BasePermission):
    """
    مجوز دسترسی برای مدیران محتوا.
    کاربر باید عضو گروه moderators باشد.
    """
    message = 'فقط مدیران محتوا می‌توانند به این بخش دسترسی داشته باشند.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # بررسی عضویت کاربر در گروه moderators
        return (request.user.is_staff or
                request.user.groups.filter(name='moderators').exists())


class IsFinanceUser(permissions.BasePermission):
    """
    مجوز دسترسی برای کارکنان مالی.
    کاربر باید عضو گروه finance باشد.
    """
    message = 'فقط کارکنان مالی می‌توانند به این بخش دسترسی داشته باشند.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # بررسی عضویت کاربر در گروه finance
        return (request.user.is_staff or
                request.user.groups.filter(name='finance').exists())


class ReadOnlyForNonAdmin(permissions.BasePermission):
    """
    مجوز دسترسی فقط خواندنی برای کاربران غیر مدیر.
    مدیران می‌توانند تغییر ایجاد کنند، اما سایر کاربران فقط می‌توانند بخوانند.
    """
    message = 'فقط مدیران سایت می‌توانند تغییرات ایجاد کنند.'

    def has_permission(self, request, view):
        # همه کاربران می‌توانند درخواست‌های GET، HEAD و OPTIONS داشته باشند
        if request.method in permissions.SAFE_METHODS:
            return True

        # فقط مدیران می‌توانند تغییرات ایجاد کنند
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)