from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from artists.models import Artist
from .serializers import ArtistListSerializer, ArtistDetailSerializer
from products.api.serializers import ProductListSerializer


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artist.objects.filter(is_verified=True)
    serializer_class = ArtistListSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['artistic_name', 'bio', 'nationality']
    ordering_fields = ['created_at', 'artistic_name']
    ordering = ['-is_featured', 'artistic_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ArtistListSerializer
        return ArtistDetailSerializer

    @action(detail=True, methods=['get'])
    def artworks(self, request, slug=None):
        artist = self.get_object()
        products = artist.products.filter(is_active=True)

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_artists = self.get_queryset().filter(is_featured=True)[:8]
        serializer = self.get_serializer(featured_artists, many=True)
        return Response(serializer.data)