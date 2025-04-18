# gallery/api/views.py

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count

from gallery.models import (
    Gallery, GalleryArtist, Exhibition, ExhibitionImage,
    AuctionEvent, AuctionItem, AuctionBid
)
from .serializers import (
    GalleryListSerializer, GalleryDetailSerializer, GalleryArtistSerializer,
    ExhibitionListSerializer, ExhibitionDetailSerializer, ExhibitionImageSerializer,
    AuctionEventListSerializer, AuctionEventDetailSerializer,
    AuctionItemListSerializer, AuctionItemDetailSerializer,
    AuctionBidSerializer, PlaceBidSerializer
)


class GalleryViewSet(viewsets.ModelViewSet):
    """ویوست گالری‌ها"""

    queryset = Gallery.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'province', 'is_verified', 'featured']
    search_fields = ['name', 'description', 'short_description', 'city', 'province']
    ordering_fields = ['name', 'city', 'created_at']
    ordering = ['-featured', 'name']
    lookup_field = 'slug'

    def get_queryset(self):
        """فیلتر کردن گالری‌ها برای نمایش تنها موارد فعال برای کاربران عادی"""
        queryset = Gallery.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        """انتخاب سریالایزر مناسب بر اساس اکشن"""
        if self.action == 'list':
            return GalleryListSerializer
        return GalleryDetailSerializer

    def get_permissions(self):
        """تعیین دسترسی‌ها بر اساس اکشن"""
        if self.action in ['list', 'retrieve', 'exhibitions', 'auctions']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['get'])
    def exhibitions(self, request, slug=None):
        """نمایشگاه‌های یک گالری"""
        gallery = self.get_object()

        # نمایش نمایشگاه‌های فعال یا آینده برای کاربران عادی
        exhibitions = gallery.exhibitions.all()
        if not request.user.is_staff:
            exhibitions = exhibitions.filter(Q(status='active') | Q(status='upcoming'))

        serializer = ExhibitionListSerializer(exhibitions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def auctions(self, request, slug=None):
        """حراجی‌های یک گالری"""
        gallery = self.get_object()

        # نمایش حراجی‌های فعال یا آینده برای کاربران عادی
        auctions = gallery.auctions.all()
        if not request.user.is_staff:
            auctions = auctions.filter(Q(status='active') | Q(status='upcoming'))

        serializer = AuctionEventListSerializer(auctions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def artists(self, request, slug=None):
        """هنرمندان یک گالری"""
        gallery = self.get_object()

        gallery_artists = GalleryArtist.objects.filter(gallery=gallery, is_active=True)
        serializer = GalleryArtistSerializer(gallery_artists, many=True)
        return Response(serializer.data)


class ExhibitionViewSet(viewsets.ModelViewSet):
    """ویوست نمایشگاه‌ها"""

    queryset = Exhibition.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_virtual', 'is_featured']
    search_fields = ['title', 'description', 'short_description', 'curator']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']
    lookup_field = 'slug'

    def get_queryset(self):
        """فیلتر کردن نمایشگاه‌ها"""
        queryset = Exhibition.objects.all()

        # فیلتر برای کاربران عادی
        if not self.request.user.is_staff:
            queryset = queryset.exclude(status='canceled')

        # فیلتر بر اساس گالری
        gallery_slug = self.request.query_params.get('gallery')
        if gallery_slug:
            queryset = queryset.filter(gallery__slug=gallery_slug)

        # فیلتر بر اساس تاریخ
        now = timezone.now().date()
        period = self.request.query_params.get('period')

        if period == 'active':
            queryset = queryset.filter(start_date__lte=now, end_date__gte=now)
        elif period == 'upcoming':
            queryset = queryset.filter(start_date__gt=now)
        elif period == 'past':
            queryset = queryset.filter(end_date__lt=now)

        return queryset

    def get_serializer_class(self):
        """انتخاب سریالایزر مناسب بر اساس اکشن"""
        if self.action == 'list':
            return ExhibitionListSerializer
        return ExhibitionDetailSerializer

    def get_permissions(self):
        """تعیین دسترسی‌ها بر اساس اکشن"""
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class AuctionEventViewSet(viewsets.ModelViewSet):
    """ویوست حراجی‌ها"""

    queryset = AuctionEvent.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_live', 'is_online', 'is_featured']
    search_fields = ['title', 'description', 'short_description', 'organizer']
    ordering_fields = ['start_datetime', 'end_datetime', 'created_at']
    ordering = ['-start_datetime']
    lookup_field = 'slug'

    def get_queryset(self):
        """فیلتر کردن حراجی‌ها"""
        queryset = AuctionEvent.objects.all()

        # فیلتر برای کاربران عادی
        if not self.request.user.is_staff:
            queryset = queryset.exclude(status='canceled')

        # فیلتر بر اساس گالری
        gallery_slug = self.request.query_params.get('gallery')
        if gallery_slug:
            queryset = queryset.filter(gallery__slug=gallery_slug)

        # فیلتر بر اساس تاریخ
        now = timezone.now()
        period = self.request.query_params.get('period')

        if period == 'active':
            queryset = queryset.filter(start_datetime__lte=now, end_datetime__gte=now)
        elif period == 'upcoming':
            queryset = queryset.filter(start_datetime__gt=now)
        elif period == 'past':
            queryset = queryset.filter(end_datetime__lt=now)

        return queryset

    def get_serializer_class(self):
        """انتخاب سریالایزر مناسب بر اساس اکشن"""
        if self.action == 'list':
            return AuctionEventListSerializer
        return AuctionEventDetailSerializer

    def get_permissions(self):
        """تعیین دسترسی‌ها بر اساس اکشن"""
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['get'])
    def items(self, request, slug=None):
        """آیتم‌های یک حراجی"""
        auction = self.get_object()
        items = auction.items.all().order_by('lot_number')

        serializer = AuctionItemListSerializer(items, many=True)
        return Response(serializer.data)


class AuctionItemViewSet(viewsets.ModelViewSet):
    """ویوست آیتم‌های حراجی"""

    queryset = AuctionItem.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['auction', 'status']
    ordering_fields = ['lot_number', 'current_bid', 'total_bids']
    ordering = ['lot_number']

    def get_serializer_class(self):
        """انتخاب سریالایزر مناسب بر اساس اکشن"""
        if self.action == 'list':
            return AuctionItemListSerializer
        return AuctionItemDetailSerializer

    def get_permissions(self):
        """تعیین دسترسی‌ها بر اساس اکشن"""
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action == 'place_bid':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['get'])
    def bids(self, request, pk=None):
        """پیشنهادات یک آیتم حراجی"""
        item = self.get_object()

        # فقط ادمین یا صاحب حراجی می‌تواند همه پیشنهادات را ببیند
        if request.user.is_staff or (item.auction.gallery and request.user == item.auction.gallery.owner):
            bids = item.bids.all().order_by('-amount')
            serializer = AuctionBidSerializer(bids, many=True)
            return Response(serializer.data)

        # کاربران عادی فقط پیشنهادات خود و پیشنهاد برنده را می‌بینند
        user_bids = item.bids.filter(user=request.user)
        winner_bid = item.bids.filter(is_winner=True).first()

        result = []
        if winner_bid:
            result.append(winner_bid)

        for bid in user_bids:
            if not bid.is_winner:  # پیشنهاد برنده قبلاً اضافه شده است
                result.append(bid)

        serializer = AuctionBidSerializer(result, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], serializer_class=PlaceBidSerializer)
    def place_bid(self, request):
        """ثبت پیشنهاد قیمت"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item = serializer.validated_data['auction_item']
        amount = serializer.validated_data['amount']

        # ایجاد پیشنهاد قیمت
        bid = AuctionBid.objects.create(
            auction_item=item,
            user=request.user,
            amount=amount
        )

        # بروزرسانی اطلاعات آیتم حراجی
        item.current_bid = amount
        item.total_bids += 1
        item.save()

        return Response(
            AuctionBidSerializer(bid).data,
            status=status.HTTP_201_CREATED
        )


class ExhibitionImageViewSet(viewsets.ModelViewSet):
    """ویوست تصاویر نمایشگاه"""

    queryset = ExhibitionImage.objects.all()
    serializer_class = ExhibitionImageSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order']
    ordering = ['order']

    def get_queryset(self):
        """فیلتر کردن تصاویر بر اساس نمایشگاه"""
        queryset = ExhibitionImage.objects.all()

        exhibition_id = self.request.query_params.get('exhibition')
        if exhibition_id:
            queryset = queryset.filter(exhibition_id=exhibition_id)

        return queryset