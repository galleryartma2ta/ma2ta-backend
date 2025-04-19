# core/validators/phone_validators.py

import re
from typing import Optional
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.utils.string_utils import convert_persian_numbers_to_english


def normalize_phone_number(phone: str) -> str:
    """
    نرمال‌سازی شماره تلفن (حذف کاراکترهای اضافی و تبدیل اعداد فارسی به انگلیسی).

    Args:
        phone: شماره تلفن

    Returns:
        str: شماره تلفن نرمال شده
    """
    # تبدیل اعداد فارسی به انگلیسی
    phone = convert_persian_numbers_to_english(phone)

    # حذف فاصله‌ها، خط تیره و پرانتز
    phone = re.sub(r'[\s\-\(\)]', '', phone)

    return phone


def validate_iran_phone(phone: str) -> Optional[str]:
    """
    اعتبارسنجی شماره تلفن ایرانی.

    Args:
        phone: شماره تلفن

    Returns:
        Optional[str]: شماره تلفن نرمال شده یا None در صورت عدم اعتبار

    Raises:
        ValidationError: اگر شماره تلفن نامعتبر باشد
    """
    # نرمال‌سازی شماره تلفن
    phone = normalize_phone_number(phone)

    # الگوی شماره تلفن همراه ایرانی (مثلا: 09123456789 یا +989123456789)
    mobile_pattern = r'^(?:0|98|\+98)9\d{9}$'

    # الگوی شماره تلفن ثابت ایرانی (مثلا: 02112345678 یا +982112345678)
    landline_pattern = r'^(?:0|98|\+98)(?:[1-9]\d{9})$'

    if re.match(mobile_pattern, phone):
        # استخراج 10 رقم آخر
        last_10_digits = phone[-10:]

        # استانداردسازی شماره تلفن همراه با فرمت 09XXXXXXXXX
        return f"09{last_10_digits[-9:]}"

    elif re.match(landline_pattern, phone):
        # استخراج 11 رقم آخر
        last_11_digits = phone[-11:]

        # استانداردسازی شماره تلفن ثابت با فرمت 0XXXXXXXXXX
        return f"0{last_11_digits[-10:]}"

    else:
        raise ValidationError(_('شماره تلفن وارد شده معتبر نیست.'))


def validate_iran_mobile(phone: str) -> Optional[str]:
    """
    اعتبارسنجی شماره تلفن همراه ایرانی.

    Args:
        phone: شماره تلفن همراه

    Returns:
        Optional[str]: شماره تلفن همراه نرمال شده یا None در صورت عدم اعتبار

    Raises:
        ValidationError: اگر شماره تلفن همراه نامعتبر باشد
    """
    # نرمال‌سازی شماره تلفن
    phone = normalize_phone_number(phone)

    # الگوی شماره تلفن همراه ایرانی
    pattern = r'^(?:0|98|\+98)9\d{9}$'

    if re.match(pattern, phone):
        # استخراج 10 رقم آخر
        last_10_digits = phone[-10:]

        # استانداردسازی شماره تلفن همراه با فرمت 09XXXXXXXXX
        return f"09{last_10_digits[-9:]}"

    else:
        raise ValidationError(_('شماره تلفن همراه وارد شده معتبر نیست.'))


