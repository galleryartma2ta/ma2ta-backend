# core/exceptions/api.py

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException as DRFAPIException
from rest_framework import status

from core.constants.error_codes import (
    ERROR_GENERAL,
    ERROR_NOT_FOUND,
    ERROR_UNAUTHORIZED,
    ERROR_FORBIDDEN,
    ERROR_VALIDATION
)


class APIException(DRFAPIException):
    """
    پایه برای تمام استثناهای API سفارشی.
    شامل کد خطا، پیام و وضعیت HTTP.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_GENERAL['message']
    default_code = ERROR_GENERAL['code']

    def __init__(self, detail=None, code=None, status_code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        if status_code is not None:
            self.status_code = status_code

        # اطمینان از اینکه detail شامل code باشد
        if isinstance(detail, str):
            detail = {'detail': detail, 'code': code}
        elif isinstance(detail, dict) and 'code' not in detail:
            detail['code'] = code

        super().__init__(detail)


class NotFound(APIException):
    """
    استثنای زمانی که منبع مورد نظر یافت نشود.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = ERROR_NOT_FOUND['message']
    default_code = ERROR_NOT_FOUND['code']


class ValidationError(APIException):
    """
    استثنای خطاهای اعتبارسنجی.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_VALIDATION['message']
    default_code = ERROR_VALIDATION['code']


class PermissionDenied(APIException):
    """
    استثنای عدم دسترسی کافی.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = ERROR_FORBIDDEN['message']
    default_code = ERROR_FORBIDDEN['code']


class AuthenticationFailed(APIException):
    """
    استثنای زمانی که احراز هویت انجام نشود.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = ERROR_UNAUTHORIZED['message']
    default_code = ERROR_UNAUTHORIZED['code']


class Throttled(APIException):
    """
    استثنای محدودیت درخواست‌های API.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _("درخواست‌های بیش از حد ارسال شده است. لطفاً کمی صبر کنید.")
    default_code = "throttled"

    def __init__(self, wait=None, detail=None, code=None):
        if detail is None:
            detail = self.default_detail

        if wait is not None:
            detail = _("درخواست‌های بیش از حد ارسال شده است. لطفاً {wait} ثانیه صبر کنید.").format(wait=int(wait))

        super().__init__(detail, code)


class ServiceUnavailable(APIException):
    """
    استثنای عدم دسترسی به سرویس خارجی.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = _("سرویس در حال حاضر در دسترس نیست. لطفاً بعداً تلاش کنید.")
    default_code = "service_unavailable"


class ResourceAlreadyExists(APIException):
    """
    استثنای زمانی که منبع قبلاً ایجاد شده باشد.
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("این منبع قبلاً وجود دارد.")
    default_code = "resource_already_exists"


class ArtworkException(APIException):
    """
    استثنای پایه برای خطاهای مرتبط با آثار هنری.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("خطای مرتبط با اثر هنری")
    default_code = "artwork_error"


class ArtworkAlreadySold(ArtworkException):
    """
    استثنای زمانی که اثر هنری مورد نظر قبلاً فروخته شده باشد.
    """
    default_detail = _("این اثر هنری قبلاً فروخته شده است.")
    default_code = "artwork_already_sold"


class ArtworkLimitExceeded(ArtworkException):
    """
    استثنای زمانی که هنرمند به حداکثر تعداد مجاز آثار رسیده باشد.
    """
    default_detail = _("شما به حداکثر تعداد مجاز آثار هنری رسیده‌اید.")
    default_code = "artwork_limit_exceeded"


class InvalidFileUpload(APIException):
    """
    استثنای آپلود فایل نامعتبر.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("فایل آپلود شده نامعتبر است.")
    default_code = "invalid_file_upload"


class FileTooLarge(InvalidFileUpload):
    """
    استثنای زمانی که حجم فایل آپلود شده بیش از حد مجاز باشد.
    """
    default_detail = _("حجم فایل بیش از حد مجاز است.")
    default_code = "file_too_large"


class InvalidFileType(InvalidFileUpload):
    """
    استثنای زمانی که نوع فایل آپلود شده مجاز نباشد.
    """
    default_detail = _("نوع فایل مجاز نیست.")
    default_code = "invalid_file_type"