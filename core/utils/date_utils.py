# core/utils/date_utils.py

import datetime
import jdatetime
from typing import Tuple, Optional, Union
from django.utils import timezone


def get_persian_date(gregorian_date: Optional[datetime.datetime] = None,
                     date_format: str = '%Y/%m/%d') -> str:
    """
    تبدیل تاریخ میلادی به شمسی و برگرداندن آن به صورت رشته.

    Args:
        gregorian_date: تاریخ میلادی (اگر ارائه نشود، از تاریخ فعلی استفاده می‌شود)
        date_format: قالب تاریخ خروجی

    Returns:
        str: تاریخ شمسی با قالب مشخص شده
    """
    if gregorian_date is None:
        gregorian_date = timezone.now()

    jalali_date = jdatetime.datetime.fromgregorian(
        datetime=gregorian_date
    )

    return jalali_date.strftime(date_format)


def convert_to_jalali(gregorian_date: datetime.datetime) -> jdatetime.datetime:
    """
    تبدیل تاریخ میلادی به شمسی.

    Args:
        gregorian_date: تاریخ میلادی

    Returns:
        jdatetime.datetime: تاریخ شمسی
    """
    return jdatetime.datetime.fromgregorian(datetime=gregorian_date)


def convert_from_jalali(jalali_date: jdatetime.datetime) -> datetime.datetime:
    """
    تبدیل تاریخ شمسی به میلادی.

    Args:
        jalali_date: تاریخ شمسی

    Returns:
        datetime.datetime: تاریخ میلادی
    """
    return jalali_date.togregorian()


def calculate_date_difference(start_date: datetime.datetime,
                              end_date: Optional[datetime.datetime] = None) -> Tuple[int, int, int]:
    """
    محاسبه اختلاف زمانی بین دو تاریخ.

    Args:
        start_date: تاریخ شروع
        end_date: تاریخ پایان (اگر ارائه نشود، از تاریخ فعلی استفاده می‌شود)

    Returns:
        Tuple[int, int, int]: تعداد سال‌ها، ماه‌ها و روزهای بین دو تاریخ
    """
    if end_date is None:
        end_date = timezone.now()

    delta = end_date - start_date

    years = delta.days // 365
    remaining_days = delta.days % 365
    months = remaining_days // 30
    days = remaining_days % 30

    return years, months, days


def get_shamsi_month_name(month_number: int) -> str:
    """
    دریافت نام فارسی ماه شمسی.

    Args:
        month_number: شماره ماه (1 تا 12)

    Returns:
        str: نام فارسی ماه
    """
    if not 1 <= month_number <= 12:
        raise ValueError("شماره ماه باید بین 1 تا 12 باشد")

    shamsi_months = [
        'فروردین', 'اردیبهشت', 'خرداد',
        'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر',
        'دی', 'بهمن', 'اسفند'
    ]

    return shamsi_months[month_number - 1]


def format_date_human_readable(date: Union[datetime.datetime, jdatetime.datetime]) -> str:
    """
    فرمت تاریخ به صورت خوانا برای انسان.

    مثال: ۲۳ مرداد ۱۴۰۲

    Args:
        date: تاریخ میلادی یا شمسی

    Returns:
        str: تاریخ فرمت شده
    """
    if isinstance(date, datetime.datetime):
        jalali_date = convert_to_jalali(date)
    else:
        jalali_date = date

    day = jalali_date.day
    month = get_shamsi_month_name(jalali_date.month)
    year = jalali_date.year

    return f"{day} {month} {year}"


def get_time_ago(date: datetime.datetime) -> str:
    """
    محاسبه زمان سپری شده از یک تاریخ به صورت متنی.

    مثال: ۲ ساعت پیش، ۳ روز پیش

    Args:
        date: تاریخ مورد نظر

    Returns:
        str: زمان سپری شده به صورت متنی
    """
    now = timezone.now()
    diff = now - date

    seconds = diff.total_seconds()

    if seconds < 60:
        return "چند لحظه پیش"

    minutes = seconds // 60
    if minutes < 60:
        return f"{int(minutes)} دقیقه پیش"

    hours = minutes // 60
    if hours < 24:
        return f"{int(hours)} ساعت پیش"

    days = hours // 24
    if days < 7:
        return f"{int(days)} روز پیش"

    weeks = days // 7
    if weeks < 5:
        return f"{int(weeks)} هفته پیش"

    months = days // 30
    if months < 12:
        return f"{int(months)} ماه پیش"

    years = days // 365
    return f"{int(years)} سال پیش"