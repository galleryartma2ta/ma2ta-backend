# core/cache/decorators.py

import hashlib
import json
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from django.conf import settings
from django.core.cache import cache
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('cache')


def get_cache_key_prefix() -> str:
    """
    دریافت پیشوند کلید کش.

    Returns:
        str: پیشوند کلید کش
    """
    return getattr(settings, 'CACHE_KEY_PREFIX', 'ma2ta')


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    تولید کلید کش بر اساس پارامترها.

    Args:
        prefix: پیشوند کلید
        *args: پارامترهای موقعیتی
        **kwargs: پارامترهای کلیدی

    Returns:
        str: کلید کش تولید شده
    """
    # تولید رشته از آرگومان‌ها
    key_parts = [prefix]

    if args:
        for arg in args:
            if isinstance(arg, (str, int, float, bool, type(None))):
                key_parts.append(str(arg))
            elif hasattr(arg, 'pk') and arg.pk:
                # برای مدل‌های Django
                key_parts.append(f"{arg.__class__.__name__}_{arg.pk}")
            elif isinstance(arg, dict):
                # برای دیکشنری‌ها، سعی می‌کنیم مرتب کنیم
                try:
                    key_parts.append(json.dumps(arg, sort_keys=True))
                except (TypeError, ValueError):
                    key_parts.append(str(hash(frozenset(arg.items()))))
            else:
                key_parts.append(str(hash(arg)))

    if kwargs:
        # مرتب‌سازی کلیدها برای ثبات
        sorted_items = sorted(kwargs.items())
        for k, v in sorted_items:
            if isinstance(v, (str, int, float, bool, type(None))):
                key_parts.append(f"{k}_{v}")
            elif hasattr(v, 'pk') and v.pk:
                key_parts.append(f"{k}_{v.__class__.__name__}_{v.pk}")
            elif isinstance(v, dict):
                try:
                    key_parts.append(f"{k}_{json.dumps(v, sort_keys=True)}")
                except (TypeError, ValueError):
                    key_parts.append(f"{k}_{hash(frozenset(v.items()))}")
            else:
                key_parts.append(f"{k}_{hash(v)}")

    # ترکیب بخش‌ها و ایجاد هش MD5
    key_string = '|'.join(key_parts)
    hashed_key = hashlib.md5(key_string.encode()).hexdigest()

    # ایجاد کلید نهایی با پیشوند کش
    return f"{get_cache_key_prefix()}:{prefix}:{hashed_key}"


def cache_page_with_params(timeout: int = 60 * 15, params: Optional[List[str]] = None) -> Callable:
    """
    دکوراتور برای کش کردن صفحات با در نظر گرفتن پارامترهای درخواست.

    Args:
        timeout: مدت زمان کش به ثانیه (پیش‌فرض: 15 دقیقه)
        params: لیست پارامترهای URL که باید در کلید کش لحاظ شوند

    Returns:
        Callable: دکوراتور
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # ایجاد کلید کش با در نظر گرفتن پارامترهای درخواست
            key_params = {}

            if params:
                for param in params:
                    if param in request.GET:
                        key_params[param] = request.GET.get(param)

            # ایجاد کلید کش
            cache_key = generate_cache_key(
                f"page:{request.path}",
                user_id=getattr(request.user, 'id', 0),
                lang=getattr(request, 'LANGUAGE_CODE', 'fa'),
                **key_params
            )

            # بررسی کش
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response

            # اجرای تابع اصلی
            response = view_func(request, *args, **kwargs)

            # ذخیره در کش (فقط پاسخ‌های HTTP 200)
            if hasattr(response, 'status_code') and response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


