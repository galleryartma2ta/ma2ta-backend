# gallery/api/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    GalleryViewSet, ExhibitionViewSet, AuctionEventViewSet,
    AuctionItemViewSet, ExhibitionImageViewSet
)

router = DefaultRouter()
router.register('galleries', GalleryViewSet, basename='gallery')
router.register('exhibitions', ExhibitionViewSet, basename='exhibition')
router.register('auctions', AuctionEventViewSet, basename='auction')
router.register('auction-items', AuctionItemViewSet, basename='auction-item')
router.register('exhibition-images', ExhibitionImageViewSet, basename='exhibition-image')

urlpatterns = [
    # ثبت پیشنهاد قیمت در حراجی
    path('place-bid/', AuctionItemViewSet.as_view({'post': 'place_bid'}), name='place-bid'),
]