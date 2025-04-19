# core/constants/choices.py

from django.utils.translation import gettext_lazy as _

# وضعیت محصولات
DRAFT = 'draft'
PUBLISHED = 'published'
SOLD = 'sold'
ARCHIVED = 'archived'
FEATURED = 'featured'
AUCTION = 'auction'

PRODUCT_STATUS_CHOICES = [
    (DRAFT, _('پیش‌نویس')),
    (PUBLISHED, _('منتشر شده')),
    (SOLD, _('فروخته شده')),
    (ARCHIVED, _('بایگانی شده')),
    (FEATURED, _('ویژه')),
    (AUCTION, _('در حراجی')),
]

# انواع آثار هنری
PAINTING = 'painting'
SCULPTURE = 'sculpture'
PHOTOGRAPHY = 'photography'
DIGITAL = 'digital'
CALLIGRAPHY = 'calligraphy'
HANDICRAFT = 'handicraft'
DRAWING = 'drawing'
PRINT = 'print'
MIXED_MEDIA = 'mixed_media'
OTHER = 'other'

ARTWORK_TYPE_CHOICES = [
    (PAINTING, _('نقاشی')),
    (SCULPTURE, _('مجسمه')),
    (PHOTOGRAPHY, _('عکاسی')),
    (DIGITAL, _('دیجیتال')),
    (CALLIGRAPHY, _('خوشنویسی')),
    (HANDICRAFT, _('صنایع دستی')),
    (DRAWING, _('طراحی')),
    (PRINT, _('چاپ')),
    (MIXED_MEDIA, _('میکس مدیا')),
    (OTHER, _('سایر')),
]

# وضعیت نمایشگاه‌ها
UPCOMING = 'upcoming'
ONGOING = 'ongoing'
PAST = 'past'
CANCELED = 'canceled'

EXHIBITION_STATUS_CHOICES = [
    (UPCOMING, _('آینده')),
    (ONGOING, _('در حال برگزاری')),
    (PAST, _('برگزار شده')),
    (CANCELED, _('لغو شده')),
]

# وضعیت سفارش‌ها
PENDING = 'pending'
PROCESSING = 'processing'
SHIPPED = 'shipped'
DELIVERED = 'delivered'
CANCELED = 'canceled'
RETURNED = 'returned'
REFUNDED = 'refunded'

ORDER_STATUS_CHOICES = [
    (PENDING, _('در انتظار پرداخت')),
    (PROCESSING, _('در حال پردازش')),
    (SHIPPED, _('ارسال شده')),
    (DELIVERED, _('تحویل داده شده')),
    (CANCELED, _('لغو شده')),
    (RETURNED, _('مرجوع شده')),
    (REFUNDED, _('بازپرداخت شده')),
]

# روش‌های پرداخت
ONLINE = 'online'
BANK_TRANSFER = 'bank_transfer'
CASH_ON_DELIVERY = 'cash_on_delivery'
WALLET = 'wallet'

PAYMENT_METHOD_CHOICES = [
    (ONLINE, _('پرداخت آنلاین')),
    (BANK_TRANSFER, _('انتقال بانکی')),
    (CASH_ON_DELIVERY, _('پرداخت در محل')),
    (WALLET, _('کیف پول')),
]

# سطوح هنرمندان
BEGINNER = 'beginner'
INTERMEDIATE = 'intermediate'
PROFESSIONAL = 'professional'
MASTER = 'master'
VERIFIED = 'verified'

ARTIST_LEVEL_CHOICES = [
    (BEGINNER, _('مبتدی')),
    (INTERMEDIATE, _('نیمه‌حرفه‌ای')),
    (PROFESSIONAL, _('حرفه‌ای')),
    (MASTER, _('استاد')),
    (VERIFIED, _('تأیید شده')),
]

# نوع تخفیف‌ها
FIXED = 'fixed'
PERCENTAGE = 'percentage'

DISCOUNT_TYPE_CHOICES = [
    (FIXED, _('مبلغ ثابت')),
    (PERCENTAGE, _('درصدی')),
]

# نوع اشتراک‌ها
FREE = 'free'
BASIC = 'basic'
PREMIUM = 'premium'
PROFESSIONAL = 'professional'

SUBSCRIPTION_TYPE_CHOICES = [
    (FREE, _('رایگان')),
    (BASIC, _('پایه')),
    (PREMIUM, _('ویژه')),
    (PROFESSIONAL, _('حرفه‌ای')),
]

# وضعیت حراجی
PLANNED = 'planned'
ACTIVE = 'active'
ENDED = 'ended'
CANCELED = 'canceled'

AUCTION_STATUS_CHOICES = [
    (PLANNED, _('برنامه‌ریزی شده')),
    (ACTIVE, _('در حال برگزاری')),
    (ENDED, _('پایان یافته')),
    (CANCELED, _('لغو شده')),
]