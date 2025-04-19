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