# orders/api/serializers.py

from rest_framework import serializers
from orders.models import Cart, CartItem, Order, OrderItem, Wishlist, Coupon
from products.models import ArtProduct
from products.api.serializers import ArtProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """سریالایزر آیتم‌های سبد خرید"""

    product_details = serializers.SerializerMethodField()
    unit_price = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'cart', 'product', 'product_details', 'quantity',
            'unit_price', 'total_price', 'added_at'
        ]
        read_only_fields = ['id', 'cart', 'added_at']

    def get_product_details(self, obj):
        """دریافت جزئیات محصول"""
        return ArtProductListSerializer(obj.product).data


class CartSerializer(serializers.ModelSerializer):
    """سریالایزر سبد خرید"""

    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CartItemCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد آیتم سبد خرید"""

    class Meta:
        model = CartItem
        fields = ['product', 'quantity']

    def validate_product(self, value):
        """اعتبارسنجی محصول"""
        if value.status != 'published':
            raise serializers.ValidationError("این محصول قابل خرید نیست.")

        if value.inventory <= 0:
            raise serializers.ValidationError("این محصول موجود نیست.")

        return value

    def validate_quantity(self, value):
        """اعتبارسنجی تعداد"""
        if value <= 0:
            raise serializers.ValidationError("تعداد باید بزرگتر از صفر باشد.")

        return value

    def validate(self, attrs):
        """اعتبارسنجی کلی"""
        request = self.context.get('request')
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)

        # بررسی موجودی کافی
        if product.inventory < quantity:
            raise serializers.ValidationError(
                {"quantity": f"تعداد درخواستی بیشتر از موجودی است. حداکثر تعداد مجاز: {product.inventory}"}
            )

        return attrs

    def create(self, validated_data):
        """ایجاد یا بروزرسانی آیتم سبد خرید"""
        request = self.context.get('request')
        product = validated_data.get('product')
        quantity = validated_data.get('quantity', 1)

        # دریافت یا ایجاد سبد خرید کاربر
        cart, created = Cart.objects.get_or_create(user=request.user)

        # بررسی وجود محصول در سبد خرید
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            # بروزرسانی تعداد
            cart_item.quantity = quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            # ایجاد آیتم جدید
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )

        return cart_item


class OrderItemSerializer(serializers.ModelSerializer):
    """سریالایزر آیتم‌های سفارش"""

    product_details = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_details', 'product_name',
            'product_price', 'quantity', 'total_price'
        ]
        read_only_fields = ['id', 'order', 'product_name', 'product_price', 'total_price']

    def get_product_details(self, obj):
        """دریافت جزئیات محصول در صورت وجود"""
        if obj.product:
            return {
                'id': obj.product.id,
                'title': obj.product.title,
                'slug': obj.product.slug,
                'image': obj.product.images.filter(is_primary=True).first().image.url if obj.product.images.filter(
                    is_primary=True).exists() else None
            }
        return None


class OrderSerializer(serializers.ModelSerializer):
    """سریالایزر سفارش"""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'order_number', 'status', 'subtotal', 'shipping_fee',
            'tax', 'discount', 'total', 'payment_method', 'is_paid', 'paid_at',
            'shipping_method', 'shipping_name', 'shipping_phone', 'shipping_address',
            'shipping_postal_code', 'shipping_province', 'shipping_city',
            'customer_note', 'admin_note', 'created_at', 'updated_at',
            'shipped_at', 'delivered_at', 'tracking_code', 'items'
        ]
        read_only_fields = [
            'id', 'user', 'order_number', 'subtotal', 'total', 'is_paid',
            'paid_at', 'created_at', 'updated_at', 'shipped_at', 'delivered_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد سفارش"""

    use_user_profile_address = serializers.BooleanField(default=False, write_only=True)
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = [
            'shipping_method', 'shipping_name', 'shipping_phone', 'shipping_address',
            'shipping_postal_code', 'shipping_province', 'shipping_city',
            'customer_note', 'use_user_profile_address', 'coupon_code'
        ]

    def validate_coupon_code(self, value):
        """اعتبارسنجی کد تخفیف"""
        if not value:
            return None

        try:
            coupon = Coupon.objects.get(code=value)
            if not coupon.is_valid:
                raise serializers.ValidationError("کد تخفیف نامعتبر است یا منقضی شده است.")
            return coupon
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("کد تخفیف نامعتبر است.")

    def validate(self, attrs):
        """اعتبارسنجی کلی"""
        request = self.context.get('request')
        user = request.user

        # بررسی استفاده از آدرس پروفایل
        use_profile_address = attrs.pop('use_user_profile_address', False)
        if use_profile_address:
            try:
                profile = user.profile
                attrs['shipping_name'] = f"{profile.first_name_fa} {profile.last_name_fa}".strip()
                attrs['shipping_phone'] = user.phone_number
                attrs['shipping_address'] = profile.address
                attrs['shipping_postal_code'] = profile.postal_code

                # اگر استان و شهر در مدل پروفایل وجود ندارد، می‌توانید این فیلدها را از attrs حذف کنید
                # تا از مقادیر پیش‌فرض استفاده شود
            except:
                raise serializers.ValidationError(
                    {"use_user_profile_address": "اطلاعات پروفایل کاربر کامل نیست."}
                )

        # بررسی وجود سبد خرید و آیتم‌ها
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                raise serializers.ValidationError(
                    {"non_field_errors": "سبد خرید شما خالی است."}
                )
        except Cart.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": "سبد خرید شما خالی است."}
            )

        return attrs


class WishlistSerializer(serializers.ModelSerializer):
    """سریالایزر لیست علاقه‌مندی‌ها"""

    products = ArtProductListSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CouponSerializer(serializers.ModelSerializer):
    """سریالایزر کد تخفیف"""

    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_amount', 'discount_percent',
            'min_purchase', 'max_usage', 'usage_count', 'is_active',
            'valid_from', 'valid_to', 'is_valid'
        ]
        read_only_fields = ['id', 'usage_count', 'is_valid']