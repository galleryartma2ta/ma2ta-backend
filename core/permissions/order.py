# core/permissions/order.py

from rest_framework import permissions


class IsOrderOwner(permissions.BasePermission):
    """
    مجوز دسترسی برای مالک سفارش.
    کاربر باید مالک سفارش باشد تا به آن دسترسی داشته باشد.
    """
    message = 'شما مالک این سفارش نیستید.'

    def has_object_permission(self, request, view, obj):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # مدیران سایت همیشه دسترسی دارند
        if request.user.is_staff:
            return True

        # بررسی مالکیت سفارش
        return obj.user == request.user


class IsArtistWithOrderedArtwork(permissions.BasePermission):
    """
    مجوز دسترسی برای هنرمندی که آثارش در سفارش وجود دارد.
    هنرمند فقط به سفارش‌هایی دسترسی دارد که شامل آثار او باشند.
    """
    message = 'این سفارش شامل آثار شما نیست.'

    def has_object_permission(self, request, view, obj):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # مدیران سایت همیشه دسترسی دارند
        if request.user.is_staff:
            return True

        # بررسی اینکه کاربر هنرمند است
        if not hasattr(request.user, 'artist_profile') or request.user.artist_profile is None:
            return False

        # بررسی اینکه آیا آثار هنرمند در سفارش وجود دارد
        artist_id = request.user.artist_profile.id

        # بررسی آیتم‌های سفارش
        for item in obj.items.all():
            if item.artwork.artist_id == artist_id:
                return True

        return False


class CanRateOrder(permissions.BasePermission):
    """
    مجوز دسترسی برای امتیازدهی به سفارش.
    کاربر باید مالک سفارش باشد و سفارش باید تحویل داده شده باشد.
    """
    message = 'شما اجازه امتیازدهی به این سفارش را ندارید.'

    def has_object_permission(self, request, view, obj):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # مدیران سایت همیشه دسترسی دارند
        if request.user.is_staff:
            return True

        # بررسی مالکیت سفارش
        if obj.user != request.user:
            return False

        # بررسی وضعیت سفارش (باید تحویل داده شده باشد)
        return obj.status == 'delivered'