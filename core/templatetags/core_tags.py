# core/templatetags/core_tags.py

from datetime import datetime
import jdatetime
import re
import json
from urllib.parse import urlencode

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.html import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from django.utils.timezone import localtime
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


# ------------------- فیلترهای قالب برای تاریخ و زمان ------------------- #

@register.filter(name='jalali_date')
def jalali_date(value, format_string=None):
    """تبدیل تاریخ میلادی به تاریخ شمسی (جلالی)"""
    if not value:
        return ''

    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return value

    if not format_string:
        format_string = "%Y/%m/%d"

    jalali_date = jdatetime.date.fromgregorian(date=value.date())
    return jalali_date.strftime(format_string)


@register.filter(name='jalali_datetime')
def jalali_datetime(value, format_string=None):
    """تبدیل تاریخ و زمان میلادی به تاریخ و زمان شمسی (جلالی)"""
    if not value:
        return ''

    if not format_string:
        format_string = "%Y/%m/%d %H:%M"

    local_datetime = localtime(value)
    jalali_datetime = jdatetime.datetime.fromgregorian(datetime=local_datetime)
    return jalali_datetime.strftime(format_string)


@register.filter(name='time_since')
def time_since_filter(value):
    """نمایش زمان سپری شده از یک تاریخ به صورت انسان‌خوان"""
    if not value:
        return ''

    now = datetime.now(value.tzinfo) if hasattr(value, 'tzinfo') else datetime.now()
    diff = now - value

    seconds = diff.total_seconds()

    if seconds < 60:
        return _('همین الان')
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return _('%d دقیقه پیش') % minutes
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return _('%d ساعت پیش') % hours
    elif seconds < 604800:
        days = int(seconds // 86400)
        return _('%d روز پیش') % days
    else:
        # برای زمان‌های قدیمی‌تر از تاریخ شمسی استفاده می‌کنیم
        return jalali_date(value)


# ------------------- فیلترهای قالب برای قیمت و ارقام ------------------- #

@register.filter(name='price_format')
def price_format(value):
    """
    فرمت‌بندی قیمت با جداکننده هزارتایی و واحد پول

    مثال:
        {{ product.price|price_format }} -> ۱,۵۰۰,۰۰۰ تومان
    """
    if not value and value != 0:
        return ''

    try:
        value = int(value)
        formatted = intcomma(value)

        # تبدیل اعداد انگلیسی به فارسی اگر زبان فارسی باشد
        if get_language() == 'fa':
            formatted = to_persian_numbers(formatted)

        return f"{formatted} تومان"
    except (ValueError, TypeError):
        return value


@register.filter(name='to_persian_numbers')
def to_persian_numbers(value):
    """تبدیل اعداد انگلیسی به فارسی"""
    if not value:
        return value

    value = str(value)
    persian_numerals = {
        '0': '۰',
        '1': '۱',
        '2': '۲',
        '3': '۳',
        '4': '۴',
        '5': '۵',
        '6': '۶',
        '7': '۷',
        '8': '۸',
        '9': '۹',
        '.': '.',
        ',': '،',
    }

    return ''.join(persian_numerals.get(c, c) for c in value)


@register.filter(name='to_english_numbers')
def to_english_numbers(value):
    """تبدیل اعداد فارسی به انگلیسی"""
    if not value:
        return value

    value = str(value)
    english_numerals = {
        '۰': '0',
        '۱': '1',
        '۲': '2',
        '۳': '3',
        '۴': '4',
        '۵': '5',
        '۶': '6',
        '۷': '7',
        '۸': '8',
        '۹': '9',
        '٠': '0',
        '١': '1',
        '٢': '2',
        '٣': '3',
        '٤': '4',
        '٥': '5',
        '٦': '6',
        '٧': '7',
        '٨': '8',
        '٩': '9',
        '،': ',',
    }

    return ''.join(english_numerals.get(c, c) for c in value)


@register.filter(name='discount_percentage')
def discount_percentage(original_price, sale_price):
    """محاسبه درصد تخفیف"""
    if not original_price or not sale_price:
        return 0

    try:
        original_price = float(original_price)
        sale_price = float(sale_price)

        if original_price <= 0:
            return 0

        discount = ((original_price - sale_price) / original_price) * 100
        return int(discount)
    except (ValueError, TypeError):
        return 0


# ------------------- فیلترهای قالب برای متن و محتوا ------------------- #

@register.filter(name='truncate_chars')
def truncate_chars(value, max_length):
    """کوتاه کردن متن با تعداد مشخصی کاراکتر"""
    if not value:
        return ''

    value = str(value)
    if len(value) <= max_length:
        return value

    return value[:max_length] + '...'


@register.filter(name='strip_tags')
@stringfilter
def strip_tags_filter(value):
    """حذف تگ‌های HTML از متن"""
    import re
    return re.sub(r'<[^>]*?>', '', value)


@register.filter(name='phone_format')
def phone_format(value):
    """
    فرمت‌بندی شماره تلفن همراه

    مثال:
        {{ user.phone|phone_format }} -> ۰۹۱۲-۳۴۵-۶۷۸۹
    """
    if not value:
        return ''

    value = str(value)
    if not value.isdigit():
        return value

    if len(value) == 11 and value.startswith('09'):
        formatted = f"{value[:4]}-{value[4:7]}-{value[7:11]}"

        # تبدیل به اعداد فارسی در صورت نیاز
        if get_language() == 'fa':
            formatted = to_persian_numbers(formatted)

        return formatted

    return value


@register.filter(name='get_translation')
def get_translation(obj, field_name):
    """دریافت ترجمه فیلد از مدل‌هایی که TranslatableMixin را پیاده‌سازی کرده‌اند"""
    if not obj or not hasattr(obj, 'get_translation'):
        return getattr(obj, field_name, '')

    current_language = get_language() or settings.LANGUAGE_CODE
    return obj.get_translation(field_name, current_language)


# ------------------- تگ‌های قالب برای تصاویر و رسانه‌ها ------------------- #

@register.simple_tag
def thumbnail(image_url, width=None, height=None, crop=False):
    """
    ساخت آدرس تصویر بندانگشتی

    مثال:
        {% thumbnail artwork.image 300 200 crop=True %}
    """
    if not image_url:
        return settings.STATIC_URL + 'images/default_thumbnail.jpg'

    # ساخت مسیر تامبنیل با پارامترهای ابعاد
    # در اینجا فرض شده که از سرویسی مانند Easy Thumbnails یا
    # Sorl-thumbnail استفاده می‌شود که با query string ابعاد را مشخص می‌کند
    params = {}

    if width:
        params['w'] = width
    if height:
        params['h'] = height
    if crop:
        params['crop'] = 1

    if params:
        # ایجاد query string برای تصویر
        query_string = urlencode(params)

        # اضافه کردن پارامترها به URL تصویر
        if '?' in image_url:
            thumbnail_url = f"{image_url}&{query_string}"
        else:
            thumbnail_url = f"{image_url}?{query_string}"

        return thumbnail_url

    return image_url


@register.simple_tag
def media_url(path):
    """
    ساخت آدرس کامل فایل رسانه‌ای

    مثال:
        {% media_url 'artists/profile.jpg' %}
    """
    if not path:
        return ''

    if path.startswith(('http://', 'https://')):
        return path

    if path.startswith('/'):
        path = path[1:]

    return f"{settings.MEDIA_URL}{path}"


# ------------------- تگ‌های قالب برای کنترل دسترسی و کاربران ------------------- #

@register.simple_tag(takes_context=True)
def is_artist(context):
    """بررسی اینکه آیا کاربر جاری هنرمند است یا خیر"""
    user = context.get('user')
    if not user or not user.is_authenticated:
        return False

    return hasattr(user, 'artist_profile') and user.artist_profile is not None


@register.simple_tag(takes_context=True)
def is_artwork_owner(context, artwork):
    """بررسی اینکه آیا کاربر جاری صاحب اثر هنری است یا خیر"""
    user = context.get('user')
    if not user or not user.is_authenticated:
        return False

    # مدیران سایت به همه آثار دسترسی دارند
    if user.is_staff:
        return True

    # بررسی اینکه آیا کاربر، هنرمند مالک اثر است
    if hasattr(user, 'artist_profile') and user.artist_profile:
        return artwork.artist == user.artist_profile

    return False


@register.simple_tag(takes_context=True)
def can_purchase_artwork(context, artwork):
    """بررسی اینکه آیا کاربر می‌تواند این اثر هنری را خریداری کند یا خیر"""
    user = context.get('user')

    # اگر اثر قابل فروش نیست یا قبلاً فروخته شده
    if artwork.status not in ['published', 'featured'] or artwork.is_sold:
        return False

    # هنرمندان نمی‌توانند آثار خود را بخرند
    if user and user.is_authenticated and hasattr(user, 'artist_profile') and user.artist_profile:
        if artwork.artist == user.artist_profile:
            return False

    return True


# ------------------- تگ‌های قالب برای مسیریابی و URL ها ------------------- #

@register.simple_tag(takes_context=True)
def active_url(context, url_name, css_class='active'):
    """
    بررسی اینکه URL فعلی با نام URL مشخص شده مطابقت دارد یا خیر

    مثال:
        <li class="{% active_url 'home' %}">خانه</li>
    """
    request = context.get('request')
    if not request:
        return ''

    if request.resolver_match and request.resolver_match.url_name == url_name:
        return css_class

    return ''


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    ایجاد query string جدید با حفظ پارامترهای فعلی و افزودن/تغییر پارامترهای جدید

    مثال برای صفحه‌بندی با حفظ فیلترها:
        <a href="?{% query_transform page=next_page %}">صفحه بعد</a>
    """
    request = context.get('request')
    if not request:
        return ''

    updated = request.GET.copy()

    # حذف پارامترهایی که مقدار None دارند
    for key, value in kwargs.items():
        if value is None and key in updated:
            del updated[key]
        elif value is not None:
            updated[key] = value

    return updated.urlencode()


# ------------------- تگ‌های قالب برای اشیاء و JSON ------------------- #

@register.filter(name='to_json')
def to_json(value):
    """تبدیل یک شیء پایتون به JSON"""
    return mark_safe(json.dumps(value, cls=DjangoJSONEncoder))


@register.filter(name='get_item')
def get_item(dictionary, key):
    """دسترسی به مقدار یک کلید در دیکشنری"""
    if not dictionary:
        return None

    return dictionary.get(key)


@register.filter(name='get_obj_attr')
def get_obj_attr(obj, attr):
    """دسترسی به مقدار یک ویژگی در شیء"""
    if not obj:
        return None

    # پشتیبانی از دسترسی به ویژگی‌های تودرتو با نقطه
    # مثال: get_obj_attr(user, "artist_profile.bio")
    attrs = attr.split('.')
    value = obj

    for a in attrs:
        value = getattr(value, a, None)
        if value is None:
            break

    return value


# ------------------- تگ‌های قالب برای لوکالیزاسیون و چندزبانگی ------------------- #

@register.simple_tag
def get_current_language():
    """دریافت زبان فعلی"""
    return get_language() or settings.LANGUAGE_CODE


@register.simple_tag
def get_language_direction():
    """
    دریافت جهت زبان (راست به چپ یا چپ به راست)

    مثال:
        <html dir="{% get_language_direction %}">
    """
    if get_language() == 'fa':
        return 'rtl'
    return 'ltr'


@register.simple_tag
def get_available_languages():
    """دریافت زبان‌های در دسترس"""
    return settings.LANGUAGES


# ------------------- تگ‌های قالب برای نمایش وضعیت ------------------- #

@register.simple_tag
def order_status_badge(status):
    """
    نمایش وضعیت سفارش با کلاس‌های متناسب برای رنگ‌بندی

    مثال:
        {% order_status_badge order.status %}
    """
    status_classes = {
        'pending': 'badge-warning',
        'processing': 'badge-info',
        'shipped': 'badge-primary',
        'delivered': 'badge-success',
        'canceled': 'badge-danger',
        'returned': 'badge-secondary',
        'refunded': 'badge-dark',
    }

    status_texts = {
        'pending': _('در انتظار پرداخت'),
        'processing': _('در حال پردازش'),
        'shipped': _('ارسال شده'),
        'delivered': _('تحویل داده شده'),
        'canceled': _('لغو شده'),
        'returned': _('مرجوع شده'),
        'refunded': _('بازپرداخت شده'),
    }

    css_class = status_classes.get(status, 'badge-secondary')
    text = status_texts.get(status, status)

    return mark_safe(f'<span class="badge {css_class}">{text}</span>')


@register.simple_tag
def artwork_status_badge(status, is_sold=False):
    """
    نمایش وضعیت اثر هنری با کلاس‌های متناسب برای رنگ‌بندی

    مثال:
        {% artwork_status_badge artwork.status artwork.is_sold %}
    """
    if is_sold:
        return mark_safe(f'<span class="badge badge-danger">{_("فروخته شده")}</span>')

    status_classes = {
        'draft': 'badge-secondary',
        'published': 'badge-success',
        'featured': 'badge-primary',
        'archived': 'badge-dark',
        'auction': 'badge-warning',
    }

    status_texts = {
        'draft': _('پیش‌نویس'),
        'published': _('منتشر شده'),
        'featured': _('ویژه'),
        'archived': _('بایگانی شده'),
        'auction': _('در حراجی'),
    }

    css_class = status_classes.get(status, 'badge-secondary')
    text = status_texts.get(status, status)

    return mark_safe(f'<span class="badge {css_class}">{text}</span>')