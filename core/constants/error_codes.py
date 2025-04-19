# core/constants/error_codes.py

from django.utils.translation import gettext_lazy as _

# کدهای خطای عمومی
ERROR_GENERAL = {
    'code': 'general_error',
    'message': _('خطای عمومی رخ داده است.')
}

ERROR_NOT_FOUND = {
    'code': 'not_found',
    'message': _('منبع درخواستی یافت نشد.')
}

ERROR_UNAUTHORIZED = {
    'code': 'unauthorized',
    'message': _('دسترسی غیرمجاز')
}

ERROR_FORBIDDEN = {
    'code': 'forbidden',
    'message': _('شما مجوز دسترسی به این محتوا را ندارید.')
}

ERROR_VALIDATION = {
    'code': 'validation_error',
    'message': _('اطلاعات وارد شده نامعتبر است.')
}

# خطاهای مربوط به کاربران
ERROR_USER_EXISTS = {
    'code': 'user_exists',
    'message': _('کاربری با این اطلاعات قبلاً ثبت‌نام کرده است.')
}

ERROR_WRONG_CREDENTIALS = {
    'code': 'wrong_credentials',
    'message': _('نام کاربری یا رمز عبور اشتباه است.')
}

ERROR_ACCOUNT_INACTIVE = {
    'code': 'account_inactive',
    'message': _('حساب کاربری شما غیرفعال است.')
}

# خطاهای مربوط به محصولات
ERROR_PRODUCT_UNAVAILABLE = {
    'code': 'product_unavailable',
    'message': _('محصول در حال حاضر در دسترس نیست.')
}

ERROR_PRODUCT_SOLD = {
    'code': 'product_sold',
    'message': _('این اثر هنری قبلاً فروخته شده است.')
}

ERROR_MAX_ARTWORKS_REACHED = {
    'code': 'max_artworks_reached',
    'message': _('شما به حداکثر تعداد مجاز آثار رسیده‌اید.')
}

# خطاهای مربوط به پرداخت
ERROR_PAYMENT_FAILED = {
    'code': 'payment_failed',
    'message': _('پرداخت با مشکل مواجه شد.')
}

ERROR_INSUFFICIENT_FUNDS = {
    'code': 'insufficient_funds',
    'message': _('موجودی کافی نیست.')
}

ERROR_PAYMENT_CANCELED = {
    'code': 'payment_canceled',
    'message': _('پرداخت لغو شد.')
}

ERROR_PAYMENT_EXPIRED = {
    'code': 'payment_expired',
    'message': _('زمان پرداخت منقضی شده است.')
}

# خطاهای مربوط به سبد خرید
ERROR_CART_EMPTY = {
    'code': 'cart_empty',
    'message': _('سبد خرید شما خالی است.')
}

ERROR_CART_ITEM_NOT_FOUND = {
    'code': 'cart_item_not_found',
    'message': _('آیتم مورد نظر در سبد خرید یافت نشد.')
}

# خطاهای مربوط به آپلود فایل
ERROR_FILE_TOO_LARGE = {
    'code': 'file_too_large',
    'message': _('حجم فایل بیش از حد مجاز است.')
}

ERROR_INVALID_FILE_TYPE = {
    'code': 'invalid_file_type',
    'message': _('نوع فایل مجاز نیست.')
}

# خطاهای مربوط به حراجی
ERROR_AUCTION_ENDED = {
    'code': 'auction_ended',
    'message': _('حراجی به پایان رسیده است.')
}

ERROR_BID_TOO_LOW = {
    'code': 'bid_too_low',
    'message': _('پیشنهاد قیمت شما پایین‌تر از حداقل قیمت مجاز است.')
}