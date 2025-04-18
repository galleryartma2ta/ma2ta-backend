from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from products.models import Category, ArtStyle, Product, Review
from .serializers import (
    CategorySerializer, ArtStyleSerializer,
    ProductListSerializer, ProductDetailSerializer, ReviewSerializer
)
from .filters import ProductFilter


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        parent_slug = self.request.query_params.get('parent', None)

        if parent_slug == 'root':
            return queryset.filter(parent=None)
        elif parent_slug:
            return queryset.filter(parent__slug=parent_slug)

        return queryset


class ArtStyleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ArtStyle.objects.all()
    serializer_class = ArtStyleSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description', 'artist__artistic_name']
    ordering_fields = ['price', 'created_at', 'title']
    ordering = ['-created_at']
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def review(self, request, slug=None):
        product = self.get_object()
        serializer = ReviewSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True)
        page = self.paginate_queryset(reviews)

        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)