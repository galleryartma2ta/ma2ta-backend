# core/behaviors/translatable.py

import copy
from django.db import models
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class TranslatableMixin(models.Model):
    """
    میکسین برای پشتیبانی از چندزبانه‌سازی مدل‌ها.

    این میکسین به مدل‌ها امکان ذخیره و بازیابی ترجمه‌های فیلدهای متنی را می‌دهد.
    ترجمه‌ها به صورت دیکشنری در یک فیلد JSONField ذخیره می‌شوند.

    نمونه استفاده:
    ```python
    class Article(TranslatableMixin, models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()

        # فیلدهایی که باید ترجمه شوند
        TRANSLATABLE_FIELDS = ['title', 'content']
    ```

    برای تنظیم ترجمه:
    ```python
    article = Article.objects.get(pk=1)
    article.set_translation('title', 'Title in English', 'en')
    article.set_translation('content', 'Content in English', 'en')
    article.save()
    ```

    برای دریافت ترجمه:
    ```python
    article = Article.objects.get(pk=1)
    title_en = article.get_translation('title', 'en')
    content_en = article.get_translation('content', 'en')
    ```
    """

    # دیکشنری فیلدهای ترجمه شده (به صورت { 'en': { 'title': 'English Title', ... }, ... })
    translations = models.JSONField(
        _("ترجمه‌ها"),
        default=dict,
        blank=True,
        help_text=_("ترجمه‌های فیلدهای مدل در زبان‌های مختلف")
    )

    # فیلدهایی که باید ترجمه شوند (باید در کلاس فرزند تعریف شود)
    TRANSLATABLE_FIELDS = []

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ذخیره مقدار اولیه translations برای مقایسه در زمان ذخیره
        self._initial_translations = copy.deepcopy(self.translations)

    def get_translation(self, field_name, language=None):
        """
        دریافت ترجمه یک فیلد در زبان مشخص

        Args:
            field_name: نام فیلد
            language: کد زبان (اختیاری، اگر ارائه نشود، زبان فعلی استفاده می‌شود)

        Returns:
            مقدار ترجمه شده فیلد در زبان مشخص، یا مقدار اصلی فیلد اگر ترجمه وجود نداشته باشد
        """
        # بررسی معتبر بودن فیلد
        if field_name not in self.TRANSLATABLE_FIELDS:
            return getattr(self, field_name)

        # تنظیم زبان پیش‌فرض اگر ارائه نشده
        if language is None:
            language = get_language() or settings.LANGUAGE_CODE

        # اگر زبان درخواستی، زبان پیش‌فرض است، مقدار اصلی فیلد را برگردان
        if language == settings.LANGUAGE_CODE:
            return getattr(self, field_name)

        # بررسی وجود ترجمه
        translations_dict = self.translations

        if not translations_dict:
            return getattr(self, field_name)

        # دریافت ترجمه‌های زبان درخواستی
        language_dict = translations_dict.get(language, {})

        # دریافت ترجمه فیلد درخواستی
        translation = language_dict.get(field_name)

        # اگر ترجمه وجود نداشت، مقدار اصلی فیلد را برگردان
        if not translation:
            return getattr(self, field_name)

        return translation

    def set_translation(self, field_name, value, language=None):
        """
        تنظیم ترجمه یک فیلد در زبان مشخص

        Args:
            field_name: نام فیلد
            value: مقدار ترجمه شده
            language: کد زبان (اختیاری، اگر ارائه نشود، زبان فعلی استفاده می‌شود)

        Returns:
            نمونه مدل به‌روزرسانی شده

        Raises:
            ValidationError: اگر فیلد قابل ترجمه نباشد
        """
        # بررسی معتبر بودن فیلد
        if field_name not in self.TRANSLATABLE_FIELDS:
            raise ValidationError(f"فیلد {field_name} قابل ترجمه نیست.")

        # تنظیم زبان پیش‌فرض اگر ارائه نشده
        if language is None:
            language = get_language() or settings.LANGUAGE_CODE

        # اگر زبان درخواستی، زبان پیش‌فرض است، مقدار اصلی فیلد را به‌روزرسانی کن
        if language == settings.LANGUAGE_CODE:
            setattr(self, field_name, value)
            return self

        # کپی دیکشنری ترجمه‌ها برای جلوگیری از تغییر مستقیم
        translations_dict = copy.deepcopy(self.translations)

        if translations_dict is None:
            translations_dict = {}

        # اطمینان از وجود دیکشنری زبان
        if language not in translations_dict:
            translations_dict[language] = {}

        # تنظیم ترجمه جدید
        translations_dict[language][field_name] = value

        # به‌روزرسانی فیلد translations
        self.translations = translations_dict

        return self

    def set_translations(self, field_name, translations_dict):
        """
        تنظیم ترجمه‌های یک فیلد در چندین زبان

        Args:
            field_name: نام فیلد
            translations_dict: دیکشنری ترجمه‌ها به صورت {language_code: translated_value, ...}

        Returns:
            نمونه مدل به‌روزرسانی شده

        Raises:
            ValidationError: اگر فیلد قابل ترجمه نباشد
        """
        # بررسی معتبر بودن فیلد
        if field_name not in self.TRANSLATABLE_FIELDS:
            raise ValidationError(f"فیلد {field_name} قابل ترجمه نیست.")

        # تنظیم ترجمه‌ها برای هر زبان
        for language, value in translations_dict.items():
            self.set_translation(field_name, value, language)

        return self

    def remove_translation(self, field_name, language=None):
        """
        حذف ترجمه یک فیلد در زبان مشخص

        Args:
            field_name: نام فیلد
            language: کد زبان (اختیاری، اگر ارائه نشود، زبان فعلی استفاده می‌شود)

        Returns:
            نمونه مدل به‌روزرسانی شده

        Raises:
            ValidationError: اگر فیلد قابل ترجمه نباشد
        """
        # بررسی معتبر بودن فیلد
        if field_name not in self.TRANSLATABLE_FIELDS:
            raise ValidationError(f"فیلد {field_name} قابل ترجمه نیست.")

        # تنظیم زبان پیش‌فرض اگر ارائه نشده
        if language is None:
            language = get_language() or settings.LANGUAGE_CODE

        # اگر زبان درخواستی، زبان پیش‌فرض است، حذف ترجمه منطقی نیست
        if language == settings.LANGUAGE_CODE:
            return self

        # کپی دیکشنری ترجمه‌ها برای جلوگیری از تغییر مستقیم
        translations_dict = copy.deepcopy(self.translations)

        if translations_dict is None or language not in translations_dict:
            return self

        # حذف ترجمه فیلد
        language_dict = translations_dict[language]

        if field_name in language_dict:
            del language_dict[field_name]

        # اگر دیکشنری زبان خالی است، آن را حذف کن
        if not language_dict:
            del translations_dict[language]

        # به‌روزرسانی فیلد translations
        self.translations = translations_dict

        return self

    def get_all_translations(self, field_name):
        """
        دریافت تمام ترجمه‌های یک فیلد در تمام زبان‌ها

        Args:
            field_name: نام فیلد

        Returns:
            دیکشنری ترجمه‌ها به صورت {language_code: translated_value, ...}

        Raises:
            ValidationError: اگر فیلد قابل ترجمه نباشد
        """
        # بررسی معتبر بودن فیلد
        if field_name not in self.TRANSLATABLE_FIELDS:
            raise ValidationError(f"فیلد {field_name} قابل ترجمه نیست.")

        # دیکشنری ترجمه‌ها
        result = {settings.LANGUAGE_CODE: getattr(self, field_name)}

        if not self.translations:
            return result

        # اضافه کردن ترجمه‌ها به نتیجه
        for language, translations in self.translations.items():
            if field_name in translations:
                result[language] = translations[field_name]

        return result

    def get_available_languages(self, field_name=None):
        """
        دریافت لیست زبان‌های موجود برای یک فیلد یا تمام فیلدها

        Args:
            field_name: نام فیلد (اختیاری)

        Returns:
            لیست کدهای زبان‌های موجود
        """
        # زبان پیش‌فرض همیشه موجود است
        result = [settings.LANGUAGE_CODE]

        if not self.translations:
            return result

        # اگر فیلد مشخص شده، زبان‌های دارای ترجمه برای آن فیلد را برگردان
        if field_name:
            # بررسی معتبر بودن فیلد
            if field_name not in self.TRANSLATABLE_FIELDS:
                raise ValidationError(f"فیلد {field_name} قابل ترجمه نیست.")

            for language, translations in self.translations.items():
                if field_name in translations and language not in result:
                    result.append(language)
        else:
            # در غیر این صورت، تمام زبان‌های موجود را برگردان
            for language in self.translations.keys():
                if language not in result:
                    result.append(language)

        return result

    def copy_translations(self, source_language, target_language, fields=None):
        """
        کپی ترجمه‌ها از یک زبان به زبان دیگر

        Args:
            source_language: کد زبان مبدأ
            target_language: کد زبان مقصد
            fields: لیست فیلدهایی که باید کپی شوند (اختیاری، اگر ارائه نشود، تمام فیلدهای قابل ترجمه کپی می‌شوند)

        Returns:
            نمونه مدل به‌روزرسانی شده
        """
        # فهرست فیلدهایی که باید کپی شوند
        fields_to_copy = fields or self.TRANSLATABLE_FIELDS

        # کپی ترجمه‌ها برای هر فیلد
        for field_name in fields_to_copy:
            if field_name not in self.TRANSLATABLE_FIELDS:
                continue

            # دریافت ترجمه از زبان مبدأ
            translation = self.get_translation(field_name, source_language)

            # تنظیم ترجمه در زبان مقصد
            self.set_translation(field_name, translation, target_language)

        return self

    def validate_translations(self):
        """
        اعتبارسنجی فیلد translations و ساختار آن

        Raises:
            ValidationError: اگر ساختار فیلد translations نامعتبر باشد
        """
        if not self.translations:
            return

        # بررسی ساختار فیلد translations
        if not isinstance(self.translations, dict):
            raise ValidationError("فیلد translations باید یک دیکشنری باشد.")

        # بررسی ساختار زبان‌ها و ترجمه‌ها
        for language, translations in self.translations.items():
            # بررسی کد زبان
            if not isinstance(language, str):
                raise ValidationError(f"کد زبان ({language}) باید یک رشته باشد.")

            # بررسی معتبر بودن کد زبان
            if language not in dict(settings.LANGUAGES):
                raise ValidationError(f"کد زبان ({language}) معتبر نیست.")

            # بررسی ساختار ترجمه‌ها
            if not isinstance(translations, dict):
                raise ValidationError(f"ترجمه‌های زبان ({language}) باید یک دیکشنری باشد.")

            # بررسی فیلدهای ترجمه شده
            for field_name in translations:
                if field_name not in self.TRANSLATABLE_FIELDS:
                    raise ValidationError(f"فیلد ({field_name}) قابل ترجمه نیست.")

    def clean(self):
        """
        اعتبارسنجی مدل قبل از ذخیره
        """
        super().clean()

        # اعتبارسنجی ترجمه‌ها
        self.validate_translations()

    def save(self, *args, **kwargs):
        """
        ذخیره مدل با اعتبارسنجی ترجمه‌ها
        """
        # اعتبارسنجی ترجمه‌ها
        self.validate_translations()

        super().save(*args, **kwargs)

        # به‌روزرسانی مقدار اولیه translations
        self._initial_translations = copy.deepcopy(self.translations)

    def has_translation(self, field_name, language=None):
        """
        بررسی وجود ترجمه برای یک فیلد در زبان مشخص

        Args:
            field_name: نام فیلد
            language: کد زبان (اختیاری، اگر ارائه نشود، زبان فعلی استفاده می‌شود)

        Returns:
            True اگر ترجمه وجود داشته باشد، False در غیر این صورت
        """
        # بررسی معتبر بودن فیلد
        if field_name not in self.TRANSLATABLE_FIELDS:
            return False

        # تنظیم زبان پیش‌فرض اگر ارائه نشده
        if language is None:
            language = get_language() or settings.LANGUAGE_CODE

        # اگر زبان درخواستی، زبان پیش‌فرض است، همیشه ترجمه وجود دارد
        if language == settings.LANGUAGE_CODE:
            return True

        # بررسی وجود ترجمه
        if not self.translations:
            return False

        # بررسی وجود زبان و فیلد
        return language in self.translations and field_name in self.translations[language]

    def translate_all_fields(self, language=None):
        """
        دریافت ترجمه تمام فیلدهای قابل ترجمه در زبان مشخص

        Args:
            language: کد زبان (اختیاری، اگر ارائه نشود، زبان فعلی استفاده می‌شود)

        Returns:
            دیکشنری فیلدها و مقادیر ترجمه شده‌ی آن‌ها
        """
        # تنظیم زبان پیش‌فرض اگر ارائه نشده
        if language is None:
            language = get_language() or settings.LANGUAGE_CODE

        # دیکشنری نتیجه
        result = {}

        # دریافت ترجمه هر فیلد
        for field_name in self.TRANSLATABLE_FIELDS:
            result[field_name] = self.get_translation(field_name, language)

        return result