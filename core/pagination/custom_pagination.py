# core/pagination/custom_pagination.py

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import (
    PageNumberPagination,
    LimitOffsetPagination,
    CursorPagination
)
from rest_framework.response import Response
from collections import OrderedDict


class CustomPageNumberPagination(PageNumberPagination):
    """
    صفحه‌بندی سفارشی با قابلیت تنظیم اندازه صفحه.

    پارامترهای درخواست:
        page: شماره صفحه (پیش‌فرض: 1)
        page_size: تعداد آیتم‌ها در هر صفحه (پیش‌فرض: 10، حداکثر: 100)

    مثال: /api/products/?page=2&page_size=20
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        فرمت پاسخ صفحه‌بندی سفارشی.
        افزودن اطلاعات کلی مانند تعداد کل آیتم‌ها، تعداد صفحات و...
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('current_page', self.page.number),
            ('results', data)
        ]))

    def get_paginated_response_schema(self, schema):
        """
        تعریف اسکیمای پاسخ صفحه‌بندی برای مستندات API.
        """
        return {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': _('تعداد کل آیتم‌ها')
                },
                'total_pages': {
                    'type': 'integer',
                    'description': _('تعداد کل صفحات')
                },
                'next': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': _('لینک صفحه بعدی (در صورت وجود)')
                },
                'previous': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': _('لینک صفحه قبلی (در صورت وجود)')
                },
                'current_page': {
                    'type': 'integer',
                    'description': _('شماره صفحه فعلی')
                },
                'results': schema,
            }
        }


class StandardResultsSetPagination(CustomPageNumberPagination):
    """
    صفحه‌بندی استاندارد برای اکثر API‌ها.

    پارامترهای درخواست:
        page: شماره صفحه (پیش‌فرض: 1)
        page_size: تعداد آیتم‌ها در هر صفحه (پیش‌فرض: 10، حداکثر: 100)

    مثال: /api/artists/?page=2&page_size=20
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(CustomPageNumberPagination):
    """
    صفحه‌بندی با اندازه بزرگتر برای API‌هایی که نیاز به تعداد بیشتری داده دارند.

    پارامترهای درخواست:
        page: شماره صفحه (پیش‌فرض: 1)
        page_size: تعداد آیتم‌ها در هر صفحه (پیش‌فرض: 50، حداکثر: 500)

    مثال: /api/search/?page=2&page_size=100
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class CustomLimitOffsetPagination(LimitOffsetPagination):
    """
    صفحه‌بندی با استفاده از پارامترهای limit و offset.

    پارامترهای درخواست:
        limit: تعداد آیتم‌ها در هر صفحه (پیش‌فرض: 10)
        offset: تعداد آیتم‌هایی که باید رد شوند (پیش‌فرض: 0)

    مثال: /api/products/?limit=20&offset=40 (آیتم‌های 41 تا 60)
    """
    default_limit = 10
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'

    def get_paginated_response(self, data):
        """
        فرمت پاسخ صفحه‌بندی سفارشی.
        """
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('limit', self.limit),
            ('offset', self.offset),
            ('results', data)
        ]))

    def get_paginated_response_schema(self, schema):
        """
        تعریف اسکیمای پاسخ صفحه‌بندی برای مستندات API.
        """
        return {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': _('تعداد کل آیتم‌ها')
                },
                'next': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': _('لینک بعدی (در صورت وجود)')
                },
                'previous': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': _('لینک قبلی (در صورت وجود)')
                },
                'limit': {
                    'type': 'integer',
                    'description': _('تعداد آیتم‌ها در این صفحه')
                },
                'offset': {
                    'type': 'integer',
                    'description': _('تعداد آیتم‌های رد شده')
                },
                'results': schema,
            }
        }


class CursorPaginationWithCount(CursorPagination):
    """
    صفحه‌بندی بر اساس کرسور با اضافه کردن تعداد کل آیتم‌ها.

    صفحه‌بندی کرسور برای مجموعه‌های بزرگ داده مناسب است و کارایی بهتری دارد.

    پارامترهای درخواست:
        cursor: کرسور بعدی یا قبلی
        page_size: تعداد آیتم‌ها در هر صفحه (پیش‌فرض: 10، حداکثر: 100)

    مثال: /api/feed/?cursor=cD0yMDIxLTA3LTIwKzE1JTNBMjMlM0ExMC4xMDQ2MTUlMkIwMCUzQTAw&page_size=20
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'  # ترتیب پیش‌فرض بر اساس زمان ایجاد (از جدید به قدیم)
    cursor_query_param = 'cursor'

    def paginate_queryset(self, queryset, request, view=None):
        """
        ذخیره تعداد کل آیتم‌ها قبل از اعمال صفحه‌بندی.
        """
        self.count = queryset.count()
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        """
        فرمت پاسخ صفحه‌بندی سفارشی با اضافه کردن تعداد کل آیتم‌ها.
        """
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

    def get_paginated_response_schema(self, schema):
        """
        تعریف اسکیمای پاسخ صفحه‌بندی برای مستندات API.
        """
        return {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': _('تعداد کل آیتم‌ها')
                },
                'next': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': _('لینک کرسور بعدی (در صورت وجود)')
                },
                'previous': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': _('لینک کرسور قبلی (در صورت وجود)')
                },
                'results': schema,
            }
        }


