# core/services/payment_gateway.py

import logging
import uuid
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Optional
from django.conf import settings
from django.urls import reverse
from core.exceptions import (
    PaymentGatewayError,
    PaymentExpiredError,
    PaymentVerificationError,
    GatewayConfigurationError
)

logger = logging.getLogger('payment')


class BasePaymentGateway(ABC):
    """
    کلاس پایه برای درگاه‌های پرداخت.
    همه درگاه‌های پرداخت باید از این کلاس ارث‌بری کنند.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        مقداردهی اولیه درگاه پرداخت.

        Args:
            config: تنظیمات اختیاری برای درگاه
        """
        self.config = config or {}
        self.merchant_id = self.config.get('merchant_id', '')
        self.callback_url = self.config.get('callback_url', '')
        self.debug = self.config.get('debug', settings.DEBUG)

    @abstractmethod
    def request_payment(self, amount: int, description: str, email: str = '', mobile: str = '',
                        order_id: Optional[str] = None) -> Dict:
        """
        درخواست پرداخت و دریافت لینک پرداخت.

        Args:
            amount: مبلغ به تومان
            description: توضیحات پرداخت
            email: ایمیل مشتری (اختیاری)
            mobile: شماره موبایل مشتری (اختیاری)
            order_id: شناسه سفارش (اختیاری)

        Returns:
            Dict: اطلاعات پرداخت شامل لینک هدایت به درگاه
        """
        pass

    @abstractmethod
    def verify_payment(self, authority: str, amount: int) -> Dict:
        """
        تأیید پرداخت پس از بازگشت از درگاه.

        Args:
            authority: کد پیگیری پرداخت
            amount: مبلغ پرداخت به تومان

        Returns:
            Dict: نتیجه تأیید پرداخت
        """
        pass

    def get_callback_url(self, order_id: Optional[str] = None) -> str:
        """
        دریافت آدرس برگشت از درگاه پرداخت.

        Args:
            order_id: شناسه سفارش (اختیاری)

        Returns:
            str: آدرس کامل برگشت از درگاه
        """
        if self.callback_url:
            # اگر order_id ارائه شده، به callback_url اضافه می‌کنیم
            if order_id and '?' not in self.callback_url:
                return f"{self.callback_url}?order_id={order_id}"
            return self.callback_url

        # استفاده از آدرس پیش‌فرض
        site_url = settings.SITE_URL
        callback_path = reverse('payment:callback')

        # اگر order_id ارائه شده، به callback_url اضافه می‌کنیم
        if order_id:
            return f"{site_url}{callback_path}?order_id={order_id}"

        return f"{site_url}{callback_path}"

    def handle_http_error(self, response: requests.Response) -> None:
        """
        مدیریت خطاهای HTTP در تعامل با API درگاه پرداخت.

        Args:
            response: پاسخ HTTP

        Raises:
            PaymentGatewayError: خطا در ارتباط با درگاه پرداخت
        """
        try:
            error_data = response.json()
            error_message = error_data.get('message', 'خطای ناشناخته')
        except (ValueError, KeyError):
            error_message = f"خطای HTTP: {response.status_code}"

        logger.error(f"خطا در ارتباط با درگاه پرداخت: {error_message}")
        raise PaymentGatewayError(gateway_name=self.__class__.__name__, gateway_error=error_message)


