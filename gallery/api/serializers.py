# gallery/api/serializers.py

from rest_framework import serializers
from gallery.models import (
    Gallery, GalleryArtist, Exhibition, ExhibitionImage,
    AuctionEvent, AuctionItem, AuctionBid
)
from artists.api.serializers import ArtistListSerializer
from products.api.serializers import ArtProductListSerializer


class GalleryListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست گالری‌ها"""

    class Meta:
        model = Gallery
        fields = [
            'id', 'name', 'slug', 'short_description', 'logo',
            'banner', 'city', 'province', 'is_verified', 'featured'
        ]
        read_only_fields = ['id', 'slug']


class GalleryArtistSerializer(serializers.ModelSerializer):
    """سریالایزر ارتباط گالری و هنرمند"""

    artist_details = serializers.SerializerMethodField()

    class Meta:
        model = GalleryArtist
        fields = [
            'id', 'gallery', 'artist', 'artist_details', 'start_date',
            'end_date', 'is_active', 'description'
        ]
        read_only_fields = ['id']

    def get_artist_details(self, obj):
        """دریافت جزئیات هنرمند"""
        return ArtistListSerializer(obj.artist).data


class GalleryDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات گالری"""

    artists = serializers.SerializerMethodField()
    active_exhibitions_count = serializers.SerializerMethodField()
    upcoming_auctions_count = serializers.SerializerMethodField()

    class Meta:
        model = Gallery
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'owner', 'logo', 'banner', 'address', 'city', 'province',
            'postal_code', 'phone', 'email', 'website', 'instagram',
            'twitter', 'is_verified', 'is_active', 'featured',
            'foundation_year', 'working_hours', 'artists',
            'active_exhibitions_count', 'upcoming_auctions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_artists(self, obj):
        """دریافت هنرمندان گالری"""
        gallery_artists = GalleryArtist.objects.filter(
            gallery=obj,
            is_active=True
        )
        return GalleryArtistSerializer(gallery_artists, many=True).data

    def get_active_exhibitions_count(self, obj):
        """تعداد نمایشگاه‌های فعال"""
        return obj.exhibitions.filter(status='active').count()

    def get_upcoming_auctions_count(self, obj):
        """تعداد حراجی‌های آینده"""
        return obj.auctions.filter(status='upcoming').count()


class ExhibitionImageSerializer(serializers.ModelSerializer):
    """سریالایزر تصاویر نمایشگاه"""

    class Meta:
        model = ExhibitionImage
        fields = ['id', 'exhibition', 'image', 'title', 'description', 'order']
        read_only_fields = ['id']


class ExhibitionListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست نمایشگاه‌ها"""

    gallery_name = serializers.ReadOnlyField(source='gallery.name')
    artists_count = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Exhibition
        fields = [
            'id', 'title', 'slug', 'short_description', 'gallery',
            'gallery_name', 'start_date', 'end_date', 'poster',
            'is_virtual', 'status', 'is_featured', 'artists_count', 'is_active'
        ]
        read_only_fields = ['id', 'slug']

    def get_artists_count(self, obj):
        """تعداد هنرمندان نمایشگاه"""
        return obj.artists.count()


class ExhibitionDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات نمایشگاه"""

    gallery = GalleryListSerializer(read_only=True)
    artists = ArtistListSerializer(many=True, read_only=True)
    products = ArtProductListSerializer(many=True, read_only=True)
    images = ExhibitionImageSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Exhibition
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'gallery', 'curator', 'artists', 'products', 'start_date', 'end_date',
            'opening_time', 'closing_time', 'is_virtual', 'has_virtual_tour',
            'virtual_tour_url', 'poster', 'banner', 'status', 'is_featured',
            'is_active', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class AuctionBidSerializer(serializers.ModelSerializer):
    """سریالایزر پیشنهاد قیمت در حراجی"""

    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = AuctionBid
        fields = [
            'id', 'auction_item', 'user', 'user_email', 'amount',
            'placed_at', 'is_winner', 'is_auto'
        ]
        read_only_fields = ['id', 'user', 'placed_at', 'is_winner']


class AuctionItemListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست آیتم‌های حراجی"""

    product_details = serializers.SerializerMethodField()
    bids_count = serializers.SerializerMethodField()

    class Meta:
        model = AuctionItem
        fields = [
            'id', 'auction', 'product', 'product_details', 'lot_number',
            'start_price', 'current_bid', 'total_bids', 'bids_count',
            'status', 'display_order'
        ]
        read_only_fields = ['id', 'current_bid', 'total_bids']

    def get_product_details(self, obj):
        """دریافت جزئیات محصول"""
        return {
            'id': obj.product.id,
            'title': obj.product.title,
            'slug': obj.product.slug,
            'artist': f"{obj.product.artist.first_name} {obj.product.artist.last_name}",
            'image': obj.product.images.filter(is_primary=True).first().image.url if obj.product.images.filter(
                is_primary=True).exists() else None,
            'category': obj.product.category.name,
        }

    def get_bids_count(self, obj):
        """تعداد پیشنهادات"""
        return obj.bids.count()


class AuctionItemDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات آیتم حراجی"""

    product = ArtProductListSerializer(read_only=True)
    bids = serializers.SerializerMethodField()

    class Meta:
        model = AuctionItem
        fields = [
            'id', 'auction', 'product', 'lot_number', 'start_price',
            'reserve_price', 'estimated_price_min', 'estimated_price_max',
            'current_bid', 'winning_bid', 'total_bids', 'status',
            'display_order', 'hammer_time', 'bids'
        ]
        read_only_fields = ['id', 'current_bid', 'winning_bid', 'total_bids', 'hammer_time']

    def get_bids(self, obj):
        """دریافت پیشنهادات قیمت"""
        # فقط برای ادمین یا صاحب حراجی همه پیشنهادات نمایش داده می‌شود
        request = self.context.get('request')
        if request and (request.user.is_staff or request.user == obj.auction.gallery.owner):
            return AuctionBidSerializer(obj.bids.order_by('-amount'), many=True).data

        # برای کاربران عادی فقط پیشنهادات برنده و خودشان نمایش داده می‌شود
        user_bids = obj.bids.filter(user=request.user) if request and request.user.is_authenticated else []
        winner_bid = obj.bids.filter(is_winner=True).first()

        result = []
        if winner_bid:
            result.append(AuctionBidSerializer(winner_bid).data)

        for bid in user_bids:
            if not bid.is_winner:  # پیشنهاد برنده قبلاً اضافه شده است
                result.append(AuctionBidSerializer(bid).data)

        return result


class AuctionEventListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست حراجی‌ها"""

    gallery_name = serializers.ReadOnlyField(source='gallery.name')
    items_count = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = AuctionEvent
        fields = [
            'id', 'title', 'slug', 'short_description', 'gallery',
            'gallery_name', 'organizer', 'start_datetime', 'end_datetime',
            'is_live', 'is_online', 'image', 'status', 'is_featured',
            'items_count', 'is_active'
        ]
        read_only_fields = ['id', 'slug']

    def get_items_count(self, obj):
        """تعداد آیتم‌های حراجی"""
        return obj.items.count()


class AuctionEventDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات حراجی"""

    gallery = GalleryListSerializer(read_only=True)
    items = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = AuctionEvent
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'gallery', 'organizer', 'start_datetime', 'end_datetime',
            'is_live', 'is_online', 'live_url', 'image', 'banner',
            'status', 'is_featured', 'is_active', 'commission_rate',
            'registration_required', 'registration_fee', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_items(self, obj):
        """دریافت آیتم‌های حراجی"""
        items = obj.items.all().order_by('lot_number')
        return AuctionItemListSerializer(items, many=True).data


class PlaceBidSerializer(serializers.Serializer):
    """سریالایزر ثبت پیشنهاد قیمت"""

    auction_item_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(required=True, max_digits=12, decimal_places=0)

    def validate_amount(self, value):
        """اعتبارسنجی مبلغ پیشنهادی"""
        if value <= 0:
            raise serializers.ValidationError("مبلغ پیشنهادی باید بزرگتر از صفر باشد.")
        return value

    def validate(self, attrs):
        """اعتبارسنجی داده‌ها"""
        item_id = attrs.get('auction_item_id')
        amount = attrs.get('amount')

        try:
            item = AuctionItem.objects.get(id=item_id)

            # بررسی وضعیت آیتم حراجی
            if item.status != 'active':
                raise serializers.ValidationError({"auction_item_id": "این آیتم حراجی فعال نیست."})

            # بررسی وضعیت حراجی
            if item.auction.status != 'active':
                raise serializers.ValidationError({"auction_item_id": "حراجی مورد نظر فعال نیست."})

            # بررسی مبلغ پیشنهادی
            if item.current_bid:
                min_allowed_bid = item.current_bid * 1.05  # حداقل 5% بیشتر از پیشنهاد قبلی
                if amount < min_allowed_bid:
                    raise serializers.ValidationError(
                        {"amount": f"مبلغ پیشنهادی باید حداقل {min_allowed_bid} تومان باشد (5% بیشتر از پیشنهاد فعلی)."}
                    )
            elif amount < item.start_price:
                raise serializers.ValidationError(
                    {"amount": f"مبلغ پیشنهادی باید حداقل برابر با قیمت شروع ({item.start_price} تومان) باشد."}
                )

            # ذخیره آیتم در اعتبارسنجی‌ها
            attrs['auction_item'] = item

            return attrs
        except AuctionItem.DoesNotExist:
            raise serializers.ValidationError({"auction_item_id": "آیتم حراجی مورد نظر یافت نشد."})