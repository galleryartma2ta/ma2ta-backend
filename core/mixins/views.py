# core/mixins/views.py

import logging
import json
from functools import wraps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

logger = logging.getLogger('view')


class PermissionRequiredMixin:
    """
    میکسین برای بررسی مجوزهای دسترسی کاربران.
    این میکسین روی LoginRequiredMixin ساخته شده است.
    """
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        """بررسی دسترسی کاربر"""
        # اطمینان از اینکه کاربر وارد شده است
        if not self.request.user.is_authenticated:
            return False

        # اگر permission_required تنظیم نشده، دسترسی مجاز است
        if not self.permission_required:
            return True

        # تبدیل به لیست اگر یک رشته یا یک مجوز است
        perms = self.permission_required
        if isinstance(perms, str):
            perms = [perms]

        # بررسی تمام مجوزها
        return self.request.user.has_perms(perms)

    def handle_no_permission(self):
        """پاسخ به عدم دسترسی"""
        # اگر کاربر وارد نشده است، از متد LoginRequiredMixin استفاده می‌کنیم
        if not self.request.user.is_authenticated:
            return LoginRequiredMixin.handle_no_permission(self)

        # برای پاسخ به API، JSON با کد خطای مناسب برمی‌گردانیم
        if 'application/json' in self.request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                'detail': _('شما مجوز دسترسی به این بخش را ندارید.'),
                'code': 'permission_denied'
            }, status=403)

        # برای درخواست‌های معمولی، از متد خطای جنگو استفاده می‌کنیم
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied()


class ArtistRequiredMixin(PermissionRequiredMixin):
    """
    میکسین برای بررسی اینکه کاربر هنرمند باشد.
    این میکسین برای صفحات داشبورد هنرمندان استفاده می‌شود.
    """

    def has_permission(self):
        """بررسی اینکه کاربر هنرمند باشد"""
        if not self.request.user.is_authenticated:
            return False

        # بررسی وجود پروفایل هنرمند
        return hasattr(self.request.user, 'artist_profile') and self.request.user.artist_profile is not None


class OwnershipRequiredMixin:
    """
    میکسین برای بررسی مالکیت یک شیء.
    این میکسین برای صفحاتی استفاده می‌شود که فقط صاحب محتوا باید بتواند آن را ویرایش کند.
    """
    # نام فیلد در شیء که باید با کاربر مطابقت داشته باشد
    owner_field = 'user'

    def dispatch(self, request, *args, **kwargs):
        # بررسی وجود شیء
        if not hasattr(self, 'object'):
            self.object = self.get_object()

        if not self.is_owner():
            return self.handle_not_owner()

        return super().dispatch(request, *args, **kwargs)

    def is_owner(self):
        """بررسی اینکه کاربر مالک شیء است یا خیر"""
        if not self.request.user.is_authenticated:
            return False

        # اگر کاربر مدیر سایت است، همیشه دسترسی دارد
        if self.request.user.is_staff:
            return True

        # بررسی مالکیت
        owner = getattr(self.object, self.owner_field)
        return owner == self.request.user

    def handle_not_owner(self):
        """پاسخ به عدم مالکیت"""
        # برای پاسخ به API، JSON با کد خطای مناسب برمی‌گردانیم
        if 'application/json' in self.request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                'detail': _('شما مالک این محتوا نیستید.'),
                'code': 'not_owner'
            }, status=403)

        # برای درخواست‌های معمولی، از متد خطای جنگو استفاده می‌کنیم
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied()


class AjaxResponseMixin:
    """
    میکسین برای پاسخ‌دهی به درخواست‌های AJAX.
    """

    def form_valid(self, form):
        """پاسخ موفقیت‌آمیز به فرم AJAX"""
        response = super().form_valid(form)

        if self.request.is_ajax():
            data = {
                'status': 'success',
                'redirect': self.get_success_url(),
                'message': _('عملیات با موفقیت انجام شد.')
            }
            return JsonResponse(data)

        return response

    def form_invalid(self, form):
        """پاسخ ناموفق به فرم AJAX"""
        response = super().form_invalid(form)

        if self.request.is_ajax():
            return JsonResponse({
                'status': 'error',
                'errors': form.errors.as_json(),
                'message': _('لطفاً خطاهای فرم را برطرف کنید.')
            }, status=400)

        return response


class LoggingMixin:
    """
    میکسین برای ثبت لاگ عملیات‌های مهم.
    """
    log_actions = False
    log_user = True

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if self.log_actions:
            user_str = "کاربر مهمان"
            if self.log_user and request.user.is_authenticated:
                user_str = f"کاربر {request.user.username} (ID: {request.user.id})"

            logger.info(
                f"{user_str} - {request.method} {request.path} - {response.status_code}"
            )

        return response

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.log_actions:
            action = getattr(self, 'action_name', self.__class__.__name__)

            user_str = "کاربر مهمان"
            if self.log_user and self.request.user.is_authenticated:
                user_str = f"کاربر {self.request.user.username} (ID: {self.request.user.id})"

            logger.info(
                f"{user_str} - {action} - {form.cleaned_data}"
            )

        return response


class CacheMixin:
    """
    میکسین برای کش کردن نتایج ویوها.
    """
    cache_timeout = 60 * 15  # 15 دقیقه پیش‌فرض
    cache_key_prefix = 'view_cache'

    def get_cache_key(self):
        """ساخت کلید کش بر اساس URL و پارامترهای درخواست"""
        url = self.request.path
        query = self.request.META.get('QUERY_STRING', '')
        user_id = self.request.user.id if self.request.user.is_authenticated else 'anonymous'

        key = f"{self.cache_key_prefix}:{url}:{query}:{user_id}"
        return key

    def dispatch(self, request, *args, **kwargs):
        # اگر درخواست GET نیست، کش نکن
        if request.method != 'GET':
            return super().dispatch(request, *args, **kwargs)

        # اگر کاربر مدیر سایت است، کش نکن
        if request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        cache_key = self.get_cache_key()
        cached_response = cache.get(cache_key)

        if cached_response:
            return cached_response

        response = super().dispatch(request, *args, **kwargs)

        # فقط پاسخ‌های موفق را کش کن
        if response.status_code == 200:
            cache.set(cache_key, response, self.cache_timeout)

        return response