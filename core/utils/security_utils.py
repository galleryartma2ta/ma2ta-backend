# core/utils/security_utils.py

import os
import uuid
import hashlib
import hmac
import base64
import secrets
import string
from typing import Union, Optional, Dict, Any
from django.conf import settings
from django.utils.crypto import get_random_string, constant_time_compare
from cryptography.fernet import Fernet


def generate_random_token(length: int = 32) -> str:
    """
    تولید توکن تصادفی امن.

    Args:
        length: طول توکن

    Returns:
        str: توکن تصادفی
    """
    return secrets.token_urlsafe(length)


def generate_hash(data: Union[str, bytes], salt: Optional[str] = None) -> str:
    """
    تولید هش SHA-256 از داده.

    Args:
        data: داده برای هش کردن
        salt: نمک برای افزودن امنیت (اختیاری)

    Returns:
        str: هش تولید شده
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    if salt is None:
        salt = getattr(settings, 'SECRET_KEY', '')

    if isinstance(salt, str):
        salt = salt.encode('utf-8')

    # ایجاد هش HMAC با SHA-256
    signature = hmac.new(salt, data, hashlib.sha256).hexdigest()
    return signature


def verify_hash(data: Union[str, bytes], hash_value: str,
                salt: Optional[str] = None) -> bool:
    """
    بررسی تطابق داده با هش.

    Args:
        data: داده برای بررسی
        hash_value: هش برای مقایسه
        salt: نمک استفاده شده در هش (اختیاری)

    Returns:
        bool: True اگر هش مطابقت داشته باشد، در غیر این صورت False
    """
    generated_hash = generate_hash(data, salt)
    return constant_time_compare(generated_hash, hash_value)


def get_encryption_key() -> bytes:
    """
    دریافت کلید رمزنگاری از تنظیمات یا تولید یک کلید جدید.

    Returns:
        bytes: کلید رمزنگاری
    """
    # دریافت کلید از تنظیمات
    key = getattr(settings, 'ENCRYPTION_KEY', None)

    if not key:
        # استفاده از SECRET_KEY به عنوان سید برای تولید کلید
        seed = settings.SECRET_KEY.encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())

    # تبدیل به bytes اگر رشته است
    if isinstance(key, str):
        key = key.encode()

    return key


def encrypt_data(data: Union[str, bytes, Dict, Any]) -> str:
    """
    رمزنگاری داده با Fernet (رمزنگاری متقارن).

    Args:
        data: داده برای رمزنگاری

    Returns:
        str: داده رمزنگاری شده (به صورت رشته)
    """
    import json

    # تبدیل داده به JSON اگر دیکشنری یا شیء باشد
    if not isinstance(data, (str, bytes)):
        data = json.dumps(data)

    # تبدیل به bytes اگر رشته است
    if isinstance(data, str):
        data = data.encode('utf-8')

    # دریافت کلید رمزنگاری
    key = get_encryption_key()

    # رمزنگاری داده
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data)

    # برگرداندن نتیجه به صورت رشته
    return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')


def decrypt_data(encrypted_data: str, as_json: bool = False) -> Union[str, Dict, Any]:
    """
    رمزگشایی داده رمزنگاری شده با Fernet.

    Args:
        encrypted_data: داده رمزنگاری شده
        as_json: آیا نتیجه به صورت JSON تفسیر شود

    Returns:
        Union[str, Dict, Any]: داده رمزگشایی شده
    """
    import json

    # تبدیل رشته به bytes
    encrypted_data = base64.urlsafe_b64decode(encrypted_data)

    # دریافت کلید رمزنگاری
    key = get_encryption_key()

    # رمزگشایی داده
    cipher_suite = Fernet(key)
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode('utf-8')

    # تبدیل به JSON اگر درخواست شده باشد
    if as_json:
        return json.loads(decrypted_data)

    return decrypted_data


def generate_secure_password(length: int = 12) -> str:
    """
    تولید رمز عبور امن تصادفی.

    Args:
        length: طول رمز عبور

    Returns:
        str: رمز عبور تولید شده
    """
    # اطمینان از استفاده از همه گروه‌های کاراکتر
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation

    while True:
        # تولید رمز عبور
        password = ''.join(secrets.choice(chars) for _ in range(length))

        # بررسی معیارهای امنیتی
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            break

    return password


def generate_unique_id(prefix: str = '', length: int = 16) -> str:
    """
    تولید شناسه یکتا.

    Args:
        prefix: پیشوند شناسه
        length: طول شناسه (بدون پیشوند)

    Returns:
        str: شناسه یکتا
    """
    unique_id = uuid.uuid4().hex[:length]

    if prefix:
        return f"{prefix}_{unique_id}"

    return unique_id


def mask_sensitive_data(data: Dict[str, Any],
                        sensitive_fields: Optional[list] = None) -> Dict[str, Any]:
    """
    مخفی کردن اطلاعات حساس در دیکشنری.

    Args:
        data: دیکشنری داده‌ها
        sensitive_fields: لیست فیلدهای حساس

    Returns:
        Dict[str, Any]: دیکشنری با فیلدهای حساس مخفی شده
    """
    if sensitive_fields is None:
        sensitive_fields = [
            'password', 'token', 'access_token', 'refresh_token',
            'card_number', 'cvv', 'key', 'secret', 'otp'
        ]

    result = {}

    for key, value in data.items():
        if key.lower() in [field.lower() for field in sensitive_fields]:
            # مخفی کردن داده حساس
            if isinstance(value, str):
                if len(value) > 4:
                    result[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    result[key] = '****'
            else:
                result[key] = '****'
        elif isinstance(value, dict):
            # بررسی بازگشتی برای دیکشنری‌های تودرتو
            result[key] = mask_sensitive_data(value, sensitive_fields)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # بررسی بازگشتی برای لیست‌های دیکشنری
            result[key] = [mask_sensitive_data(item, sensitive_fields) if isinstance(item, dict) else item for item in
                           value]
        else:
            result[key] = value

    return result