def cache_method(timeout: int = 60 * 15, key_prefix: Optional[str] = None) -> Callable:
    """
    دکوراتور برای کش کردن نتیجه متد کلاس.

    Args:
        timeout: مدت زمان کش به ثانیه (پیش‌فرض: 15 دقیقه)
        key_prefix: پیشوند کلید کش

    Returns:
        Callable: دکوراتور
    """

    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # ایجاد پیشوند کلید
            prefix = key_prefix or f"{self.__class__.__name__}:{method.__name__}"

            # ایجاد کلید کش
            if hasattr(self, 'pk') and self.pk:
                cache_key = generate_cache_key(prefix, self.pk, *args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, hash(self), *args, **kwargs)

            # بررسی کش
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # اجرای متد اصلی
            result = method(self, *args, **kwargs)

            # ذخیره در کش
            cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def cache_function(timeout: int = 60 * 15, key_prefix: Optional[str] = None) -> Callable:
    """
    دکوراتور برای کش کردن نتیجه یک تابع.

    Args:
        timeout: مدت زمان کش به ثانیه (پیش‌فرض: 15 دقیقه)
        key_prefix: پیشوند کلید کش

    Returns:
        Callable: دکوراتور
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # ایجاد پیشوند کلید
            prefix = key_prefix or f"func:{func.__module__}:{func.__name__}"

            # ایجاد کلید کش
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # بررسی کش
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # اجرای تابع اصلی
            result = func(*args, **kwargs)

            # ذخیره در کش
            cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def cache_queryset(timeout: int = 60 * 15, key_func: Optional[Callable] = None) -> Callable:
    """
    دکوراتور برای کش کردن نتیجه یک کوئری.

    Args:
        timeout: مدت زمان کش به ثانیه (پیش‌فرض: 15 دقیقه)
        key_func: تابع اختیاری برای تولید کلید کش

    Returns:
        Callable: دکوراتور
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # ایجاد کلید کش
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                model_name = args[0].__name__ if args and isinstance(args[0], type) else 'queryset'
                prefix = f"query:{model_name}:{func.__name__}"
                cache_key = generate_cache_key(prefix, *args, **kwargs)

            # بررسی کش
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # اجرای تابع اصلی
            result = func(*args, **kwargs)

            # اگر نتیجه یک کوئری‌ست است، آن را به لیست تبدیل می‌کنیم
            if isinstance(result, QuerySet):
                result = list(result)

            # ذخیره در کش
            cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def invalidate_cache_key(key: str) -> bool:
    """
    حذف یک کلید خاص از کش.

    Args:
        key: کلید کش

    Returns:
        bool: True اگر کلید با موفقیت حذف شد، در غیر این صورت False
    """
    try:
        cache.delete(key)
        return True
    except Exception as e:
        logger.error(f"خطا در حذف کلید کش {key}: {str(e)}")
        return False


def invalidate_model_cache(model_instance: Model, action: str = 'all') -> None:
    """
    حذف کش مربوط به یک نمونه مدل.

    Args:
        model_instance: نمونه مدل
        action: نوع عملیات ('all', 'detail', 'list')
    """
    try:
        model_name = model_instance.__class__.__name__.lower()
        model_id = getattr(model_instance, 'pk', None)

        if not model_id:
            return

        # الگوی کلیدهای کش برای حذف
        patterns = []

        if action in ('all', 'detail'):
            # کلیدهای مربوط به جزئیات
            patterns.append(f"{get_cache_key_prefix()}:{model_name}_detail:*")
            patterns.append(f"{get_cache_key_prefix()}:{model_name}:{model_id}:*")

        if action in ('all', 'list'):
            # کلیدهای مربوط به لیست
            patterns.append(f"{get_cache_key_prefix()}:{model_name}_list:*")
            patterns.append(f"{get_cache_key_prefix()}:query:{model_name.__class__.__name__}:*")

        # حذف کلیدهای منطبق
        for pattern in patterns:
            # جایگزین کنید با روشی که برای حذف با الگو در سیستم کش شما مناسب است
            # بسته به backend کش شما، ممکن است نیاز به روش متفاوتی داشته باشید
            keys = cache.keys(pattern) if hasattr(cache, 'keys') else []
            for key in keys:
                cache.delete(key)

        logger.debug(f"کش برای {model_name} با شناسه {model_id} حذف شد")

    except Exception as e:
        logger.error(f"خطا در حذف کش مدل: {str(e)}")


