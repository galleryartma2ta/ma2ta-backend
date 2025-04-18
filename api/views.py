# api/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_overview(request, format=None):
    """
    API overview - نمای کلی از API
    """
    api_endpoints = {
        'Authentication': {
            'Login': reverse('token_obtain_pair', request=request, format=format),
            'Refresh Token': reverse('token_refresh', request=request, format=format),
        },
        'Users': {
            'Register': reverse('user-register', request=request, format=format),
            'Profile': reverse('user-profile', request=request, format=format),
        },
        'Products': {
            'List': reverse('product-list', request=request, format=format),
            'Categories': reverse('category-list', request=request, format=format),
        },
        'Artists': {
            'List': reverse('artist-list', request=request, format=format),
        },
        'Gallery': {
            'Exhibitions': reverse('exhibition-list', request=request, format=format),
        },
        'Orders': {
            'Cart': reverse('cart-detail', request=request, format=format),
            'Orders': reverse('order-list', request=request, format=format),
        },
        'Blog': {
            'Posts': reverse('post-list', request=request, format=format),
        },
    }

    return Response(api_endpoints)