def validate_iran_landline(phone: str, province_code: Optional[bool] = True) -> Optional[str]:
    """
    اعتبارسنجی شماره تلفن ثابت ایرانی.

    Args:
        phone: شماره تلفن ثابت
        province_code: آیا شماره تلفن باید شامل کد استان باشد

    Returns:
        Optional[str]: شماره تلفن ثابت نرمال شده یا None در صورت عدم اعتبار

    Raises:
        ValidationError: اگر شماره تلفن ثابت نامعتبر باشد
    """
    # نرمال‌سازی شماره تلفن
    phone = normalize_phone_number(phone)

    if province_code:
        # الگوی شماره تلفن ثابت با کد استان (مثلا: 02112345678)
        pattern = r'^(?:0|98|\+98)(?:[1-9]\d{9})$'

        if re.match(pattern, phone):
            # استخراج 11 رقم آخر
            last_11_digits = phone[-11:]

            # استانداردسازی شماره تلفن ثابت با فرمت 0XXXXXXXXXX
            return f"0{last_11_digits[-10:]}"

        else:
            raise ValidationError(_('شماره تلفن ثابت وارد شده معتبر نیست.'))

    else:
        # الگوی شماره تلفن ثابت بدون کد استان (مثلا: 12345678)
        pattern = r'^(?:\d{8})$'

        if re.match(pattern, phone):
            return phone

        else:
            raise ValidationError(_('شماره تلفن ثابت وارد شده معتبر نیست (بدون کد استان باید 8 رقم باشد).'))


def validate_international_phone(phone: str) -> Optional[str]:
    """
    اعتبارسنجی شماره تلفن بین‌المللی.

    Args:
        phone: شماره تلفن بین‌المللی

    Returns:
        Optional[str]: شماره تلفن بین‌المللی نرمال شده یا None در صورت عدم اعتبار

    Raises:
        ValidationError: اگر شماره تلفن بین‌المللی نامعتبر باشد
    """
    # نرمال‌سازی شماره تلفن
    phone = normalize_phone_number(phone)

    # حذف علامت + اضافی
    if phone.startswith('+'):
        phone = '+' + phone[1:].lstrip('+')

    # الگوی شماره تلفن بین‌المللی (شروع با + و سپس 7 تا 15 رقم)
    pattern = r'^\+[1-9]\d{6,14}$'

    if re.match(pattern, phone):
        return phone

    else:
        raise ValidationError(_('شماره تلفن بین‌المللی وارد شده معتبر نیست.'))


def validate_iran_postal_code(postal_code: str) -> Optional[str]:
    """
    اعتبارسنجی کد پستی ایرانی.

    Args:
        postal_code: کد پستی

    Returns:
        Optional[str]: کد پستی نرمال شده یا None در صورت عدم اعتبار

    Raises:
        ValidationError: اگر کد پستی نامعتبر باشد
    """
    # نرمال‌سازی کد پستی
    postal_code = normalize_phone_number(postal_code)

    # الگوی کد پستی ایرانی (10 رقم)
    pattern = r'^\d{10}$'

    if re.match(pattern, postal_code):
        return postal_code

    else:
        raise ValidationError(_('کد پستی وارد شده معتبر نیست. کد پستی باید 10 رقم باشد.'))


def validate_iran_national_code(national_code: str) -> Optional[str]:
    """
    اعتبارسنجی کد ملی ایرانی.

    Args:
        national_code: کد ملی

    Returns:
        Optional[str]: کد ملی نرمال شده یا None در صورت عدم اعتبار

    Raises:
        ValidationError: اگر کد ملی نامعتبر باشد
    """
    # نرمال‌سازی کد ملی
    national_code = normalize_phone_number(national_code)

    # بررسی طول کد ملی
    if len(national_code) != 10:
        raise ValidationError(_('کد ملی باید 10 رقم باشد.'))

    # بررسی اینکه کد ملی فقط شامل اعداد باشد
    if not national_code.isdigit():
        raise ValidationError(_('کد ملی باید فقط شامل اعداد باشد.'))

    # بررسی اینکه همه ارقام یکسان نباشند
    if national_code == national_code[0] * 10:
        raise ValidationError(_('کد ملی نامعتبر است.'))

    # محاسبه رقم کنترل
    check = int(national_code[9])
    s = sum(int(national_code[i]) * (10 - i) for i in range(9)) % 11

    if (s < 2 and check == s) or (s >= 2 and check == 11 - s):
        return national_code

    else:
        raise ValidationError(_('کد ملی نامعتبر است.'))