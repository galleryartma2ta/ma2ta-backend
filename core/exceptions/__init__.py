# core/exceptions/__init__.py

from core.exceptions.api import (
    APIException,
    NotFound,
    ValidationError,
    PermissionDenied,
    AuthenticationFailed,
    Throttled,
    ServiceUnavailable
)

from core.exceptions.payment import (
    PaymentError,
    PaymentGatewayError,
    PaymentCanceledError,
    InsufficientFundsError,
    PaymentExpiredError,
    RefundError
)

__all__ = [
    # API exceptions
    'APIException',
    'NotFound',
    'ValidationError',
    'PermissionDenied',
    'AuthenticationFailed',
    'Throttled',
    'ServiceUnavailable',

    # Payment exceptions
    'PaymentError',
    'PaymentGatewayError',
    'PaymentCanceledError',
    'InsufficientFundsError',
    'PaymentExpiredError',
    'RefundError',
]