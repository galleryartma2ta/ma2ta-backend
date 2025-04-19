# core/exceptions/payment.py

from django.utils.translation import gettext_lazy as _
from rest_framework import status

from core.exceptions.api import APIException
from core.constants.error_codes import (
    ERROR_PAYMENT_FAILED,
    ERROR_PAYMENT_CANCELED,
    ERROR_PAYMENT_EXPIRED,
    ERROR_INSUFFICIENT_FUNDS,
)


class PaymentError(APIException):
    """
    استثنای پایه برای خطاهای پرداخت.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_PAYMENT_FAILED['message']
    default_code = ERROR_PAYMENT_FAILED['code']


class PaymentGatewayError(PaymentError):
    """
    استثنای خطای ارتباط با درگاه پرداخت.
    """
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = _("خطا در ارتباط با درگاه پرداخت. لطفاً بعداً تلاش کنید.")
    default_code = "payment_gateway_error"

    def __init__(self, gateway_name=None, gateway_error=None, detail=None, code=None):
        if detail is None and gateway_name:
            detail = _("خطا در ارتباط با درگاه پرداخت {gateway}").format(gateway=gateway_name)

            if gateway_error:
                detail = f"{detail}: {gateway_error}"

        super().__init__(detail, code)


class PaymentCanceledError(PaymentError):
    """
    استثنای لغو پرداخت توسط کاربر.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_PAYMENT_CANCELED['message']
    default_code = ERROR_PAYMENT_CANCELED['code']


class PaymentExpiredError(PaymentError):
    """
    استثنای منقضی شدن زمان پرداخت.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_PAYMENT_EXPIRED['message']
    default_code = ERROR_PAYMENT_EXPIRED['code']


class InsufficientFundsError(PaymentError):
    """
    استثنای کافی نبودن موجودی.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ERROR_INSUFFICIENT_FUNDS['message']
    default_code = ERROR_INSUFFICIENT_FUNDS['code']


class RefundError(PaymentError):
    """
    استثنای خطا در فرآیند بازگشت وجه.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("خطا در فرآیند بازگشت وجه.")
    default_code = "refund_error"

    def __init__(self, order_number=None, detail=None, code=None):
        if detail is None and order_number:
            detail = _("خطا در بازگشت وجه برای سفارش {order_number}").format(order_number=order_number)

        super().__init__(detail, code)


class InvalidPaymentAmountError(PaymentError):
    """
    استثنای مبلغ پرداخت نامعتبر.
    """
    default_detail = _("مبلغ پرداخت نامعتبر است.")
    default_code = "invalid_payment_amount"


class PaymentVerificationError(PaymentError):
    """
    استثنای خطا در تأیید پرداخت.
    """
    default_detail = _("تأیید تراکنش با خطا مواجه شد.")
    default_code = "payment_verification_error"


class WalletDeductionError(PaymentError):
    """
    استثنای خطا در برداشت از کیف پول.
    """
    default_detail = _("برداشت از کیف پول با خطا مواجه شد.")
    default_code = "wallet_deduction_error"


class WithdrawalError(PaymentError):
    """
    استثنای خطا در برداشت وجه.
    """
    default_detail = _("خطا در درخواست برداشت وجه.")
    default_code = "withdrawal_error"


class MinimumWithdrawalError(WithdrawalError):
    """
    استثنای رعایت نشدن حداقل مبلغ برداشت.
    """
    default_detail = _("مبلغ درخواستی کمتر از حداقل مبلغ مجاز برداشت است.")
    default_code = "minimum_withdrawal_error"


class GatewayConfigurationError(PaymentError):
    """
    استثنای خطا در تنظیمات درگاه پرداخت.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("خطا در تنظیمات درگاه پرداخت.")
    default_code = "gateway_configuration_error"