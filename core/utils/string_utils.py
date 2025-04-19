# core/utils/string_utils.py

import re
import uuid
import unicodedata
from typing import Optional, Tuple, List
from django.utils.text import slugify


def generate_slug(text: str, allow_unicode: bool = True) -> str:
    """
    تولید اسلاگ از متن.

    Args:
        text: متن اصلی
        allow_unicode: اجازه استفاده از یونیکد

    Returns:
        str: اسلاگ تولید شده
    """
    # تولید اسلاگ با استفاده از تابع slugify جنگو
    slug = slugify(text, allow_unicode=allow_unicode)

    # اگر خالی بود، یک UUID تولید کنید
    if not slug:
        slug = uuid.uuid4().hex[:8]

    return slug


def generate_unique_slug(text: str, check_exists_func,
                         allow_unicode: bool = True) -> str:
    """
    تولید اسلاگ یکتا از متن.

    Args:
        text: متن اصلی
        check_exists_func: تابعی که بررسی می‌کند آیا اسلاگ موجود است
        allow_unicode: اجازه استفاده از یونیکد

    Returns:
        str: اسلاگ یکتای تولید شده
    """
    # تولید اسلاگ اولیه
    slug = generate_slug(text, allow_unicode=allow_unicode)

    # بررسی یکتا بودن
    original_slug = slug
    counter = 1

    while check_exists_func(slug):
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug


def normalize_persian_text(text: str) -> str:
    """
    نرمال‌سازی متن فارسی.

    Args:
        text: متن فارسی

    Returns:
        str: متن نرمال شده
    """
    # تبدیل اعداد عربی به فارسی
    arabic_to_persian = {
        '٠': '۰', '١': '۱', '٢': '۲', '٣': '۳', '٤': '۴',
        '٥': '۵', '٦': '۶', '٧': '۷', '٨': '۸', '٩': '۹',
        'ي': 'ی', 'ك': 'ک'
    }

    # جایگزینی کاراکترها
    for arabic, persian in arabic_to_persian.items():
        text = text.replace(arabic, persian)

    # نرمال‌سازی فاصله‌ها
    text = re.sub(r'\s+', ' ', text)

    # جایگزینی نیم‌فاصله
    text = text.replace(' ', '‌')

    return text.strip()


def convert_arabic_to_persian(text: str) -> str:
    """
    تبدیل کاراکترهای عربی به فارسی.

    Args:
        text: متن با کاراکترهای عربی

    Returns:
        str: متن با کاراکترهای فارسی
    """
    # جدول تبدیل کاراکترهای عربی به فارسی
    arabic_to_persian = {
        'ي': 'ی',  # ی عربی به ی فارسی
        'ك': 'ک',  # ک عربی به ک فارسی
        '٠': '۰',  # ارقام عربی به فارسی
        '١': '۱',
        '٢': '۲',
        '٣': '۳',
        '٤': '۴',
        '٥': '۵',
        '٦': '۶',
        '٧': '۷',
        '٨': '۸',
        '٩': '۹',
        'ة': 'ه',  # تای گرد به ه
        'إ': 'ا',  # همزه‌دار به ا
        'أ': 'ا',
        'آ': 'ا',
        'ؤ': 'و',  # همزه‌دار به و
        'ئ': 'ی'  # همزه‌دار به ی
    }

    # جایگزینی کاراکترها
    for arabic, persian in arabic_to_persian.items():
        text = text.replace(arabic, persian)

    return text


def remove_special_characters(text: str,
                              keep_chars: Optional[str] = None) -> str:
    """
    حذف کاراکترهای خاص از متن.

    Args:
        text: متن اصلی
        keep_chars: کاراکترهایی که باید حفظ شوند

    Returns:
        str: متن بدون کاراکترهای خاص
    """
    if keep_chars is None:
        keep_chars = ' .-_'

    # الگوی حفظ حروف، اعداد و کاراکترهای مشخص شده
    pattern = f'[^\\w\\d{re.escape(keep_chars)}]+'

    # حذف کاراکترهای خاص
    return re.sub(pattern, '', text)


