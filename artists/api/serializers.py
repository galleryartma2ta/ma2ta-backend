from rest_framework import serializers
from artists.models import Artist, Education, Exhibition, Award
from products.models import Product
from products.api.serializers import ProductListSerializer


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'institution', 'degree', 'field_of_study', 'start_year', 'end_year']


class ExhibitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exhibition
        fields = ['id', 'title', 'gallery', 'location', 'year', 'type', 'description']


class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = ['id', 'title', 'organization', 'year', 'description']


class ArtistListSerializer(serializers.ModelSerializer):
    artwork_count = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = [
            'id', 'artistic_name', 'slug', 'nationality',
            'birth_year', 'is_featured', 'is_verified', 'artwork_count'
        ]

    def get_artwork_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ArtistDetailSerializer(serializers.ModelSerializer):
    education = EducationSerializer(many=True, read_only=True)
    exhibitions = ExhibitionSerializer(many=True, read_only=True)
    awards = AwardSerializer(many=True, read_only=True)
    artworks = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = [
            'id', 'artistic_name', 'slug', 'nationality',
            'birth_year', 'death_year', 'bio', 'artist_statement',
            'website', 'instagram', 'twitter',
            'is_featured', 'is_verified', 'created_at',
            'education', 'exhibitions', 'awards', 'artworks'
        ]

    def get_artworks(self, obj):
        # Get first 8 active artworks for preview
        products = obj.products.filter(is_active=True)[:8]
        return ProductListSerializer(products, many=True, context=self.context).data