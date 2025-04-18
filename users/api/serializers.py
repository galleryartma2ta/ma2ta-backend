from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Profile, Address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_artist', 'is_gallery_owner', 'date_joined']
        read_only_fields = ['email', 'is_artist', 'is_gallery_owner', 'date_joined']


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = Profile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'first_name_fa', 'last_name_fa', 'gender',
            'birth_date', 'phone_number', 'profile_image', 'bio'
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Update User model fields
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        user.save()

        # Update Profile model fields
        return super().update(instance, validated_data)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'title', 'province', 'city',
            'postal_code', 'address', 'is_default'
        ]

    def create(self, validated_data):
        # If this address is set as default, unset other defaults
        user = self.context['request'].user
        if validated_data.get('is_default', False):
            Address.objects.filter(user=user, is_default=True).update(is_default=False)

        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # If this address is set as default, unset other defaults
        if validated_data.get('is_default', False) and not instance.is_default:
            Address.objects.filter(user=instance.user, is_default=True).update(is_default=False)

        return super().update(instance, validated_data)