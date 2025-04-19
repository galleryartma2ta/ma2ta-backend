# core/mixins/serializers.py

from rest_framework import serializers
from django.utils.translation import get_language
from django.conf import settings


class DynamicFieldsMixin:
    """
    میکسین برای پشتیبانی از فیلدهای پویا در سریالایزرها.
    با این میکسین می‌توان فیلدهای مورد نیاز را با پارامتر fields مشخص کرد.

    مثال: ?fields=id,title,created_at
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            # اگر فیلدها به صورت رشته ارسال شده‌اند، آنها را تقسیم کنید
            if isinstance(fields, str):
                fields = fields.split(',')

            # حذف فیلدهای خارج از لیست
            existing = set(self.fields)
            for field_name in existing - set(fields):
                self.fields.pop(field_name)

        if exclude is not None:
            # اگر فیلدهای استثنا به صورت رشته ارسال شده‌اند، آنها را تقسیم کنید
            if isinstance(exclude, str):
                exclude = exclude.split(',')

            # حذف فیلدهای مشخص شده برای استثنا
            for field_name in set(exclude):
                if field_name in self.fields:
                    self.fields.pop(field_name)


class HyperlinkedModelSerializerMixin:
    """
    میکسین برای اضافه کردن لینک‌های HATEOAS به سریالایزرها.
    """

    def get_links(self, obj):
        """
        تولید لینک‌های مرتبط با شیء.
        کلاس‌های فرزند باید این متد را پیاده‌سازی کنند.
        """
        request = self.context.get('request')
        links = {}

        if request is not None:
            return links

        return links

    def to_representation(self, instance):
        """
        اضافه کردن فیلد links به نمایش شیء.
        """
        representation = super().to_representation(instance)
        representation['links'] = self.get_links(instance)
        return representation


class ReadWriteSerializerMixin:
    """
    میکسین برای استفاده از سریالایزرهای متفاوت برای خواندن و نوشتن.

    این میکسین به شما اجازه می‌دهد تا دو سریالایزر متفاوت برای عملیات‌های GET و POST/PUT تعریف کنید.
    """
    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return self.get_write_serializer_class()
        return self.get_read_serializer_class()

    def get_read_serializer_class(self):
        assert self.read_serializer_class is not None, (
            f"'{self.__class__.__name__}' باید دارای 'read_serializer_class' باشد."
        )
        return self.read_serializer_class

    def get_write_serializer_class(self):
        assert self.write_serializer_class is not None, (
            f"'{self.__class__.__name__}' باید دارای 'write_serializer_class' باشد."
        )
        return self.write_serializer_class


class TranslationMixin:
    """
    میکسین برای پشتیبانی از ترجمه‌ها در سریالایزرها.
    این میکسین با مدل‌هایی که از TranslatableMixin استفاده می‌کنند، کار می‌کند.
    """

    def to_representation(self, instance):
        """
        ترجمه فیلدهای قابل ترجمه بر اساس زبان فعلی.
        """
        representation = super().to_representation(instance)

        # اگر مدل از TranslatableMixin استفاده نمی‌کند، به همان شکل برگردان
        if not hasattr(instance, 'TRANSLATABLE_FIELDS') or not hasattr(instance, 'get_translation'):
            return representation

        # زبان فعلی
        current_language = get_language() or settings.LANGUAGE_CODE

        # اگر زبان فعلی، زبان پیش‌فرض است، نیازی به ترجمه نیست
        if current_language == settings.LANGUAGE_CODE:
            return representation

        # ترجمه فیلدهای قابل ترجمه
        for field_name in instance.TRANSLATABLE_FIELDS:
            if field_name in representation:
                translated_value = instance.get_translation(field_name, current_language)
                if translated_value:
                    representation[field_name] = translated_value

        return representation