# core/management/commands/cleanup_data.py

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session

User = get_user_model()
logger = logging.getLogger('commands')


class Command(BaseCommand):
    """
    دستور مدیریتی برای پاکسازی داده‌های قدیمی و غیرضروری.

    این دستور می‌تواند موارد زیر را پاکسازی کند:
    - کاربران تأیید نشده قدیمی
    - جلسات منقضی شده
    - توکن‌های بازنشانی رمز عبور منقضی شده
    - تراکنش‌های ناموفق قدیمی
    - فایل‌های موقت
    - لاگ‌های قدیمی
    """

    help = 'پاکسازی داده‌های قدیمی و غیرضروری از پایگاه داده'

    def add_arguments(self, parser):
        """تعریف آرگومان‌های دستور"""
        parser.add_argument(
            '--users',
            action='store_true',
            dest='clean_users',
            help='پاکسازی کاربران تأیید نشده قدیمی',
        )

        parser.add_argument(
            '--sessions',
            action='store_true',
            dest='clean_sessions',
            help='پاکسازی جلسات منقضی شده',
        )

        parser.add_argument(
            '--tokens',
            action='store_true',
            dest='clean_tokens',
            help='پاکسازی توکن‌های بازنشانی رمز عبور منقضی شده',
        )

        parser.add_argument(
            '--transactions',
            action='store_true',
            dest='clean_transactions',
            help='پاکسازی تراکنش‌های ناموفق قدیمی',
        )

        parser.add_argument(
            '--temp-files',
            action='store_true',
            dest='clean_temp_files',
            help='پاکسازی فایل‌های موقت',
        )

        parser.add_argument(
            '--logs',
            action='store_true',
            dest='clean_logs',
            help='پاکسازی لاگ‌های قدیمی',
        )

        parser.add_argument(
            '--days',
            dest='days',
            type=int,
            default=30,
            help='تعداد روزهای قدیمی (پیش‌فرض: 30)',
        )

        parser.add_argument(
            '--all',
            action='store_true',
            dest='clean_all',
            help='پاکسازی همه داده‌های قدیمی',
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='نمایش اقدامات بدون انجام آن‌ها',
        )

    def handle(self, *args, **options):
        """اجرای دستور"""
        clean_users = options['clean_users']
        clean_sessions = options['clean_sessions']
        clean_tokens = options['clean_tokens']
        clean_transactions = options['clean_transactions']
        clean_temp_files = options['clean_temp_files']
        clean_logs = options['clean_logs']
        clean_all = options['clean_all']
        days = options['days']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('اجرا در حالت dry-run. هیچ داده‌ای حذف نخواهد شد.'))

        # تنظیم تاریخ مرز برای داده‌های قدیمی
        cutoff_date = timezone.now() - timedelta(days=days)

        # آمار پاکسازی
        stats = {
            'users': 0,
            'sessions': 0,
            'tokens': 0,
            'transactions': 0,
            'temp_files': 0,
            'logs': 0,
        }

        # پاکسازی کاربران تأیید نشده
        if clean_users or clean_all:
            stats['users'] = self.cleanup_users(cutoff_date, dry_run)

        # پاکسازی جلسات منقضی شده
        if clean_sessions or clean_all:
            stats['sessions'] = self.cleanup_sessions(cutoff_date, dry_run)

        # پاکسازی توکن‌های بازنشانی رمز عبور
        if clean_tokens or clean_all:
            stats['tokens'] = self.cleanup_tokens(cutoff_date, dry_run)

        # پاکسازی تراکنش‌های ناموفق
        if clean_transactions or clean_all:
            stats['transactions'] = self.cleanup_transactions(cutoff_date, dry_run)

        # پاکسازی فایل‌های موقت
        if clean_temp_files or clean_all:
            stats['temp_files'] = self.cleanup_temp_files(cutoff_date, dry_run)

        # پاکسازی لاگ‌ها
        if clean_logs or clean_all:
            stats['logs'] = self.cleanup_logs(cutoff_date, dry_run)

        # نمایش خلاصه پاکسازی
        self.stdout.write(self.style.SUCCESS('پاکسازی داده‌های قدیمی با موفقیت انجام شد:'))
        for name, count in stats.items():
            if count > 0:
                self.stdout.write(f"  - {name}: {count}")

    def cleanup_users(self, cutoff_date, dry_run):
        """پاکسازی کاربران تأیید نشده قدیمی"""
        # کاربران تأیید نشده که بیش از زمان مشخص شده قدیمی هستند
        unverified_users = User.objects.filter(
            is_active=False,
            date_joined__lt=cutoff_date,
            email_verified=False
        )

        count = unverified_users.count()

        if count:
            self.stdout.write(f"پاکسازی {count} کاربر تأیید نشده قدیمی...")

            if not dry_run:
                unverified_users.delete()
        else:
            self.stdout.write("هیچ کاربر تأیید نشده قدیمی یافت نشد.")

        return count

    def cleanup_sessions(self, cutoff_date, dry_run):
        """پاکسازی جلسات منقضی شده"""
        # جلسات منقضی شده
        expired_sessions = Session.objects.filter(
            expire_date__lt=cutoff_date
        )

        count = expired_sessions.count()

        if count:
            self.stdout.write(f"پاکسازی {count} جلسه منقضی شده...")

            if not dry_run:
                expired_sessions.delete()
        else:
            self.stdout.write("هیچ جلسه منقضی شده یافت نشد.")

        return count

    def cleanup_tokens(self, cutoff_date, dry_run):
        """پاکسازی توکن‌های بازنشانی رمز عبور منقضی شده"""
        # بررسی وجود مدل توکن‌های بازنشانی رمز عبور
        try:
            from django.contrib.auth.models import PasswordResetToken

            expired_tokens = PasswordResetToken.objects.filter(
                created_at__lt=cutoff_date
            )

            count = expired_tokens.count()

            if count:
                self.stdout.write(f"پاکسازی {count} توکن بازنشانی رمز عبور منقضی شده...")

                if not dry_run:
                    expired_tokens.delete()
            else:
                self.stdout.write("هیچ توکن بازنشانی رمز عبور منقضی شده یافت نشد.")

            return count
        except ImportError:
            self.stdout.write("مدل توکن بازنشانی رمز عبور پیدا نشد.")
            return 0

    def cleanup_transactions(self, cutoff_date, dry_run):
        """پاکسازی تراکنش‌های ناموفق قدیمی"""
        # بررسی وجود مدل تراکنش‌ها
        try:
            from apps.payments.models import Transaction

            # تراکنش‌های ناموفق قدیمی
            failed_transactions = Transaction.objects.filter(
                status='failed',
                created_at__lt=cutoff_date
            )

            count = failed_transactions.count()

            if count:
                self.stdout.write(f"پاکسازی {count} تراکنش ناموفق قدیمی...")

                if not dry_run:
                    failed_transactions.delete()
            else:
                self.stdout.write("هیچ تراکنش ناموفق قدیمی یافت نشد.")

            return count
        except ImportError:
            self.stdout.write("مدل تراکنش پیدا نشد.")
            return 0

    def cleanup_temp_files(self, cutoff_date, dry_run):
        """پاکسازی فایل‌های موقت"""
        import os
        from django.conf import settings

        # مسیر پوشه فایل‌های موقت
        temp_dir = getattr(settings, 'TEMP_DIR', None)
        if not temp_dir or not os.path.exists(temp_dir):
            self.stdout.write("پوشه فایل‌های موقت پیدا نشد.")
            return 0

        count = 0
        cutoff_timestamp = cutoff_date.timestamp()

        # بررسی فایل‌های موقت قدیمی
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # بررسی زمان آخرین تغییر فایل
                if os.path.getmtime(file_path) < cutoff_timestamp:
                    self.stdout.write(f"پاکسازی فایل موقت: {file}")
                    count += 1

                    if not dry_run:
                        try:
                            os.remove(file_path)
                        except OSError as e:
                            self.stdout.write(f"خطا در حذف فایل {file}: {str(e)}")

        if count:
            self.stdout.write(f"پاکسازی {count} فایل موقت قدیمی...")
        else:
            self.stdout.write("هیچ فایل موقت قدیمی یافت نشد.")

        return count

    def cleanup_logs(self, cutoff_date, dry_run):
        """پاکسازی لاگ‌های قدیمی"""
        # بررسی وجود مدل لاگ‌ها
        try:
            # تلاش برای پیدا کردن مدل‌های لاگ
            log_models = []

            try:
                from apps.core.models import SystemLog
                log_models.append(SystemLog)
            except ImportError:
                pass

            try:
                from apps.audit.models import AuditLog
                log_models.append(AuditLog)
            except ImportError:
                pass

            if not log_models:
                self.stdout.write("هیچ مدل لاگی پیدا نشد.")
                return 0

            count = 0

            for model in log_models:
                # لاگ‌های قدیمی
                old_logs = model.objects.filter(
                    created_at__lt=cutoff_date
                )

                model_count = old_logs.count()
                count += model_count

                if model_count:
                    self.stdout.write(f"پاکسازی {model_count} لاگ قدیمی از {model.__name__}...")

                    if not dry_run:
                        # حذف دسته‌ای برای کارایی بهتر
                        old_logs.delete()

            if count:
                self.stdout.write(f"پاکسازی {count} لاگ قدیمی...")
            else:
                self.stdout.write("هیچ لاگ قدیمی یافت نشد.")

            return count
        except Exception as e:
            self.stdout.write(f"خطا در پاکسازی لاگ‌ها: {str(e)}")
            return 0