# core/middlewares/language.py

import re
from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.urls import is_valid_path


class LanguageMiddleware(MiddlewareMixin):
    """
    میدل‌ویر تشخیص و تنظیم زبان کاربر.
    این میدل‌ویر زبان مورد نظر کاربر را از طریق URL، هدر و یا کوکی تشخیص می‌دهد.
    قابلیت اعمال زبان پیش‌فرض بر اساس مسیر URL خاص را دارد.

    مثال URL چندزبانه: /fa/products/ یا /en/products/
    """

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.language_pattern = re.compile(r'^/(?P<language>(%s))/' % '|'.join(dict(settings.LANGUAGES).keys()))
        # مسیرهایی که همیشه باید با زبان فارسی نشان داده شوند
        self.persian_only_paths = getattr(settings, 'PERSIAN_ONLY_PATHS', [
            '/admin/',
            '/artists/dashboard/',
        ])
        # مسیرهایی که همیشه باید با زبان انگلیسی نشان داده شوند
        self.english_only_paths = getattr(settings, 'ENGLISH_ONLY_PATHS', [
            '/api/',
            '/docs/',
        ])
        super().__init__(get_response)

    def process_request(self, request):
        """پردازش درخواست و تشخیص زبان"""
        language = self.get_language_from_url(request)

        if not language:
            language = self.get_language_from_header(request)

        if not language:
            language = self.get_language_from_cookie(request)

        if not language:
            language = self.get_language_from_path_rules(request)

        if not language:
            language = settings.LANGUAGE_CODE

        translation.activate(language)
        request.LANGUAGE_CODE = language

    def process_response(self, request, response):
        """تنظیم کوکی زبان در پاسخ"""
        if hasattr(request, 'LANGUAGE_CODE') and request.LANGUAGE_CODE:
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                request.LANGUAGE_CODE,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
        return response

    def get_language_from_url(self, request):
        """استخراج زبان از URL"""
        match = self.language_pattern.match(request.path_info)
        if match:
            return match.group('language')
        return None

    def get_language_from_header(self, request):
        """استخراج زبان از هدر Accept-Language"""
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            languages = [lang.split(';')[0].strip() for lang in accept_language.split(',')]
            for lang in languages:
                if lang in dict(settings.LANGUAGES):
                    return lang
                # بررسی کد زبان دو حرفی (مثلاً en-US -> en)
                lang_prefix = lang.split('-')[0]
                if lang_prefix in dict(settings.LANGUAGES):
                    return lang_prefix
        return None

    def get_language_from_cookie(self, request):
        """استخراج زبان از کوکی"""
        return request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    def get_language_from_path_rules(self, request):
        """تشخیص زبان بر اساس قوانین مسیر"""
        path = request.path_info

        # بررسی مسیرهای همیشه فارسی
        for persian_path in self.persian_only_paths:
            if path.startswith(persian_path):
                return 'fa'

        # بررسی مسیرهای همیشه انگلیسی
        for english_path in self.english_only_paths:
            if path.startswith(english_path):
                return 'en'

        return None