# core/services/sms_service.py

import logging
import random
import string
import json
import requests
from typing import Dict, List, Optional, Union
from django.conf import settings
from core.exceptions import ServiceUnavailable

logger = logging.getLogger('sms')


class SMSService:
    """
    سرویس ارسال پیامک.
    این کلاس با ارائه‌دهندگان مختلف پیامک در ایران کار می‌کند.
    """

    def __init__(self):
        """مقداردهی اولیه سرویس پیامک"""
        self.provider = getattr(settings, 'SMS_PROVIDER', 'kavenegar')
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.sender = getattr(settings, 'SMS_SENDER', '')
        self.debug = getattr(settings, 'SMS_DEBUG', settings.DEBUG)

        # پیکربندی‌های مخصوص هر ارائه‌دهنده
        self.provider_configs = {
            'kavenegar': {
                'url': 'https://api.kavenegar.com/v1/{}/sms/send.json'.format(self.api_key),
                'bulk_url': 'https://api.kavenegar.com/v1/{}/sms/sendarray.json'.format(self.api_key),
                'verification_url': 'https://api.kavenegar.com/v1/{}/verify/lookup.json'.format(self.api_key),
            },
            'melipayamak': {
                'url': 'https://rest.payamak-panel.com/api/SendSMS/SendSMS',
                'bulk_url': 'https://rest.payamak-panel.com/api/SendSMS/SendSMS',
                'username': getattr(settings, 'SMS_USERNAME', ''),
                'password': getattr(settings, 'SMS_PASSWORD', ''),
            },
            'ghasedak': {
                'url': 'https://api.ghasedak.me/v2/sms/send/simple',
                'bulk_url': 'https://api.ghasedak.me/v2/sms/send/bulk',
                'verification_url': 'https://api.ghasedak.me/v2/verification/send',
            }
        }

        # ارائه‌دهنده جایگزین برای زمانی که ارائه‌دهنده اصلی در دسترس نیست
        self.fallback_provider = getattr(settings, 'SMS_FALLBACK_PROVIDER', None)

    def send_sms(self,
                 to: Union[str, List[str]],
                 message: str,
                 sender: Optional[str] = None,
                 fail_silently: bool = False) -> Dict:
        """
        ارسال پیامک به یک یا چند شماره.

        Args:
            to: شماره یا لیستی از شماره‌های دریافت‌کننده
            message: متن پیامک
            sender: شماره فرستنده (اختیاری، پیش‌فرض از تنظیمات)
            fail_silently: اگر True باشد، خطاها را نادیده می‌گیرد

        Returns:
            Dict: نتیجه ارسال پیامک
        """
        if not to:
            logger.warning("تلاش برای ارسال پیامک بدون شماره دریافت‌کننده")
            return {'success': False, 'message': 'شماره دریافت‌کننده ارائه نشده است'}

        # تبدیل تک شماره به لیست
        if isinstance(to, str):
            to = [to]

        # تنظیم شماره فرستنده
        if not sender:
            sender = self.sender

        # در حالت دیباگ، پیامک ارسال نمی‌شود
        if self.debug:
            logger.debug(f"حالت دیباگ: پیامک به {', '.join(to)} ارسال می‌شد: {message}")
            return {'success': True, 'message': 'پیامک در حالت دیباگ ارسال نشد', 'debug': True}

        # بیش از یک گیرنده؟ از ارسال انبوه استفاده کنید
        if len(to) > 1:
            return self._send_bulk_sms(to, message, sender, fail_silently)

        # ارسال به یک گیرنده
        return self._send_single_sms(to[0], message, sender, fail_silently)

    def _send_single_sms(self, to: str, message: str, sender: str, fail_silently: bool) -> Dict:
        """ارسال پیامک به یک شماره"""
        try:
            if self.provider == 'kavenegar':
                return self._send_kavenegar_sms(to, message, sender)
            elif self.provider == 'melipayamak':
                return self._send_melipayamak_sms(to, message, sender)
            elif self.provider == 'ghasedak':
                return self._send_ghasedak_sms(to, message, sender)
            else:
                logger.error(f"ارائه‌دهنده پیامک ناشناخته: {self.provider}")
                raise ValueError(f"ارائه‌دهنده پیامک ناشناخته: {self.provider}")
        except Exception as e:
            logger.error(f"خطا در ارسال پیامک به {to}: {str(e)}")

            # تلاش مجدد با ارائه‌دهنده جایگزین
            if self.fallback_provider:
                return self._send_with_fallback(to, message, sender)

            if not fail_silently:
                raise

            return {'success': False, 'message': str(e)}

    def _send_bulk_sms(self, to: List[str], message: str, sender: str, fail_silently: bool) -> Dict:
        """ارسال پیامک به چند شماره"""
        try:
            if self.provider == 'kavenegar':
                return self._send_kavenegar_bulk_sms(to, message, sender)
            elif self.provider == 'melipayamak':
                return self._send_melipayamak_bulk_sms(to, message, sender)
            elif self.provider == 'ghasedak':
                return self._send_ghasedak_bulk_sms(to, message, sender)
            else:
                logger.error(f"ارائه‌دهنده پیامک ناشناخته: {self.provider}")
                raise ValueError(f"ارائه‌دهنده پیامک ناشناخته: {self.provider}")
        except Exception as e:
            logger.error(f"خطا در ارسال پیامک انبوه: {str(e)}")

            if not fail_silently:
                raise

            return {'success': False, 'message': str(e)}

    def _send_with_fallback(self, to: str, message: str, sender: str) -> Dict:
        """تلاش مجدد با ارائه‌دهنده جایگزین"""
        try:
            logger.info(f"تلاش برای ارسال پیامک با ارائه‌دهنده جایگزین {self.fallback_provider}")

            # ذخیره ارائه‌دهنده اصلی
            original_provider = self.provider

            # تغییر به ارائه‌دهنده جایگزین
            self.provider = self.fallback_provider

            # ارسال پیامک با ارائه‌دهنده جایگزین
            result = self._send_single_sms(to, message, sender, True)

            # بازگرداندن ارائه‌دهنده اصلی
            self.provider = original_provider

            return result
        except Exception as e:
            logger.error(f"خطا در ارسال پیامک با ارائه‌دهنده جایگزین: {str(e)}")
            return {'success': False, 'message': str(e)}

    def _send_kavenegar_sms(self, to: str, message: str, sender: str) -> Dict:
        """ارسال پیامک با کاوه‌نگار"""
        try:
            url = self.provider_configs['kavenegar']['url']
            payload = {
                'receptor': to,
                'message': message,
                'sender': sender,
            }

            response = requests.post(url, data=payload)
            data = response.json()

            if response.status_code == 200:
                if data.get('return', {}).get('status') == 200:
                    logger.info(f"پیامک با موفقیت به {to} ارسال شد")
                    return {'success': True, 'message': 'پیامک با موفقیت ارسال شد', 'data': data}
                else:
                    error = data.get('return', {}).get('message', 'خطای ناشناخته')
                    logger.error(f"خطا در ارسال پیامک با کاوه‌نگار: {error}")
                    return {'success': False, 'message': error, 'data': data}
            else:
                logger.error(f"خطا در ارسال پیامک با کاوه‌نگار: کد {response.status_code}")
                return {'success': False, 'message': f'خطای HTTP: {response.status_code}', 'data': data}
        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با سرویس کاوه‌نگار: {str(e)}")
            raise ServiceUnavailable(f"خطا در ارتباط با سرویس پیامک: {str(e)}")

    def _send_kavenegar_bulk_sms(self, to: List[str], message: str, sender: str) -> Dict:
        """ارسال پیامک انبوه با کاوه‌نگار"""
        try:
            url = self.provider_configs['kavenegar']['bulk_url']

            # تبدیل آرایه‌ای از گیرندگان به فرمت مورد نیاز کاوه‌نگار
            receptors = ",".join(to)

            payload = {
                'receptor': receptors,
                'message': message,
                'sender': sender,
            }

            response = requests.post(url, data=payload)
            data = response.json()

            if response.status_code == 200:
                if data.get('return', {}).get('status') == 200:
                    logger.info(f"پیامک انبوه با موفقیت به {len(to)} شماره ارسال شد")
                    return {'success': True, 'message': 'پیامک انبوه با موفقیت ارسال شد', 'data': data}
                else:
                    error = data.get('return', {}).get('message', 'خطای ناشناخته')
                    logger.error(f"خطا در ارسال پیامک انبوه با کاوه‌نگار: {error}")
                    return {'success': False, 'message': error, 'data': data}
            else:
                logger.error(f"خطا در ارسال پیامک انبوه با کاوه‌نگار: کد {response.status_code}")
                return {'success': False, 'message': f'خطای HTTP: {response.status_code}', 'data': data}
        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با سرویس کاوه‌نگار: {str(e)}")
            raise ServiceUnavailable(f"خطا در ارتباط با سرویس پیامک: {str(e)}")

    def _send_melipayamak_sms(self, to: str, message: str, sender: str) -> Dict:
        """ارسال پیامک با ملی پیامک"""
        try:
            url = self.provider_configs['melipayamak']['url']
            username = self.provider_configs['melipayamak']['username']
            password = self.provider_configs['melipayamak']['password']

            payload = {
                'username': username,
                'password': password,
                'to': to,
                'from': sender,
                'text': message,
            }

            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            data = response.json()

            if response.status_code == 200:
                if data.get('Value', -1) > 0:
                    logger.info(f"پیامک با موفقیت به {to} ارسال شد")
                    return {'success': True, 'message': 'پیامک با موفقیت ارسال شد', 'data': data}
                else:
                    error = data.get('RetStatus', 'خطای ناشناخته')
                    logger.error(f"خطا در ارسال پیامک با ملی پیامک: {error}")
                    return {'success': False, 'message': error, 'data': data}
            else:
                logger.error(f"خطا در ارسال پیامک با ملی پیامک: کد {response.status_code}")
                return {'success': False, 'message': f'خطای HTTP: {response.status_code}', 'data': data}
        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با سرویس ملی پیامک: {str(e)}")
            raise ServiceUnavailable(f"خطا در ارتباط با سرویس پیامک: {str(e)}")

    def _send_melipayamak_bulk_sms(self, to: List[str], message: str, sender: str) -> Dict:
        """ارسال پیامک انبوه با ملی پیامک"""
        # ملی پیامک API جداگانه برای ارسال انبوه ندارد، بنابراین پیامک‌ها را تک به تک ارسال می‌کنیم
        results = []
        success_count = 0

        for recipient in to:
            result = self._send_melipayamak_sms(recipient, message, sender)
            results.append(result)
            if result['success']:
                success_count += 1

        if success_count == len(to):
            logger.info(f"پیامک انبوه با موفقیت به {success_count} شماره از {len(to)} ارسال شد")
            return {'success': True, 'message': 'پیامک انبوه با موفقیت ارسال شد', 'results': results}
        else:
            logger.warning(f"پیامک انبوه با مشکل مواجه شد: {success_count} موفق از {len(to)}")
            return {'success': False, 'message': f'ارسال ناموفق به برخی شماره‌ها', 'results': results}

    def _send_ghasedak_sms(self, to: str, message: str, sender: str) -> Dict:
        """ارسال پیامک با قاصدک"""
        try:
            url = self.provider_configs['ghasedak']['url']

            payload = {
                'receptor': to,
                'message': message,
                'linenumber': sender,
            }

            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(url, data=payload, headers=headers)
            data = response.json()

            if response.status_code == 200:
                if data.get('result', {}).get('code') == 200:
                    logger.info(f"پیامک با موفقیت به {to} ارسال شد")
                    return {'success': True, 'message': 'پیامک با موفقیت ارسال شد', 'data': data}
                else:
                    error = data.get('result', {}).get('message', 'خطای ناشناخته')
                    logger.error(f"خطا در ارسال پیامک با قاصدک: {error}")
                    return {'success': False, 'message': error, 'data': data}
            else:
                logger.error(f"خطا در ارسال پیامک با قاصدک: کد {response.status_code}")
                return {'success': False, 'message': f'خطای HTTP: {response.status_code}', 'data': data}
        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با سرویس قاصدک: {str(e)}")
            raise ServiceUnavailable(f"خطا در ارتباط با سرویس پیامک: {str(e)}")

    def _send_ghasedak_bulk_sms(self, to: List[str], message: str, sender: str) -> Dict:
        """ارسال پیامک انبوه با قاصدک"""
        try:
            url = self.provider_configs['ghasedak']['bulk_url']

            # تبدیل آرایه‌ای از گیرندگان به فرمت مورد نیاز قاصدک
            receptors = ",".join(to)

            payload = {
                'receptor': receptors,
                'message': message,
                'linenumber': sender,
            }

            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(url, data=payload, headers=headers)
            data = response.json()

            if response.status_code == 200:
                if data.get('result', {}).get('code') == 200:
                    logger.info(f"پیامک انبوه با موفقیت به {len(to)} شماره ارسال شد")
                    return {'success': True, 'message': 'پیامک انبوه با موفقیت ارسال شد', 'data': data}
                else:
                    error = data.get('result', {}).get('message', 'خطای ناشناخته')
                    logger.error(f"خطا در ارسال پیامک انبوه با قاصدک: {error}")
                    return {'success': False, 'message': error, 'data': data}
            else:
                logger.error(f"خطا در ارسال پیامک انبوه با قاصدک: کد {response.status_code}")
                return {'success': False, 'message': f'خطای HTTP: {response.status_code}', 'data': data}
        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با سرویس قاصدک: {str(e)}")
            raise ServiceUnavailable(f"خطا در ارتباط با سرویس پیامک: {str(e)}")

    def send_verification_code(self, phone_number: str, code: Optional[str] = None,
                               fail_silently: bool = False) -> Dict:
        """
        ارسال کد تأیید به شماره تلفن.

        Args:
            phone_number: شماره تلفن دریافت‌کننده
            code: کد تأیید (اختیاری، اگر ارائه نشود، یک کد تصادفی تولید می‌شود)
            fail_silently: اگر True باشد، خطاها را نادیده می‌گیرد

        Returns:
            Dict: نتیجه ارسال کد تأیید
        """
        # تولید کد تأیید در صورت عدم ارائه
        if not code:
            code = self.generate_verification_code()

        # در حالت دیباگ، پیامک ارسال نمی‌شود
        if self.debug:
            logger.debug(f"حالت دیباگ: کد تأیید {code} به {phone_number} ارسال می‌شد")
            return {'success': True, 'message': 'کد تأیید در حالت دیباگ ارسال نشد', 'code': code, 'debug': True}

        try:
            # ارائه‌دهنده‌های مختلف روش‌های متفاوتی برای ارسال کد تأیید دارند
            if self.provider == 'kavenegar':
                return self._send_kavenegar_verification(phone_number, code)
            elif self.provider == 'ghasedak':
                return self._send_ghasedak_verification(phone_number, code)
            else:
                # برای سایر ارائه‌دهندگان، از پیامک معمولی استفاده می‌کنیم
                message = f"کد تأیید شما در Ma2tA: {code}"
                return self.send_sms(phone_number, message, fail_silently=fail_silently)
        except Exception as e:
            logger.error(f"خطا در ارسال کد تأیید به {phone_number}: {str(e)}")

            if not fail_silently:
                raise

            return {'success': False, 'message': str(e), 'code': code}

    def _send_kavenegar_verification(self, phone_number: str, code: str) -> Dict:
        """ارسال کد تأیید با کاوه‌نگار"""
        try:
            url = self.provider_configs['kavenegar']['verification_url']

            payload = {
                'receptor': phone_number,
                'token': code,
                'template': 'ma2ta-verify',  # نام قالب در کاوه‌نگار
            }

            response = requests.post(url, data=payload)
            data = response.json()

            if response.status_code == 200:
                if data.get('return', {}).get('status') == 200:
                    logger.info(f"کد تأیید با موفقیت به {phone_number} ارسال شد")
                    return {'success': True, 'message': 'کد تأیید با موفقیت ارسال شد', 'code': code, 'data': data}
                else:
                    error = data.get('return', {}).get('message', 'خطای ناشناخته')
                    logger.error(f"خطا در ارسال کد تأیید با کاوه‌نگار: {error}")
                    return {'success': False, 'message': error, 'code': code, 'data': data}
            else:
                logger.error(f"خطا در ارسال کد تأیید با کاوه‌نگار: کد {response.status_code}")
                return {'success': False, 'message': f'خطای HTTP: {response.status_code}', 'code': code, 'data': data}
        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با سرویس کاوه‌نگار: {str(e)}")
            raise ServiceUnavailable(f"خطا در ارتباط با سرویس پیامک: {str(e)}")

    def _send_ghasedak_verification(self, phone_number: str, code: str) -> Dict:
        """ارسال کد تأیید با قاصدک"""
        try:
            url = self.provider_configs['ghasedak']['verification_url']

            payload = {
                'receptor': phone_number,
                'type': '1',  # نوع پیام تأیید
                'template': 'ma2ta',  # نام قالب در قاصدک
                'param1': code,
            }

            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(url, data=payload, headers=headers)
            data = response.json()

            if response.status_code == 200:
                if data.get('result', {}).get('code') == 200:
                    logger.info(f"کد تأیید با موفقیت به {phone_number} ارسال شد")
                    return {'success': True, 'message': 'کد تأیید با موفقیت ارسال شد', 'code': code, 'data': data}
                else:
                    error = data.get('result', {}).get('message', 'خطای ناشناخته')
                    logger.error(f"خطا در ارسال کد تأیید با قاصدک: {error}")
                    return {'success': False, 'message': error, 'code': code, 'data': data}
            else:
                logger.error(f"خطا در ارسال کد تأیید با قاصدک: کد {response.status_code}")
                return {'success': False, 'message': f'خطای HTTP: {response.status_code}', 'code': code, 'data': data}
        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با سرویس قاصدک: {str(e)}")
            raise ServiceUnavailable(f"خطا در ارتباط با سرویس پیامک: {str(e)}")

    def generate_verification_code(self, length: int = 5) -> str:
        """
        تولید کد تأیید تصادفی.

        Args:
            length: طول کد تأیید (پیش‌فرض: 5)

        Returns:
            str: کد تأیید تولید شده
        """
        return ''.join(random.choices(string.digits, k=length))

    # روش‌های کاربردی برای انواع خاص پیامک‌ها

    def send_order_status_sms(self, phone_number: str, order_number: str, status: str,
                              fail_silently: bool = False) -> Dict:
        """ارسال پیامک وضعیت سفارش"""
        status_map = {
            'pending': 'در انتظار پرداخت',
            'processing': 'در حال پردازش',
            'shipped': 'ارسال شده',
            'delivered': 'تحویل داده شده',
            'canceled': 'لغو شده',
        }

        status_text = status_map.get(status, status)
        message = f"وضعیت سفارش #{order_number} در Ma2tA به {status_text} تغییر کرد."

        return self.send_sms(phone_number, message, fail_silently=fail_silently)

    def send_payment_confirmation_sms(self, phone_number: str, order_number: str, amount: str,
                                      fail_silently: bool = False) -> Dict:
        """ارسال پیامک تأیید پرداخت"""
        message = f"پرداخت شما به مبلغ {amount} تومان برای سفارش #{order_number} در Ma2tA با موفقیت انجام شد."

        return self.send_sms(phone_number, message, fail_silently=fail_silently)