class ArtworkPagination(CustomPageNumberPagination):
    """
    صفحه‌بندی سفارشی برای آثار هنری.

    پارامترهای درخواست:
        page: شماره صفحه (پیش‌فرض: 1)
        page_size: تعداد آثار در هر صفحه (پیش‌فرض: 12، حداکثر: 100)

    مثال: /api/artworks/?page=2&page_size=24
    """
    page_size = 12  # اندازه مناسب برای نمایش آثار هنری در شبکه
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        فرمت پاسخ صفحه‌بندی سفارشی با اضافه کردن اطلاعات مفید مثل فیلترهای فعال.
        """
        response_data = OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('current_page', self.page.number),
            ('results', data)
        ])

        # اضافه کردن اطلاعات فیلترهای فعال در صورت وجود
        request = self.request
        active_filters = {}

        # فیلترهای رایج برای آثار هنری
        filter_params = ['category', 'style', 'min_price', 'max_price', 'artist', 'status', 'orientation']

        for param in filter_params:
            if param in request.query_params:
                active_filters[param] = request.query_params.get(param)

        if active_filters:
            response_data['active_filters'] = active_filters

        return Response(response_data)


class ArtistPagination(CustomPageNumberPagination):
    """
    صفحه‌بندی سفارشی برای هنرمندان.

    پارامترهای درخواست:
        page: شماره صفحه (پیش‌فرض: 1)
        page_size: تعداد هنرمندان در هر صفحه (پیش‌فرض: 16، حداکثر: 100)

    مثال: /api/artists/?page=2&page_size=20
    """
    page_size = 16  # اندازه مناسب برای نمایش کارت‌های هنرمندان
    page_size_query_param = 'page_size'
    max_page_size = 100


class ExhibitionPagination(CustomPageNumberPagination):
    """
    صفحه‌بندی سفارشی برای نمایشگاه‌ها.

    پارامترهای درخواست:
        page: شماره صفحه (پیش‌فرض: 1)
        page_size: تعداد نمایشگاه‌ها در هر صفحه (پیش‌فرض: 9، حداکثر: 50)

    مثال: /api/exhibitions/?page=2&page_size=12
    """
    page_size = 9  # اندازه مناسب برای نمایش کارت‌های نمایشگاه
    page_size_query_param = 'page_size'
    max_page_size = 50


class InfiniteMixedPagination(CustomLimitOffsetPagination):
    """
    صفحه‌بندی برای محتوای مختلط مثل صفحه خانه یا فید.

    پارامترهای درخواست:
        limit: تعداد آیتم‌ها (پیش‌فرض: 20)
        offset: تعداد آیتم‌هایی که باید رد شوند (پیش‌فرض: 0)

    مثال: /api/feed/?limit=20&offset=40
    """
    default_limit = 20
    max_limit = 200

    def get_paginated_response(self, data):
        """
        فرمت پاسخ سفارشی برای محتوای مختلط.
        """
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('has_more', bool(self.get_next_link())),  # برای اسکرول بی‌نهایت
            ('results', data)
        ]))