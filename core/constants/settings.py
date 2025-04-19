# core/constants/settings.py

# تنظیمات آثار هنری
MAX_ARTWORK_SIZE = 10 * 1024 * 1024  # 10 مگابایت - حداکثر سایز آپلود تصویر
MAX_ARTWORKS_PER_ARTIST = {
    'free': 5,           # تعداد مجاز آثار برای حساب رایگان
    'basic': 20,         # تعداد مجاز آثار برای حساب پایه
    'premium': 50,       # تعداد مجاز آثار برای حساب ویژه
    'professional': 100  # تعداد مجاز آثار برای حساب حرفه‌ای
}
MAX_FEATURED_ARTWORKS = 8  # تعداد آثار برجسته در صفحه اصلی

# تنظیمات مالی و کمیسیون
DEFAULT_COMMISSION_RATE = 0.15  # نرخ کمیسیون پیش‌فرض (15%)
COMMISSION_RATES = {
    'beginner': 0.20,       # 20% کمیسیون برای هنرمندان مبتدی
    'intermediate': 0.15,   # 15% کمیسیون برای هنرمندان نیمه‌حرفه‌ای
    'professional': 0.10,   # 10% کمیسیون برای هنرمندان حرفه‌ای
    'master': 0.05,         # 5% کمیسیون برای استادان
    'verified': 0.05,       # 5% کمیسیون برای هنرمندان تأیید شده
}
MIN_WITHDRAWAL_AMOUNT = 500000  # حداقل مبلغ برداشت (500,000 تومان)

# تنظیمات حراجی
MIN_AUCTION_DURATION = 3  # حداقل مدت زمان حراجی (روز)
MAX_AUCTION_DURATION = 14  # حداکثر مدت زمان حراجی (روز)
AUCTION_AUTO_EXTEND_TIME = 15  # زمان تمدید خودکار حراجی (دقیقه)

# تنظیمات مهلت‌ها
ORDER_EXPIRATION_TIME = 60 * 30  # مهلت پرداخت سفارش (30 دقیقه)
PAYMENT_LINK_EXPIRATION = 60 * 15  # مدت اعتبار لینک پرداخت (15 دقیقه)

# تنظیمات API و محدودیت‌ها
API_DEFAULT_PAGE_SIZE = 10  # اندازه پیش‌فرض صفحه‌بندی API
API_MAX_PAGE_SIZE = 100  # حداکثر اندازه صفحه‌بندی API
API_THROTTLE_RATE = '60/minute'  # نرخ محدودیت درخواست API

# تنظیمات نمایش
RECENT_ARTWORKS_COUNT = 12  # تعداد آثار جدید در صفحه اصلی
RELATED_ARTWORKS_COUNT = 6  # تعداد آثار مرتبط
FEATURED_ARTISTS_COUNT = 8  # تعداد هنرمندان برجسته در صفحه اصلی

# تنظیمات تخفیف
MAX_DISCOUNT_PERCENTAGE = 70  # حداکثر درصد تخفیف (70%)
DISCOUNT_CODE_LENGTH = 8  # طول کد تخفیف

# تنظیمات بازخورد
MIN_REVIEW_LENGTH = 10  # حداقل طول متن نظر
MAX_REVIEW_LENGTH = 500  # حداکثر طول متن نظر

# تنظیمات واقعیت افزوده (AR)
AR_MODEL_FORMATS = ['glb', 'gltf', 'usdz']  # فرمت‌های مجاز مدل AR
AR_MAX_MODEL_SIZE = 20 * 1024 * 1024  # حداکثر سایز مدل AR (20 مگابایت)

# تنظیمات اعلان
NOTIFICATION_EXPIRY_DAYS = 30  # مدت زمان نگهداری اعلان‌ها (روز)

# تنظیمات بلاگ
BLOG_POSTS_PER_PAGE = 9  # تعداد پست‌ها در هر صفحه بلاگ
BLOG_RECENT_POSTS = 5  # تعداد پست‌های اخیر در سایدبار