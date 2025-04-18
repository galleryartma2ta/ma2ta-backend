import django_filters
from products.models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    style = django_filters.CharFilter(field_name='art_style__slug')
    artist = django_filters.CharFilter(field_name='artist__slug')
    availability = django_filters.CharFilter(field_name='availability')
    is_original = django_filters.BooleanFilter(field_name='is_original')

    # Filter by dimensions
    min_width = django_filters.NumberFilter(field_name="width", lookup_expr='gte')
    max_width = django_filters.NumberFilter(field_name="width", lookup_expr='lte')
    min_height = django_filters.NumberFilter(field_name="height", lookup_expr='gte')
    max_height = django_filters.NumberFilter(field_name="height", lookup_expr='lte')

    # Filter by creation year
    min_year = django_filters.NumberFilter(field_name="creation_year", lookup_expr='gte')
    max_year = django_filters.NumberFilter(field_name="creation_year", lookup_expr='lte')

    class Meta:
        model = Product
        fields = [
            'min_price', 'max_price', 'category', 'style', 'artist',
            'availability', 'is_original', 'is_featured',
            'min_width', 'max_width', 'min_height', 'max_height',
            'min_year', 'max_year'
        ]