class ZarinpalGateway(BasePaymentGateway):
    """
    درگاه پرداخت زرین‌پال.
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

        # تنظیم آدرس‌های API بر اساس حالت (sandbox یا production)
        self.is_sandbox = self.config.get('sandbox', self.debug)

        if self.is_sandbox:
            # محیط تست
            self.request_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'
            self.payment_url = 'https://sandbox.zarinpal.com/pg/StartPay/'
            self.verify_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json'
        else:
            # محیط تولید
            self.request_url = 'https://api.zarinpal.com/pg/v4/payment/request.json'
            self.payment_url = 'https://www.zarinpal.com/pg/StartPay/'
            self.verify_url = 'https://api.zarinpal.com/pg/v4/payment/verify.json'

    def request_payment(self, amount: int, description: str, email: str = '', mobile: str = '',
                        order_id: Optional[str] = None) -> Dict:
        """
        درخواست پرداخت با زرین‌پال.

        Args:
            amount: مبلغ به تومان
            description: توضیحات پرداخت
            email: ایمیل مشتری (اختیاری)
            mobile: شماره موبایل مشتری (اختیاری)
            order_id: شناسه سفارش (اختیاری)

        Returns:
            Dict: اطلاعات پرداخت شامل لینک هدایت به درگاه
        """
        if not self.merchant_id:
            raise GatewayConfigurationError("کد مرچنت زرین‌پال تنظیم نشده است")

        # تبدیل به ریال برای زرین‌پال
        amount_rials = amount * 10

        # دریافت آدرس برگشت
        callback_url = self.get_callback_url(order_id)

        # ساخت داده‌های درخواست
        payload = {
            'MerchantID': self.merchant_id,
            'Amount': amount_rials,
            'Description': description,
            'CallbackURL': callback_url,
        }

        # افزودن اطلاعات اختیاری
        if email:
            payload['Email'] = email
        if mobile:
            payload['Mobile'] = mobile

        try:
            # ارسال درخواست به زرین‌پال
            logger.info(f"درخواست پرداخت به زرین‌پال: {amount} تومان")
            response = requests.post(self.request_url, json=payload)

            # بررسی پاسخ
            if response.status_code == 200:
                data = response.json()

                # در محیط تست، ساختار پاسخ متفاوت است
                if self.is_sandbox:
                    status = data.get('Status', -99)
                    authority = data.get('Authority', '')
                else:
                    status = data.get('data', {}).get('code', -99)
                    authority = data.get('data', {}).get('authority', '')

                if status == 100:
                    # ساخت لینک پرداخت
                    payment_url = f"{self.payment_url}{authority}"

                    logger.info(f"درخواست پرداخت با موفقیت ایجاد شد: {authority}")
                    return {
                        'success': True,
                        'payment_url': payment_url,
                        'authority': authority,
                        'gateway': 'zarinpal',
                        'amount': amount,
                    }
                else:
                    error_code = status
                    error_message = self._get_error_message(error_code)
                    logger.error(f"خطا در درخواست پرداخت زرین‌پال: {error_code} - {error_message}")
                    return {
                        'success': False,
                        'error_code': error_code,
                        'message': error_message,
                    }
            else:
                self.handle_http_error(response)

        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با زرین‌پال: {str(e)}")
            raise PaymentGatewayError(gateway_name='ZarinPal', gateway_error=str(e))

    def verify_payment(self, authority: str, amount: int) -> Dict:
        """
        تأیید پرداخت زرین‌پال.

        Args:
            authority: کد پیگیری پرداخت
            amount: مبلغ پرداخت به تومان

        Returns:
            Dict: نتیجه تأیید پرداخت
        """
        if not self.merchant_id:
            raise GatewayConfigurationError("کد مرچنت زرین‌پال تنظیم نشده است")

        # تبدیل به ریال برای زرین‌پال
        amount_rials = amount * 10

        # ساخت داده‌های درخواست
        payload = {
            'MerchantID': self.merchant_id,
            'Authority': authority,
            'Amount': amount_rials,
        }

        try:
            # ارسال درخواست تأیید به زرین‌پال
            logger.info(f"درخواست تأیید پرداخت به زرین‌پال: {authority}")
            response = requests.post(self.verify_url, json=payload)

            # بررسی پاسخ
            if response.status_code == 200:
                data = response.json()

                # در محیط تست، ساختار پاسخ متفاوت است
                if self.is_sandbox:
                    status = data.get('Status', -99)
                    ref_id = data.get('RefID', '')
                else:
                    status = data.get('data', {}).get('code', -99)
                    ref_id = data.get('data', {}).get('ref_id', '')

                if status == 100 or status == 101:
                    # پرداخت موفق
                    logger.info(f"پرداخت با موفقیت تأیید شد: {ref_id}")
                    return {
                        'success': True,
                        'reference_id': ref_id,
                        'authority': authority,
                        'gateway': 'zarinpal',
                        'amount': amount,
                    }
                else:
                    # پرداخت ناموفق
                    error_code = status
                    error_message = self._get_error_message(error_code)
                    logger.error(f"خطا در تأیید پرداخت زرین‌پال: {error_code} - {error_message}")

                    # بررسی خطای منقضی شدن پرداخت
                    if error_code == -2:
                        raise PaymentExpiredError("پرداخت منقضی شده است")

                    raise PaymentVerificationError(error_message)
            else:
                self.handle_http_error(response)

        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با زرین‌پال: {str(e)}")
            raise PaymentGatewayError(gateway_name='ZarinPal', gateway_error=str(e))

    def _get_error_message(self, error_code: int) -> str:
        """
        دریافت پیام خطا بر اساس کد خطای زرین‌پال.

        Args:
            error_code: کد خطا

        Returns:
            str: پیام خطا
        """
        error_messages = {
            -1: "اطلاعات ارسال شده ناقص است",
            -2: "IP یا مرچنت کد پذیرنده صحیح نیست",
            -3: "با توجه به محدودیت‌های شاپرک، امکان پرداخت با رقم درخواست شده میسر نیست",
            -4: "سطح تأیید پذیرنده پایین‌تر از سطح نقره‌ای است",
            -11: "درخواست مورد نظر یافت نشد",
            -12: "امکان ویرایش درخواست میسر نیست",
            -21: "هیچ نوع عملیات مالی برای این تراکنش یافت نشد",
            -22: "تراکنش ناموفق بوده است",
            -33: "رقم تراکنش با رقم پرداخت شده مطابقت ندارد",
            -34: "سقف تقسیم تراکنش از لحاظ تعداد یا رقم عبور نموده است",
            -40: "اجازه دسترسی به متد مربوطه وجود ندارد",
            -41: "اطلاعات ارسال شده مربوط به AdditionalData غیرمعتبر است",
            -42: "مدت زمان معتبر طول عمر شناسه پرداخت باید بین ۳۰ دقیقه تا ۴۵ روز باشد",
            -54: "درخواست مورد نظر آرشیو شده است",
            100: "عملیات موفق",
            101: "عملیات موفق - تراکنش قبلاً انجام شده است",
        }

        return error_messages.get(error_code, f"خطای ناشناخته: {error_code}")


class PayPingGateway(BasePaymentGateway):
    """
    درگاه پرداخت پی‌پینگ.
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

        # آدرس‌های API پی‌پینگ
        self.request_url = 'https://api.payping.ir/v2/pay'
        self.verify_url = 'https://api.payping.ir/v2/pay/verify'
        self.payment_url = 'https://api.payping.ir/v2/pay/gotoipg/'

    def request_payment(self, amount: int, description: str, email: str = '', mobile: str = '',
                        order_id: Optional[str] = None) -> Dict:
        """
        درخواست پرداخت با پی‌پینگ.

        Args:
            amount: مبلغ به تومان
            description: توضیحات پرداخت
            email: ایمیل مشتری (اختیاری)
            mobile: شماره موبایل مشتری (اختیاری)
            order_id: شناسه سفارش (اختیاری)

        Returns:
            Dict: اطلاعات پرداخت شامل لینک هدایت به درگاه
        """
        if not self.merchant_id:
            raise GatewayConfigurationError("توکن پی‌پینگ تنظیم نشده است")

        # دریافت آدرس برگشت
        callback_url = self.get_callback_url(order_id)

        # ساخت شناسه پرداخت
        client_reference_id = order_id or str(uuid.uuid4())

        # ساخت داده‌های درخواست
        payload = {
            'amount': amount,
            'returnUrl': callback_url,
            'description': description,
            'clientRefId': client_reference_id,
        }

        # افزودن اطلاعات اختیاری
        if email:
            payload['payerIdentity'] = email
        if mobile:
            payload['payerName'] = mobile

        # ساخت هدرهای درخواست
        headers = {
            'Authorization': f'Bearer {self.merchant_id}',
            'Content-Type': 'application/json',
        }

        try:
            # ارسال درخواست به پی‌پینگ
            logger.info(f"درخواست پرداخت به پی‌پینگ: {amount} تومان")
            response = requests.post(self.request_url, json=payload, headers=headers)

            # بررسی پاسخ
            if response.status_code == 200:
                data = response.json()
                code = data.get('code')

                # ساخت لینک پرداخت
                payment_url = f"{self.payment_url}{code}"

                logger.info(f"درخواست پرداخت با موفقیت ایجاد شد: {code}")
                return {
                    'success': True,
                    'payment_url': payment_url,
                    'authority': code,
                    'gateway': 'payping',
                    'amount': amount,
                    'client_reference_id': client_reference_id,
                }
            else:
                self.handle_http_error(response)

        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با پی‌پینگ: {str(e)}")
            raise PaymentGatewayError(gateway_name='PayPing', gateway_error=str(e))

    def verify_payment(self, authority: str, amount: int) -> Dict:
        """
        تأیید پرداخت پی‌پینگ.

        Args:
            authority: کد پیگیری پرداخت
            amount: مبلغ پرداخت به تومان

        Returns:
            Dict: نتیجه تأیید پرداخت
        """
        if not self.merchant_id:
            raise GatewayConfigurationError("توکن پی‌پینگ تنظیم نشده است")

        # ساخت داده‌های درخواست
        payload = {
            'amount': amount,
            'refId': authority,
        }

        # ساخت هدرهای درخواست
        headers = {
            'Authorization': f'Bearer {self.merchant_id}',
            'Content-Type': 'application/json',
        }

        try:
            # ارسال درخواست تأیید به پی‌پینگ
            logger.info(f"درخواست تأیید پرداخت به پی‌پینگ: {authority}")
            response = requests.post(self.verify_url, json=payload, headers=headers)

            # بررسی پاسخ
            if response.status_code == 200:
                data = response.json()
                card_number = data.get('cardNumber', '')
                card_hashpan = data.get('cardHashPan', '')

                # پرداخت موفق
                logger.info(f"پرداخت با موفقیت تأیید شد: {authority}")
                return {
                    'success': True,
                    'reference_id': authority,
                    'authority': authority,
                    'gateway': 'payping',
                    'amount': amount,
                    'card_number': card_number,
                    'card_hashpan': card_hashpan,
                }
            else:
                error_message = 'تأیید پرداخت ناموفق بود'

                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and 'message' in error_data:
                        error_message = error_data['message']
                except (ValueError, KeyError):
                    pass

                logger.error(f"خطا در تأیید پرداخت پی‌پینگ: {error_message}")
                raise PaymentVerificationError(error_message)

        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با پی‌پینگ: {str(e)}")
            raise PaymentGatewayError(gateway_name='PayPing', gateway_error=str(e))


