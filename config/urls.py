"""
پیکربندی URL های اصلی پروژه Ma2tA.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# تنظیم مستندات Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Ma2tA API",
        default_version='v1',
        description="API سرویس گالری آنلاین هنری Ma2tA",
        terms_of_service="https://www.ma2ta.com/terms/",
        contact=openapi.Contact(email="info@ma2ta.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# الگوهای URL اصلی
urlpatterns = [
    # پنل ادمین
    path('admin/', admin.site.urls),

    # API نسخه 1
    path('api/v1/', include('apps.api.v1.urls')),

    # احراز هویت
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),

    # مستندات API
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # اندپوینت‌های اختصاصی هر ماژول 
    path('api/v1/products/', include('apps.products.api.urls')),
    path('api/v1/artists/', include('apps.artists.api.urls')),
    path('api/v1/users/', include('apps.users.api.urls')),
    path('api/v1/orders/', include('apps.orders.api.urls')),
    path('api/v1/gallery/', include('apps.gallery.api.urls')),
    path('api/v1/blog/', include('apps.blog.api.urls')),

    # نقشه سایت
    path('sitemap.xml', TemplateView.as_view(
        template_name="sitemaps/sitemap.xml",
        content_type='application/xml'
    )),

    # صفحه وضعیت سلامت سیستم 
    path('health/', include('health_check.urls')),
]

# اضافه کردن مسیرهای فایل‌های رسانه در محیط توسعه
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
                          path('__debug__/', include(debug_toolbar.urls)),
                      ] + urlpatterns

# مسیر برای صفحات React (برای استفاده در حالت تک‌سرور)
# همه مسیرهای نامشخص به برنامه React ارجاع می‌شوند
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]