def truncate_text(text: str, length: int,
                  suffix: str = '...', keep_words: bool = True) -> str:
    """
    کوتاه کردن متن به طول مشخص.

    Args:
        text: متن اصلی
        length: طول مورد نظر
        suffix: پسوند برای متن کوتاه شده
        keep_words: حفظ کلمات کامل

    Returns:
        str: متن کوتاه شده
    """
    if len(text) <= length:
        return text

    if keep_words:
        # کوتاه کردن با حفظ کلمات کامل
        truncated = text[:length].rsplit(' ', 1)[0]
    else:
        # کوتاه کردن دقیقاً به طول مشخص شده
        truncated = text[:length]

    # افزودن پسوند
    return truncated + suffix


def extract_numbers(text: str) -> List[str]:
    """
    استخراج اعداد از متن.

    Args:
        text: متن اصلی

    Returns:
        List[str]: لیست اعداد استخراج شده
    """
    # الگوی تطبیق اعداد (شامل اعداد فارسی)
    pattern = r'[0-9۰-۹]+'

    # استخراج اعداد
    return re.findall(pattern, text)


def convert_persian_numbers_to_english(text: str) -> str:
    """
    تبدیل اعداد فارسی به انگلیسی.

    Args:
        text: متن با اعداد فارسی

    Returns:
        str: متن با اعداد انگلیسی
    """
    # جدول تبدیل اعداد فارسی به انگلیسی
    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }

    # جایگزینی اعداد
    for persian, english in persian_to_english.items():
        text = text.replace(persian, english)

    return text


def split_name(full_name: str) -> Tuple[str, str]:
    """
    جدا کردن نام و نام خانوادگی.

    Args:
        full_name: نام کامل

    Returns:
        Tuple[str, str]: نام و نام خانوادگی
    """
    parts = full_name.strip().split()

    if len(parts) == 1:
        return parts[0], ''

    first_name = parts[0]
    last_name = ' '.join(parts[1:])

    return first_name, last_name


def is_valid_national_code(code: str) -> bool:
    """
    بررسی صحت کد ملی ایرانی.

    Args:
        code: کد ملی

    Returns:
        bool: صحت کد ملی
    """
    # تبدیل اعداد فارسی به انگلیسی
    code = convert_persian_numbers_to_english(code)

    # حذف فاصله‌ها و خط تیره
    code = code.replace(' ', '').replace('-', '')

    # بررسی طول کد
    if len(code) != 10:
        return False

    # بررسی اینکه کد فقط شامل اعداد باشد
    if not code.isdigit():
        return False

    # بررسی اینکه همه ارقام یکسان نباشند
    if code == code[0] * 10:
        return False

    # محاسبه رقم کنترل
    check = int(code[9])
    s = sum(int(code[i]) * (10 - i) for i in range(9)) % 11

    return (s < 2 and check == s) or (s >= 2 and check == 11 - s)


def is_valid_mobile_number(mobile: str) -> bool:
    """
    بررسی صحت شماره موبایل ایرانی.

    Args:
        mobile: شماره موبایل

    Returns:
        bool: صحت شماره موبایل
    """
    # تبدیل اعداد فارسی به انگلیسی
    mobile = convert_persian_numbers_to_english(mobile)

    # حذف فاصله‌ها و خط تیره
    mobile = mobile.replace(' ', '').replace('-', '')

    # الگوی شماره موبایل ایرانی (شروع با 09 یا +989)
    pattern = r'^(?:0|98|\+98)9\d{9}$'

    return bool(re.match(pattern, mobile))


def format_mobile_number(mobile: str) -> str:
    """
    فرمت‌دهی شماره موبایل ایرانی.

    Args:
        mobile: شماره موبایل

    Returns:
        str: شماره موبایل فرمت شده (09XXXXXXXXX)
    """
    # تبدیل اعداد فارسی به انگلیسی
    mobile = convert_persian_numbers_to_english(mobile)

    # حذف فاصله‌ها و خط تیره
    mobile = mobile.replace(' ', '').replace('-', '')

    # تطبیق با الگوی شماره موبایل ایرانی
    if re.match(r'^(?:0|98|\+98)9\d{9}$', mobile):
        # استخراج 10 رقم آخر
        last_10_digits = mobile[-10:]

        # اضافه کردن پیشوند 0
        return f"09{last_10_digits[-9:]}"

    return mobile