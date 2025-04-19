# core/management/commands/rebuild_search_index.py

import time
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q

logger = logging.getLogger('commands')


class Command(BaseCommand):
    """
    دستور مدیریتی برای بازسازی ایندکس جستجو.

    این دستور ایندکس جستجو را برای مدل‌های مختلف بازسازی می‌کند تا سرعت و دقت جستجو بهبود یابد.
    برای استفاده نیاز به پیاده‌سازی متد `update_search_vector` در مدل‌های مورد نظر است.
    """

    help = 'بازسازی ایندکس جستجو برای مدل‌های مختلف'

    def add_arguments(self, parser):
        """تعریف آرگومان‌های دستور"""
        parser.add_argument(
            '--models',
            dest='models',
            type=str,
            help='لیست مدل‌ها به صورت app_label.model_name (با کاما جدا شوند، پیش‌فرض: همه مدل‌ها)',
        )

        parser.add_argument(
            '--batch-size',
            dest='batch_size',
            type=int,
            default=1000,
            help='تعداد رکوردها در هر بچ (پیش‌فرض: 1000)',
        )

        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='اجبار به بازسازی کامل ایندکس، حتی برای رکوردهایی که تغییر نکرده‌اند',
        )

    def handle(self, *args, **options):
        """اجرای دستور"""
        models_arg = options['models']
        batch_size = options['batch_size']
        force = options['force']

        # لیست مدل‌هایی که باید ایندکس آن‌ها بازسازی شود
        models_to_index = []

        if models_arg:
            # پیدا کردن مدل‌های مشخص شده
            for model_path in models_arg.split(','):
                try:
                    app_label, model_name = model_path.strip().split('.')
                    model = models.get_model(app_label, model_name)
                    if hasattr(model, 'update_search_vector'):
                        models_to_index.append(model)
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"مدل {model_path} متد update_search_vector ندارد و نادیده گرفته می‌شود."))
                except (ValueError, LookupError) as e:
                    self.stdout.write(self.style.ERROR(f"خطا در یافتن مدل {model_path}: {str(e)}"))
        else:
            # پیدا کردن همه مدل‌هایی که متد update_search_vector دارند
            for app_config in settings.INSTALLED_APPS:
                try:
                    app_models = models.get_models(app_config)
                    for model in app_models:
                        if hasattr(model, 'update_search_vector'):
                            models_to_index.append(model)
                except LookupError:
                    pass

        if not models_to_index:
            self.stdout.write(self.style.ERROR("هیچ مدلی برای بازسازی ایندکس پیدا نشد."))
            return

        total_count = 0

        # برای هر مدل
        for model in models_to_index:
            model_name = f"{model._meta.app_label}.{model._meta.model_name}"

            self.stdout.write(f"بازسازی ایندکس برای {model_name}...")

            # تعداد کل رکوردها
            total_records = model.objects.count()

            if total_records == 0:
                self.stdout.write(f"هیچ رکوردی برای {model_name} یافت نشد. گذر از این مدل.")
                continue

            processed_count = 0
            start_time = time.time()

            # ایندکس‌گذاری به صورت بچ
            while processed_count < total_records:
                # محدوده بچ فعلی
                batch_end = min(processed_count + batch_size, total_records)

                # رکوردهای بچ فعلی
                query = model.objects.all()[processed_count:batch_end]

                # اگر بازسازی اجباری نیست، فقط رکوردهای تغییر یافته را بازسازی کنید
                if not force and hasattr(model, 'search_vector') and hasattr(model, 'updated_at'):
                    query = query.filter(
                        Q(search_vector__isnull=True) |
                        Q(updated_at__gt=models.F('search_vector_updated'))
                    )

                # محاسبه رکوردها در این بچ
                batch_count = query.count()

                if batch_count > 0:
                    with transaction.atomic():
                        # بازسازی ایندکس برای بچ فعلی
                        for obj in query:
                            try:
                                obj.update_search_vector()
                                obj.save(update_fields=['search_vector', 'search_vector_updated'])
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(
                                    f"خطا در بازسازی ایندکس برای {model_name} با ID {obj.pk}: {str(e)}"))

                # به‌روزرسانی شمارنده‌ها
                processed_count += batch_size
                total_count += batch_count

                # نمایش پیشرفت
                progress = min(processed_count, total_records) / total_records * 100
                self.stdout.write(
                    f"پیشرفت {model_name}: {progress:.1f}% ({min(processed_count, total_records)}/{total_records})")

            # محاسبه زمان کل
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(
                f"بازسازی ایندکس برای {model_name} با موفقیت انجام شد. زمان: {elapsed_time:.2f} ثانیه"))

        self.stdout.write(self.style.SUCCESS(f"بازسازی ایندکس‌ها برای {total_count} رکورد با موفقیت انجام شد."))