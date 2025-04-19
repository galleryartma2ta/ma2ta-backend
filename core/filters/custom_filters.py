# core/filters/custom_filters.py

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import FilterSet, filters

from core.utils.date_utils import parse_jalali_date


class ArtworkFilter(FilterSet):
    """
    فیلترهای سفارشی برای آثار هنری.
    این فیلترها امکان جستجو و فیلتر کردن آثار هنری را فراهم می‌کنند.
    """
    # فیلتر بر اساس عنوان، توضیحات یا برچسب‌ها
    search = filters.CharFilter(method='filter_search', label=_('جستجو'))

    # فیلتر بر اساس دسته‌بندی‌ها
    category = filters.CharFilter(field_name='category__slug')
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name='category__slug',
        to_field_name='slug',
        conjoined=False,
        label=_('دسته‌بندی‌ها')
    )

    # فیلتر بر اساس سبک‌های هنری
    style = filters.CharFilter(field_name='style__slug')
    styles = django_filters.ModelMultipleChoiceFilter(
        field_name='style__slug',
        to_field_name='slug',
        conjoined=False,
        label=_('سبک‌ها')
    )

    # فیلتر بر اساس هنرمند
    artist = filters.CharFilter(field_name='artist__slug')

    # فیلتر بر اساس قیمت
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte', label=_('حداقل قیمت'))
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte', label=_('حداکثر قیمت'))

    # فیلتر بر اساس وضعیت
    status = filters.CharFilter(field_name='status')
    is_sold = filters.BooleanFilter(field_name='is_sold', label=_('فروخته شده'))

    # فیلتر بر اساس ابعاد
    orientation = filters.ChoiceFilter(
        choices=[
            ('landscape', _('افقی')),
            ('portrait', _('عمودی')),
            ('square', _('مربع')),
        ],
        method='filter_orientation',
        label=_('جهت')
    )

    # فیلتر بر اساس تاریخ ایجاد
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte', label=_('ایجاد شده پس از'))
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte', label=_('ایجاد شده پیش از'))

    # فیلتر بر اساس تاریخ جلالی
    jalali_created_after = filters.CharFilter(method='filter_jalali_created_after', label=_('ایجاد شده پس از (جلالی)'))
    jalali_created_before = filters.CharFilter(method='filter_jalali_created_before',
                                               label=_('ایجاد شده پیش از (جلالی)'))

    # فیلتر بر اساس ویژگی‌های خاص
    featured = filters.BooleanFilter(field_name='is_featured', label=_('ویژه'))
    has_discount = filters.BooleanFilter(method='filter_has_discount', label=_('دارای تخفیف'))

    class Meta:
        fields = [
            'search', 'category', 'categories', 'style', 'styles', 'artist',
            'min_price', 'max_price', 'status', 'is_sold', 'orientation',
            'created_after', 'created_before', 'featured', 'has_discount'
        ]

    def filter_search(self, queryset, name, value):
        """جستجو در عنوان، توضیحات و برچسب‌ها"""
        if not value:
            return queryset

        # جستجو در فیلدهای مختلف
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(tags__name__icontains=value)
        ).distinct()

    def filter_orientation(self, queryset, name, value):
        """فیلتر بر اساس جهت تصویر"""
        if value == 'landscape':
            # حالت افقی: عرض بیشتر از ارتفاع
            return queryset.filter(width__gt=0, height__gt=0).filter(width__gt=models.F('height'))
        elif value == 'portrait':
            # حالت عمودی: ارتفاع بیشتر از عرض
            return queryset.filter(width__gt=0, height__gt=0).filter(height__gt=models.F('width'))
        elif value == 'square':
            # حالت مربع: عرض و ارتفاع تقریباً برابر
            return queryset.filter(width__gt=0, height__gt=0).filter(
                Q(width=models.F('height')) |
                (models.F('height') / models.F('width')).between(0.9, 1.1)
            )

        return queryset

    def filter_has_discount(self, queryset, name, value):
        """فیلتر بر اساس داشتن تخفیف"""
        if value is True:
            # آثاری که قیمت فروش کمتر از قیمت اصلی دارند
            return queryset.filter(sale_price__lt=models.F('original_price'))
        elif value is False:
            # آثاری که تخفیف ندارند
            return queryset.filter(
                Q(sale_price__isnull=True) |
                Q(sale_price=models.F('original_price'))
            )
        return queryset

    def filter_jalali_created_after(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی پس از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(created_at__gte=date)
        return queryset

    def filter_jalali_created_before(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی پیش از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(created_at__lte=date)
        return queryset


class ArtistFilter(FilterSet):
    """
    فیلترهای سفارشی برای هنرمندان.
    این فیلترها امکان جستجو و فیلتر کردن هنرمندان را فراهم می‌کنند.
    """
    # جستجو بر اساس نام، نام کاربری یا بیوگرافی
    search = filters.CharFilter(method='filter_search', label=_('جستجو'))

    # فیلتر بر اساس سطح هنرمند
    level = filters.ChoiceFilter(field_name='level', choices=[
        ('beginner', _('مبتدی')),
        ('intermediate', _('نیمه‌حرفه‌ای')),
        ('professional', _('حرفه‌ای')),
        ('master', _('استاد')),
        ('verified', _('تأیید شده')),
    ])

    # فیلتر بر اساس سبک‌های هنری
    style = filters.CharFilter(field_name='styles__slug')
    styles = django_filters.ModelMultipleChoiceFilter(
        field_name='styles__slug',
        to_field_name='slug',
        conjoined=False,
        label=_('سبک‌ها')
    )

    # فیلتر بر اساس ویژگی‌های خاص
    is_verified = filters.BooleanFilter(field_name='is_verified', label=_('تأیید شده'))
    is_featured = filters.BooleanFilter(field_name='is_featured', label=_('ویژه'))
    has_active_subscription = filters.BooleanFilter(method='filter_active_subscription', label=_('اشتراک فعال'))

    # فیلتر بر اساس تعداد آثار
    min_artworks = filters.NumberFilter(method='filter_min_artworks', label=_('حداقل تعداد آثار'))

    # فیلتر بر اساس محل زندگی
    location = filters.CharFilter(field_name='location__name', lookup_expr='icontains', label=_('محل زندگی'))
    city = filters.CharFilter(field_name='city__name', lookup_expr='icontains', label=_('شهر'))

    class Meta:
        fields = [
            'search', 'level', 'style', 'styles', 'is_verified', 'is_featured',
            'has_active_subscription', 'min_artworks', 'location', 'city'
        ]

    def filter_search(self, queryset, name, value):
        """جستجو در نام، نام کاربری و بیوگرافی"""
        if not value:
            return queryset

        # جستجو در فیلدهای مختلف
        return queryset.filter(
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(user__username__icontains=value) |
            Q(artistic_name__icontains=value) |
            Q(bio__icontains=value)
        ).distinct()

    def filter_active_subscription(self, queryset, name, value):
        """فیلتر بر اساس داشتن اشتراک فعال"""
        if value is True:
            # هنرمندانی که اشتراک فعال دارند
            return queryset.filter(has_active_subscription=True)
        elif value is False:
            # هنرمندانی که اشتراک فعال ندارند
            return queryset.filter(has_active_subscription=False)
        return queryset

    def filter_min_artworks(self, queryset, name, value):
        """فیلتر بر اساس حداقل تعداد آثار"""
        if value is not None and value > 0:
            # فقط هنرمندانی که حداقل تعداد آثار مشخص شده را دارند
            return queryset.annotate(artwork_count=models.Count('artworks')).filter(artwork_count__gte=value)
        return queryset


class OrderFilter(FilterSet):
    """
    فیلترهای سفارشی برای سفارش‌ها.
    این فیلترها امکان جستجو و فیلتر کردن سفارش‌ها را فراهم می‌کنند.
    """
    # فیلتر بر اساس شماره سفارش یا اطلاعات مشتری
    search = filters.CharFilter(method='filter_search', label=_('جستجو'))

    # فیلتر بر اساس وضعیت سفارش
    status = filters.ChoiceFilter(field_name='status', choices=[
        ('pending', _('در انتظار پرداخت')),
        ('processing', _('در حال پردازش')),
        ('shipped', _('ارسال شده')),
        ('delivered', _('تحویل داده شده')),
        ('canceled', _('لغو شده')),
        ('returned', _('مرجوع شده')),
        ('refunded', _('بازپرداخت شده')),
    ])

    # فیلتر بر اساس روش پرداخت
    payment_method = filters.ChoiceFilter(field_name='payment_method', choices=[
        ('online', _('پرداخت آنلاین')),
        ('bank_transfer', _('انتقال بانکی')),
        ('cash_on_delivery', _('پرداخت در محل')),
        ('wallet', _('کیف پول')),
    ])

    # فیلتر بر اساس مبلغ سفارش
    min_total = filters.NumberFilter(field_name='total_amount', lookup_expr='gte', label=_('حداقل مبلغ'))
    max_total = filters.NumberFilter(field_name='total_amount', lookup_expr='lte', label=_('حداکثر مبلغ'))

    # فیلتر بر اساس تاریخ سفارش
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte', label=_('ایجاد شده پس از'))
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte', label=_('ایجاد شده پیش از'))

    # فیلتر بر اساس تاریخ جلالی
    jalali_created_after = filters.CharFilter(method='filter_jalali_created_after', label=_('ایجاد شده پس از (جلالی)'))
    jalali_created_before = filters.CharFilter(method='filter_jalali_created_before',
                                               label=_('ایجاد شده پیش از (جلالی)'))

    # فیلتر هنرمندان
    artist = filters.CharFilter(method='filter_artist', label=_('هنرمند'))

    class Meta:
        fields = [
            'search', 'status', 'payment_method', 'min_total', 'max_total',
            'created_after', 'created_before', 'artist'
        ]

    def filter_search(self, queryset, name, value):
        """جستجو در شماره سفارش و اطلاعات مشتری"""
        if not value:
            return queryset

        # جستجو در فیلدهای مختلف
        return queryset.filter(
            Q(order_number__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(user__email__icontains=value) |
            Q(shipping_address__icontains=value) |
            Q(tracking_number__icontains=value)
        ).distinct()

    def filter_artist(self, queryset, name, value):
        """فیلتر سفارش‌های مربوط به یک هنرمند خاص"""
        if not value:
            return queryset

        # سفارش‌هایی که شامل آثار هنرمند مشخص شده هستند
        return queryset.filter(items__artwork__artist__slug=value).distinct()

    def filter_jalali_created_after(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی پس از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(created_at__gte=date)
        return queryset

    def filter_jalali_created_before(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی پیش از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(created_at__lte=date)
        return queryset


class GalleryFilter(FilterSet):
    """
    فیلترهای سفارشی برای گالری‌ها.
    این فیلترها امکان جستجو و فیلتر کردن گالری‌ها را فراهم می‌کنند.
    """
    # جستجو در نام و توضیحات گالری
    search = filters.CharFilter(method='filter_search', label=_('جستجو'))

    # فیلتر بر اساس نوع گالری
    gallery_type = filters.ChoiceFilter(field_name='gallery_type', choices=[
        ('physical', _('فیزیکی')),
        ('virtual', _('مجازی')),
        ('mixed', _('ترکیبی')),
    ])

    # فیلتر بر اساس موقعیت مکانی
    city = filters.CharFilter(field_name='city__name', lookup_expr='icontains', label=_('شهر'))
    location = filters.CharFilter(field_name='location', lookup_expr='icontains', label=_('موقعیت'))

    # فیلتر بر اساس ویژگی‌های خاص
    is_verified = filters.BooleanFilter(field_name='is_verified', label=_('تأیید شده'))
    is_featured = filters.BooleanFilter(field_name='is_featured', label=_('ویژه'))

    # فیلتر بر اساس تعداد نمایشگاه‌های فعال
    has_active_exhibitions = filters.BooleanFilter(method='filter_active_exhibitions', label=_('نمایشگاه فعال'))

    class Meta:
        fields = [
            'search', 'gallery_type', 'city', 'location',
            'is_verified', 'is_featured', 'has_active_exhibitions'
        ]

    def filter_search(self, queryset, name, value):
        """جستجو در نام و توضیحات گالری"""
        if not value:
            return queryset

        # جستجو در فیلدهای مختلف
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(owner__first_name__icontains=value) |
            Q(owner__last_name__icontains=value) |
            Q(city__name__icontains=value)
        ).distinct()

    def filter_active_exhibitions(self, queryset, name, value):
        """فیلتر گالری‌هایی که نمایشگاه فعال دارند"""
        if value is True:
            # گالری‌هایی که حداقل یک نمایشگاه فعال دارند
            now = timezone.now()
            return queryset.filter(
                exhibitions__start_date__lte=now,
                exhibitions__end_date__gte=now,
                exhibitions__status='ongoing'
            ).distinct()
        elif value is False:
            # گالری‌هایی که نمایشگاه فعال ندارند
            now = timezone.now()
            active_gallery_ids = queryset.filter(
                exhibitions__start_date__lte=now,
                exhibitions__end_date__gte=now,
                exhibitions__status='ongoing'
            ).values_list('id', flat=True)

            return queryset.exclude(id__in=active_gallery_ids)

        return queryset


class ExhibitionFilter(FilterSet):
    """
    فیلترهای سفارشی برای نمایشگاه‌ها.
    این فیلترها امکان جستجو و فیلتر کردن نمایشگاه‌ها را فراهم می‌کنند.
    """
    # جستجو در عنوان و توضیحات نمایشگاه
    search = filters.CharFilter(method='filter_search', label=_('جستجو'))

    # فیلتر بر اساس وضعیت نمایشگاه
    status = filters.ChoiceFilter(field_name='status', choices=[
        ('upcoming', _('آینده')),
        ('ongoing', _('در حال برگزاری')),
        ('past', _('برگزار شده')),
        ('canceled', _('لغو شده')),
    ])

    # فیلتر بر اساس گالری
    gallery = filters.CharFilter(field_name='gallery__slug')

    # فیلتر بر اساس هنرمندان شرکت‌کننده
    artist = filters.CharFilter(method='filter_artist', label=_('هنرمند'))

    # فیلتر بر اساس تاریخ برگزاری
    start_after = filters.DateFilter(field_name='start_date', lookup_expr='gte', label=_('شروع پس از'))
    start_before = filters.DateFilter(field_name='start_date', lookup_expr='lte', label=_('شروع پیش از'))
    end_after = filters.DateFilter(field_name='end_date', lookup_expr='gte', label=_('پایان پس از'))
    end_before = filters.DateFilter(field_name='end_date', lookup_expr='lte', label=_('پایان پیش از'))

    # فیلتر بر اساس تاریخ جلالی
    jalali_start_after = filters.CharFilter(method='filter_jalali_start_after', label=_('شروع پس از (جلالی)'))
    jalali_start_before = filters.CharFilter(method='filter_jalali_start_before', label=_('شروع پیش از (جلالی)'))

    # فیلتر نمایشگاه‌های فعال
    is_active = filters.BooleanFilter(method='filter_active', label=_('فعال'))

    # فیلتر بر اساس موقعیت مکانی
    city = filters.CharFilter(field_name='gallery__city__name', lookup_expr='icontains', label=_('شهر'))

    class Meta:
        fields = [
            'search', 'status', 'gallery', 'artist',
            'start_after', 'start_before', 'end_after', 'end_before',
            'is_active', 'city'
        ]

    def filter_search(self, queryset, name, value):
        """جستجو در عنوان و توضیحات نمایشگاه"""
        if not value:
            return queryset

        # جستجو در فیلدهای مختلف
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(gallery__name__icontains=value) |
            Q(curator__first_name__icontains=value) |
            Q(curator__last_name__icontains=value)
        ).distinct()

    def filter_artist(self, queryset, name, value):
        """فیلتر نمایشگاه‌هایی که یک هنرمند خاص در آن‌ها شرکت دارد"""
        if not value:
            return queryset

        return queryset.filter(participating_artists__slug=value).distinct()

    def filter_active(self, queryset, name, value):
        """فیلتر نمایشگاه‌های فعال (در حال برگزاری)"""
        now = timezone.now()

        if value is True:
            # نمایشگاه‌های در حال برگزاری
            return queryset.filter(
                start_date__lte=now,
                end_date__gte=now,
                status='ongoing'
            )
        elif value is False:
            # نمایشگاه‌هایی که در حال برگزاری نیستند
            return queryset.exclude(
                start_date__lte=now,
                end_date__gte=now,
                status='ongoing'
            )

        return queryset

    def filter_jalali_start_after(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی شروع پس از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(start_date__gte=date)
        return queryset

    def filter_jalali_start_before(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی شروع پیش از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(start_date__lte=date)
        return queryset


class BlogPostFilter(FilterSet):
    """
    فیلترهای سفارشی برای مقالات وبلاگ.
    این فیلترها امکان جستجو و فیلتر کردن مقالات را فراهم می‌کنند.
    """
    # جستجو در عنوان، محتوا و برچسب‌ها
    search = filters.CharFilter(method='filter_search', label=_('جستجو'))

    # فیلتر بر اساس دسته‌بندی
    category = filters.CharFilter(field_name='category__slug')
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name='category__slug',
        to_field_name='slug',
        conjoined=False,
        label=_('دسته‌بندی‌ها')
    )

    # فیلتر بر اساس برچسب‌ها
    tag = filters.CharFilter(field_name='tags__slug')
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        conjoined=False,
        label=_('برچسب‌ها')
    )

    # فیلتر بر اساس نویسنده
    author = filters.CharFilter(field_name='author__username')

    # فیلتر بر اساس وضعیت
    status = filters.ChoiceFilter(field_name='status', choices=[
        ('draft', _('پیش‌نویس')),
        ('published', _('منتشر شده')),
        ('archived', _('بایگانی شده')),
    ])

    # فیلتر بر اساس تاریخ انتشار
    published_after = filters.DateFilter(field_name='publish_date', lookup_expr='gte', label=_('منتشر شده پس از'))
    published_before = filters.DateFilter(field_name='publish_date', lookup_expr='lte', label=_('منتشر شده پیش از'))

    # فیلتر بر اساس تاریخ جلالی
    jalali_published_after = filters.CharFilter(method='filter_jalali_published_after',
                                                label=_('منتشر شده پس از (جلالی)'))
    jalali_published_before = filters.CharFilter(method='filter_jalali_published_before',
                                                 label=_('منتشر شده پیش از (جلالی)'))

    # فیلتر مقالات ویژه
    is_featured = filters.BooleanFilter(field_name='is_featured', label=_('ویژه'))

    class Meta:
        fields = [
            'search', 'category', 'categories', 'tag', 'tags', 'author',
            'status', 'published_after', 'published_before', 'is_featured'
        ]

    def filter_search(self, queryset, name, value):
        """جستجو در عنوان، محتوا و برچسب‌های مقاله"""
        if not value:
            return queryset

        # جستجو در فیلدهای مختلف
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(excerpt__icontains=value) |
            Q(tags__name__icontains=value) |
            Q(author__first_name__icontains=value) |
            Q(author__last_name__icontains=value)
        ).distinct()

    def filter_jalali_published_after(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی انتشار پس از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(publish_date__gte=date)
        return queryset

    def filter_jalali_published_before(self, queryset, name, value):
        """فیلتر بر اساس تاریخ جلالی انتشار پیش از"""
        date = parse_jalali_date(value)
        if date:
            return queryset.filter(publish_date__lte=date)
        return queryset