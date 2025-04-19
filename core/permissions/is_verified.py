# core/permissions/is_verified.py

from rest_framework import permissions


class IsVerified(permissions.BasePermission):
    """
    مجوز دسترسی برای کاربران تأیید شده.
    کاربر باید تأیید شده باشد (ایمیل یا شماره تلفن).
    """
    message = 'برای دسترسی به این بخش، باید حساب کاربری خود را تأیید کنید.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی تأیید شده بودن ایمیل یا شماره تلفن
        return request.user.is_verified


class HasVerifiedEmail(permissions.BasePermission):
    """
    مجوز دسترسی برای کاربران با ایمیل تأیید شده.
    """
    message = 'برای دسترسی به این بخش، باید ایمیل خود را تأیید کنید.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی تأیید شده بودن ایمیل
        return request.user.email_verified


class HasVerifiedPhone(permissions.BasePermission):
    """
    مجوز دسترسی برای کاربران با شماره تلفن تأیید شده.
    """
    message = 'برای دسترسی به این بخش، باید شماره تلفن خود را تأیید کنید.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی تأیید شده بودن شماره تلفن
        return request.user.phone_verified


class HasCompletedProfile(permissions.BasePermission):
    """
    مجوز دسترسی برای کاربران با پروفایل تکمیل شده.
    """
    message = 'برای دسترسی به این بخش، باید پروفایل خود را تکمیل کنید.'

    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر وارد شده است
        if not request.user.is_authenticated:
            return False

        # بررسی تکمیل شده بودن پروفایل
        return request.user.has_completed_profile()