class IdPayGateway(BasePaymentGateway):
    """
    درگاه پرداخت آیدی پی.
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

        # آدرس‌های API آیدی پی
        self.request_url = 'https://api.idpay.ir/v1.1/payment'
        self.verify_url = 'https://api.idpay.ir/v1.1/payment/verify'

        # تنظیم حالت (sandbox یا normal)
        self.is_sandbox = self.config.get('sandbox', self.debug)

    def request_payment(self, amount: int, description: str, email: str = '', mobile: str = '',
                        order_id: Optional[str] = None) -> Dict:
        """
        درخواست پرداخت با آیدی پی.

        Args:
            amount: مبلغ به تومان
            description: توضیحات پرداخت
            email: ایمیل مشتری (اختیاری)
            mobile: شماره موبایل مشتری (اختیاری)
            order_id: شناسه سفارش (اختیاری)

        Returns:
            Dict: اطلاعات پرداخت شامل لینک هدایت به درگاه
        """
        if not self.merchant_id:
            raise GatewayConfigurationError("کلید API آیدی پی تنظیم نشده است")

        # دریافت آدرس برگشت
        callback_url = self.get_callback_url(order_id)

        # ساخت شناسه سفارش
        order_id = order_id or str(uuid.uuid4())

        # ساخت داده‌های درخواست
        payload = {
            'order_id': order_id,
            'amount': amount,
            'callback': callback_url,
            'desc': description,
        }

        # افزودن اطلاعات اختیاری
        if email:
            payload['mail'] = email
        if mobile:
            payload['phone'] = mobile

        # ساخت هدرهای درخواست
        headers = {
            'X-API-KEY': self.merchant_id,
            'X-SANDBOX': '1' if self.is_sandbox else '0',
            'Content-Type': 'application/json',
        }

        try:
            # ارسال درخواست به آیدی پی
            logger.info(f"درخواست پرداخت به آیدی پی: {amount} تومان")
            response = requests.post(self.request_url, json=payload, headers=headers)

            # بررسی پاسخ
            if response.status_code == 201:
                data = response.json()
                link = data.get('link', '')
                id_pay_id = data.get('id', '')

                logger.info(f"درخواست پرداخت با موفقیت ایجاد شد: {id_pay_id}")
                return {
                    'success': True,
                    'payment_url': link,
                    'authority': id_pay_id,
                    'gateway': 'idpay',
                    'amount': amount,
                    'order_id': order_id,
                }
            else:
                self.handle_http_error(response)

        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با آیدی پی: {str(e)}")
            raise PaymentGatewayError(gateway_name='IdPay', gateway_error=str(e))

    def verify_payment(self, authority: str, amount: int) -> Dict:
        """
        تأیید پرداخت آیدی پی.

        Args:
            authority: کد پیگیری پرداخت
            amount: مبلغ پرداخت به تومان (مورد نیاز نیست)

        Returns:
            Dict: نتیجه تأیید پرداخت
        """
        if not self.merchant_id:
            raise GatewayConfigurationError("کلید API آیدی پی تنظیم نشده است")

        # دریافت پارامترهای بازگشت از درگاه
        # در آیدی پی، اطلاعات درخواست و پاسخ از طریق id و order_id پاس داده می‌شوند
        try:
            # ساخت داده‌های درخواست
            payload = {
                'id': authority,
                'order_id': '',  # این مقدار باید از پارامترهای بازگشت از درگاه دریافت شود
            }

            # ساخت هدرهای درخواست
            headers = {
                'X-API-KEY': self.merchant_id,
                'X-SANDBOX': '1' if self.is_sandbox else '0',
                'Content-Type': 'application/json',
            }

            # ارسال درخواست تأیید به آیدی پی
            logger.info(f"درخواست تأیید پرداخت به آیدی پی: {authority}")
            response = requests.post(self.verify_url, json=payload, headers=headers)

            # بررسی پاسخ
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                track_id = data.get('track_id', '')
                card_no = data.get('payment', {}).get('card_no', '')
                hashed_card_no = data.get('payment', {}).get('hashed_card_no', '')

                # بررسی وضعیت پرداخت
                if status == 100:
                    # پرداخت موفق
                    logger.info(f"پرداخت با موفقیت تأیید شد: {track_id}")
                    return {
                        'success': True,
                        'reference_id': track_id,
                        'authority': authority,
                        'gateway': 'idpay',
                        'amount': amount,
                        'card_number': card_no,
                        'card_hashpan': hashed_card_no,
                    }
                else:
                    # پرداخت ناموفق
                    error_message = self._get_status_message(status)
                    logger.error(f"خطا در تأیید پرداخت آیدی پی: {status} - {error_message}")
                    raise PaymentVerificationError(error_message)
            else:
                self.handle_http_error(response)

        except requests.RequestException as e:
            logger.error(f"خطا در ارتباط با آیدی پی: {str(e)}")
            raise PaymentGatewayError(gateway_name='IdPay', gateway_error=str(e))

    def _get_status_message(self, status: int) -> str:
        """
        دریافت پیام وضعی