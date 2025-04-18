from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ArtStyleViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'styles', ArtStyleViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
]