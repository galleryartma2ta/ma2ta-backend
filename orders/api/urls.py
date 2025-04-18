# orders/api/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CartViewSet, OrderViewSet, WishlistViewSet, CouponViewSet
)

router = DefaultRouter()
router.register('orders', OrderViewSet, basename='order')
router.register('coupons', CouponViewSet, basename='coupon')

urlpatterns = [
    # سبد خرید
    path('cart/', CartViewSet.as_view({'get': 'retrieve'}), name='cart-detail'),
    path('cart/add/', CartViewSet.as_view({'post': 'add_item'}), name='cart-add-item'),
    path('cart/remove/', CartViewSet.as_view({'post': 'remove_item'}), name='cart-remove-item'),
    path('cart/update-quantity/', CartViewSet.as_view({'post': 'update_quantity'}), name='cart-update-quantity'),
    path('cart/clear/', CartViewSet.as_view({'post': 'clear'}), name='cart-clear'),
    path('cart/apply-coupon/', CartViewSet.as_view({'post': 'apply_coupon'}), name='cart-apply-coupon'),

    # لیست علاقه‌مندی‌ها
    path('wishlist/', WishlistViewSet.as_view({'get': 'items'}), name='wishlist-items'),
    path('wishlist/add/', WishlistViewSet.as_view({'post': 'add'}), name='wishlist-add'),
    path('wishlist/remove/', WishlistViewSet.as_view({'post': 'remove'}), name='wishlist-remove'),
    path('wishlist/check/', WishlistViewSet.as_view({'get': 'check'}), name='wishlist-check'),
    path('wishlist/clear/', WishlistViewSet.as_view({'post': 'clear'}), name='wishlist-clear'),
]