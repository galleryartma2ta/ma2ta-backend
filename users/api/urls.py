from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet, AddressViewSet

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]