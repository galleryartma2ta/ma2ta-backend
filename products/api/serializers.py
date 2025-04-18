from rest_framework import serializers
from products.models import Category, ArtStyle, Product, ProductImage, Review
from artists.models import Artist


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'description', 'is_active']


class ArtStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtStyle
        fields = ['id', 'name', 'slug', 'description']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'alt_text']


class ArtistMiniSerializer(serializers.ModelSerializer):
    """Simplified Artist serializer for use in ProductSerializer"""

    class Meta:
        model = Artist
        fields = ['id', 'artistic_name', 'slug']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view"""
    artist = ArtistMiniSerializer(read_only=True)
    category = serializers.StringRelatedField()
    art_style = serializers.StringRelatedField()
    primary_image = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'artist', 'category', 'art_style',
            'price', 'discount_price', 'availability', 'is_featured',
            'primary_image', 'avg_rating', 'created_at'
        ]

    def get_primary_image(self, obj):
        try:
            primary_image = obj.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = obj.images.first()
            if primary_image:
                return ProductImageSerializer(primary_image).data
            return None
        except:
            return None

    def get_avg_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return None


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['user']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email.split('@')[0]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed Product serializer"""
    artist = ArtistMiniSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    art_style = ArtStyleSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'artist', 'category', 'art_style',
            'description', 'price', 'discount_price', 'creation_year',
            'width', 'height', 'depth', 'weight', 'materials', 'technique',
            'availability', 'is_original', 'is_featured', 'stock_quantity',
            'images', 'reviews', 'avg_rating', 'review_count', 'created_at'
        ]

    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True)[:5]  # Get first 5 approved reviews
        return ReviewSerializer(reviews, many=True).data

    def get_avg_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return None

    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()