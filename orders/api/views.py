# orders/api/views.py

from rest_framework import viewsets, mixins, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, F
from django.db import transaction
import uuid

from orders.models import Cart, CartItem, Order, OrderItem, Wishlist, Coupon
from products.models import ArtProduct
from .serializers import (
    CartSerializer, CartItemSerializer, CartItemCreateSerializer,
    OrderSerializer, OrderCreateSerializer, OrderItemSerializer,
    WishlistSerializer, CouponSerializer
)


class CartViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """ویوست سبد خرید"""

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """دریافت یا ایجاد سبد خرید کاربر"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'], serializer_class=CartItemCreateSerializer)
    def add_item(self, request):
        """افزودن آیتم به سبد خرید"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        # بازگرداندن اطلاعات آیتم جدید به همراه جزئیات محصول
        return Response(
            CartItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """حذف آیتم از سبد خرید"""
        try:
            cart = self.get_object()
            item_id = request.data.get('item_id')

            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()

            return Response(
                {"message": "آیتم با موفقیت از سبد خرید حذف شد."},
                status=status.HTTP_200_OK
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "آیتم مورد نظر در سبد خرید شما یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        """بروزرسانی تعداد آیتم سبد خرید"""
        try:
            cart = self.get_object()
            item_id = request.data.get('item_id')
            quantity = request.data.get('quantity', 1)

            # اعتبارسنجی تعداد
            if quantity <= 0:
                return Response(
                    {"error": "تعداد باید بزرگتر از صفر باشد."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item = CartItem.objects.get(id=item_id, cart=cart)

            # بررسی موجودی کافی
            if item.product.inventory < quantity:
                return Response(
                    {"error": f"تعداد درخواستی بیشتر از موجودی است. حداکثر تعداد مجاز: {item.product.inventory}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item.quantity = quantity
            item.save()

            return Response(
                CartItemSerializer(item).data,
                status=status.HTTP_200_OK
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "آیتم مورد نظر در سبد خرید شما یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """پاک کردن سبد خرید"""
        cart = self.get_object()
        cart.clear()

        return Response(
            {"message": "سبد خرید با موفقیت خالی شد."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def apply_coupon(self, request):
        """اعمال کد تخفیف"""
        coupon_code = request.data.get('coupon_code')

        try:
            coupon = Coupon.objects.get(code=coupon_code)

            # بررسی معتبر بودن کد تخفیف
            if not coupon.is_valid:
                return Response(
                    {"error": "کد تخفیف نامعتبر است یا منقضی شده است."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # بررسی حداقل مبلغ خرید
            cart = self.get_object()
            cart_total = cart.total_price

            if cart_total < coupon.min_purchase:
                return Response(
                    {"error": f"حداقل مبلغ برای استفاده از این کد تخفیف {coupon.min_purchase} تومان است."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # اینجا می‌توانید کد تخفیف را در سشن یا دیتابیس ذخیره کنید
            # برای سادگی، فعلاً فقط اطلاعات تخفیف را برمی‌گردانیم

            discount_amount = coupon.discount_amount
            if coupon.discount_percent:
                discount_amount = (cart_total * coupon.discount_percent) / 100

            return Response({
                "coupon": CouponSerializer(coupon).data,
                "discount_amount": discount_amount,
                "cart_total_after_discount": cart_total - discount_amount
            })

        except Coupon.DoesNotExist:
            return Response(
                {"error": "کد تخفیف نامعتبر است."},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderViewSet(viewsets.ModelViewSet):
    """ویوست سفارشات"""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """فیلتر کردن سفارشات بر اساس کاربر"""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get_serializer_class(self):
        """انتخاب سریالایزر مناسب بر اساس اکشن"""
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """ایجاد سفارش جدید از سبد خرید"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # دریافت کاربر و سبد خرید
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
            cart_items = cart.items.select_related('product').all()

            if not cart_items.exists():
                return Response(
                    {"error": "سبد خرید شما خالی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Cart.DoesNotExist:
            return Response(
                {"error": "سبد خرید شما خالی است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # بررسی و اعمال کد تخفیف
        coupon = serializer.validated_data.pop('coupon_code', None)
        discount_amount = 0
        if coupon:
            cart_total = cart.total_price
            if coupon.discount_amount:
                discount_amount = coupon.discount_amount
            elif coupon.discount_percent:
                discount_amount = (cart_total * coupon.discount_percent) / 100

            # افزایش تعداد استفاده از کد تخفیف
            coupon.usage_count += 1
            coupon.save()

        # محاسبه قیمت‌ها
        subtotal = cart.total_price
        shipping_fee = 0  # می‌توانید بر اساس روش ارسال محاسبه کنید
        tax = 0  # می‌توانید محاسبه مالیات را اضافه کنید
        total = subtotal + shipping_fee + tax - discount_amount

        # ایجاد سفارش
        order = Order.objects.create(
            user=user,
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            status='pending_payment',
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            discount=discount_amount,
            total=total,
            **serializer.validated_data
        )

        # ایجاد آیتم‌های سفارش
        for cart_item in cart_items:
            # بررسی موجودی
            if cart_item.product.inventory < cart_item.quantity:
                # در صورت عدم موجودی کافی، سفارش را لغو می‌کنیم
                order.delete()
                return Response(
                    {"error": f"محصول '{cart_item.product.title}' به تعداد کافی موجود نیست."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ایجاد آیتم سفارش
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.title,
                product_price=cart_item.product.current_price,
                quantity=cart_item.quantity,
                total_price=cart_item.total_price
            )

            # کاهش موجودی محصول
            cart_item.product.inventory -= cart_item.quantity
            cart_item.product.save()

        # خالی کردن سبد خرید
        cart.clear()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو سفارش"""
        order = self.get_object()

        # بررسی امکان لغو سفارش
        if not order.can_cancel:
            return Response(
                {"error": "این سفارش قابل لغو نیست."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # لغو سفارش
        order.status = 'canceled'
        order.save()

        # برگرداندن موجودی محصولات
        for item in order.items.all():
            if item.product:
                item.product.inventory += item.quantity
                item.product.save()

        return Response(
            {"message": "سفارش با موفقیت لغو شد."},
            status=status.HTTP_200_OK
        )


class WishlistViewSet(viewsets.GenericViewSet):
    """ویوست لیست علاقه‌مندی‌ها"""

    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """دریافت یا ایجاد لیست علاقه‌مندی‌های کاربر"""
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

    @action(detail=False, methods=['get'])
    def items(self, request):
        """نمایش آیتم‌های لیست علاقه‌مندی‌ها"""
        wishlist = self.get_object()
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        """افزودن محصول به لیست علاقه‌مندی‌ها"""
        wishlist = self.get_object()
        product_id = request.data.get('product_id')

        try:
            product = ArtProduct.objects.get(id=product_id, status='published')
            wishlist.products.add(product)

            return Response(
                {"message": "محصول با موفقیت به لیست علاقه‌مندی‌ها اضافه شد."},
                status=status.HTTP_200_OK
            )
        except ArtProduct.DoesNotExist:
            return Response(
                {"error": "محصول مورد نظر یافت نشد یا قابل دسترسی نیست."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def remove(self, request):
        """حذف محصول از لیست علاقه‌مندی‌ها"""
        wishlist = self.get_object()
        product_id = request.data.get('product_id')

        try:
            product = ArtProduct.objects.get(id=product_id)
            wishlist.products.remove(product)

            return Response(
                {"message": "محصول با موفقیت از لیست علاقه‌مندی‌ها حذف شد."},
                status=status.HTTP_200_OK
            )
        except ArtProduct.DoesNotExist:
            return Response(
                {"error": "محصول مورد نظر یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def check(self, request):
        """بررسی وجود محصول در لیست علاقه‌مندی‌ها"""
        wishlist = self.get_object()
        product_id = request.query_params.get('product_id')

        try:
            product = ArtProduct.objects.get(id=product_id)
            is_in_wishlist = wishlist.products.filter(id=product_id).exists()

            return Response(
                {"is_in_wishlist": is_in_wishlist},
                status=status.HTTP_200_OK
            )
        except ArtProduct.DoesNotExist:
            return Response(
                {"error": "محصول مورد نظر یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """پاک کردن لیست علاقه‌مندی‌ها"""
        wishlist = self.get_object()
        wishlist.products.clear()

        return Response(
            {"message": "لیست علاقه‌مندی‌ها با موفقیت خالی شد."},
            status=status.HTTP_200_OK
        )


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """ویوست کدهای تخفیف (فقط برای ادمین در پنل مدیریت)"""

    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'description']
    ordering_fields = ['valid_from', 'valid_to', 'is_active', 'usage_count']
    ordering = ['-valid_from']

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def validate(self, request):
        """اعتبارسنجی کد تخفیف"""
        coupon_code = request.data.get('coupon_code')

        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if not coupon.is_valid:
                return Response(
                    {"is_valid": False, "message": "کد تخفیف نامعتبر است یا منقضی شده است."},
                    status=status.HTTP_200_OK
                )

            return Response({
                "is_valid": True,
                "coupon": CouponSerializer(coupon).data
            })

        except Coupon.DoesNotExist:
            return Response(
                {"is_valid": False, "message": "کد تخفیف نامعتبر است."},
                status=status.HTTP_200_OK
            )