# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API overview view
from .views import api_overview

# Import routers from each app
from users.api.routers import router as users_router
from products.api.routers import router as products_router
from orders.api.routers import router as orders_router
from payments.api.routers import router as payments_router
from gallery.api.routers import router as gallery_router
from artists.api.routers import router as artists_router
from blog.api.routers import router as blog_router
from notifications.api.routers import router as notifications_router

# Combine all routers
router = DefaultRouter()
router.registry.extend(users_router.registry)
router.registry.extend(products_router.registry)
router.registry.extend(orders_router.registry)
router.registry.extend(payments_router.registry)
router.registry.extend(gallery_router.registry)
router.registry.extend(artists_router.registry)
router.registry.extend(blog_router.registry)
router.registry.extend(notifications_router.registry)

urlpatterns = [
    path('', api_overview, name='api-overview'),
    path('', include(router.urls)),
    path('users/', include('users.api.urls')),
    path('products/', include('products.api.urls')),
    path('orders/', include('orders.api.urls')),
    path('payments/', include('payments.api.urls')),
    path('gallery/', include('gallery.api.urls')),
    path('artists/', include('artists.api.urls')),
    path('blog/', include('blog.api.urls')),
    path('notifications/', include('notifications.api.urls')),
]