def cache_api_response(timeout: int = 60 * 15, cache_anonymous_only: bool = False) -> Callable:
    """
    دکوراتور برای کش کردن پاسخ‌های API.

    Args:
        timeout: مدت زمان کش به ثانیه (پیش‌فرض: 15 دقیقه)
        cache_anonymous_only: آیا فقط برای کاربران ناشناس کش شود

    Returns:
        Callable: دکوراتور
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # بررسی می‌کنیم فقط برای درخواست‌های GET کش می‌کنیم
            if request.method != 'GET':
                return view_func(self, request, *args, **kwargs)

            # اگر فقط برای کاربران ناشناس کش می‌کنیم و کاربر وارد شده است
            if cache_anonymous_only and request.user.is_authenticated:
                return view_func(self, request, *args, **kwargs)

            # ایجاد کلید کش
            user_id = 0 if not request.user.is_authenticated else request.user.id

            # پارامترهای URL
            query_params = {k: v for k, v in request.GET.items()}

            # ایجاد کلید کش
            cache_key = generate_cache_key(
                f"api:{request.path}",
                user_id=user_id,
                lang=getattr(request, 'LANGUAGE_CODE', 'fa'),
                params=query_params
            )

            # بررسی کش
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # اجرای تابع اصلی
            response = view_func(self, request, *args, **kwargs)

            # ذخیره در کش (فقط پاسخ‌های موفق)
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


def cache_control_decorator(max_age: int = 60 * 15,
                            public: bool = True,
                            must_revalidate: bool = False) -> Callable:
    """
    دکوراتور برای تنظیم هدرهای کنترل کش HTTP.

    Args:
        max_age: حداکثر عمر کش به ثانیه (پیش‌فرض: 15 دقیقه)
        public: آیا کش عمومی باشد
        must_revalidate: آیا اعتبارسنجی مجدد لازم است

    Returns:
        Callable: دکوراتور
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            response = view_func(*args, **kwargs)

            if hasattr(response, 'has_header') and not response.has_header('Cache-Control'):
                cache_control = []

                if public:
                    cache_control.append('public')
                else:
                    cache_control.append('private')

                cache_control.append(f"max-age={max_age}")

                if must_revalidate:
                    cache_control.append('must-revalidate')

                response['Cache-Control'] = ', '.join(cache_control)

            return response

        return wrapper

    return decorator


def get_cached_queryset(model: Type[Model],
                        timeout: int = 60 * 15,
                        filter_kwargs: Optional[Dict] = None,
                        key_prefix: Optional[str] = None) -> List[Model]:
    """
    دریافت کوئری‌ست کش شده از یک مدل.

    Args:
        model: کلاس مدل
        timeout: مدت زمان کش به ثانیه (پیش‌فرض: 15 دقیقه)
        filter_kwargs: پارامترهای فیلتر (اختیاری)
        key_prefix: پیشوند کلید کش (اختیاری)

    Returns:
        List[Model]: لیست نمونه‌های مدل
    """
    filter_kwargs = filter_kwargs or {}
    model_name = model.__name__.lower()
    prefix = key_prefix or f"queryset:{model_name}"

    # ایجاد کلید کش
    cache_key = generate_cache_key(prefix, **filter_kwargs)

    # بررسی کش
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # اجرای کوئری
    queryset = model.objects.filter(**filter_kwargs)
    result = list(queryset)

    # ذخیره در کش
    cache.set(cache_key, result, timeout)

    return result


def clear_cache_pattern(pattern: str) -> int:
    """
    پاک کردن کلیدهای کش منطبق با الگو.

    Args:
        pattern: الگوی کلید کش

    Returns:
        int: تعداد کلیدهای حذف شده
    """
    try:
        # این متد به backend کش شما بستگی دارد
        # برای Redis، می‌توانید از client.keys استفاده کنید
        # برای سایر backend‌ها، ممکن است نیاز به پیاده‌سازی خاص داشته باشید
        if hasattr(cache, 'keys'):
            keys = cache.keys(pattern)
            if keys:
                count = 0
                for key in keys:
                    cache.delete(key)
                    count += 1

                logger.debug(f"{count} کلید کش با الگوی {pattern} حذف شد")
                return count

        logger.warning(f"امکان حذف کش با الگو برای backend فعلی وجود ندارد")
        return 0

    except Exception as e:
        logger.error(f"خطا در حذف کش با الگوی {pattern}: {str(e)}")
        return 0