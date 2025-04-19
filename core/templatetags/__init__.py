# core/templatetags/__init__.py

from core.templatetags.core_tags import (
    # فیلترها و تگ‌های تاریخ و زمان
    jalali_date,
    jalali_datetime,
    time_since_filter,

    # فیلترها و تگ‌های قیمت و ارقام
    price_format,
    to_persian_numbers,
    to_english_numbers,
    discount_percentage,

    # فیلترها و تگ‌های متن و محتوا
    truncate_chars,
    strip_tags_filter,
    phone_format,
    get_translation,

    # تگ‌های تصاویر و رسانه‌ها
    thumbnail,
    media_url,

    # تگ‌های کنترل دسترسی و کاربران
    is_artist,
    is_artwork_owner,
    can_purchase_artwork,

    # تگ‌های مسیریابی و URL
    active_url,
    query_transform,

    # تگ‌های اشیاء و JSON
    to_json,
    get_item,
    get_obj_attr,

    # تگ‌های لوکالیزاسیون و چندزبانگی
    get_current_language,
    get_language_direction,
    get_available_languages,

    # تگ‌های نمایش وضعیت
    order_status_badge,
    artwork_status_badge,
)

__all__ = [
    # تاریخ و زمان
    'jalali_date',
    'jalali_datetime',
    'time_since_filter',

    # قیمت و ارقام
    'price_format',
    'to_persian_numbers',
    'to_english_numbers',
    'discount_percentage',

    # متن و محتوا
    'truncate_chars',
    'strip_tags_filter',
    'phone_format',
    'get_translation',

    # تصاویر و رسانه‌ها
    'thumbnail',
    'media_url',

    # کنترل دسترسی و کاربران
    'is_artist',
    'is_artwork_owner',
    'can_purchase_artwork',

    # مسیریابی و URL
    'active_url',
    'query_transform',

    # اشیاء و JSON
    'to_json',
    'get_item',
    'get_obj_attr',

    # لوکالیزاسیون و چندزبانگی
    'get_current_language',
    'get_language_direction',
    'get_available_languages',

    # نمایش وضعیت
    'order_status_badge',
    'artwork_status_badge',
]