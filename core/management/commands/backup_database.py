# core/management/commands/backup_database.py

import os
import time
import subprocess
import tempfile
import datetime
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage

logger = logging.getLogger('commands')


class Command(BaseCommand):
    """
    دستور مدیریتی برای تهیه پشتیبان از پایگاه داده.

    این دستور پشتیبان از پایگاه داده PostgreSQL تهیه می‌کند و آن را در مسیر مشخص شده
    یا در خدمات ذخیره‌سازی ابری ذخیره می‌کند.
    """

    help = 'تهیه پشتیبان از پایگاه داده'

    def add_arguments(self, parser):
        """تعریف آرگومان‌های دستور"""
        parser.add_argument(
            '--output',
            dest='output_dir',
            type=str,
            help='مسیر ذخیره‌سازی فایل پشتیبان',
        )

        parser.add_argument(
            '--filename',
            dest='filename',
            type=str,
            help='نام فایل پشتیبان (پیش‌فرض: backup_YYYY-MM-DD_HH-MM-SS.sql.gz)',
        )

        parser.add_argument(
            '--no-compression',
            action='store_true',
            dest='no_compression',
            help='عدم فشرده‌سازی فایل پشتیبان',
        )

        parser.add_argument(
            '--databases',
            dest='databases',
            type=str,
            help='نام پایگاه‌های داده (با کاما جدا شوند، پیش‌فرض: پایگاه داده اصلی)',
        )

        parser.add_argument(
            '--exclude-tables',
            dest='exclude_tables',
            type=str,
            help='جدول‌هایی که باید از پشتیبان‌گیری مستثنی شوند (با کاما جدا شوند)',
        )

        parser.add_argument(
            '--email',
            dest='email',
            type=str,
            help='آدرس ایمیل برای ارسال فایل پشتیبان',
        )

        parser.add_argument(
            '--upload-s3',
            action='store_true',
            dest='upload_s3',
            help='آپلود فایل پشتیبان در Amazon S3',
        )

        parser.add_argument(
            '--keep-local',
            action='store_true',
            dest='keep_local',
            help='نگهداری نسخه محلی پس از آپلود در S3',
        )

    def handle(self, *args, **options):
        """اجرای دستور"""
        output_dir = options['output_dir']
        filename = options['filename']
        no_compression = options['no_compression']
        databases = options['databases']
        exclude_tables = options['exclude_tables']
        email = options['email']
        upload_s3 = options['upload_s3']
        keep_local = options['keep_local']

        # تنظیم مسیر خروجی پیش‌فرض
        if not output_dir:
            output_dir = getattr(settings, 'BACKUP_DIR', None)
            if not output_dir:
                output_dir = os.path.join(settings.BASE_DIR, 'backups')

        # اطمینان از وجود دایرکتوری خروجی
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                raise CommandError(f"خطا در ایجاد دایرکتوری خروجی: {str(e)}")

        # تنظیم نام فایل پیش‌فرض
        if not filename:
            timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
            if no_compression:
                filename = f"backup_{timestamp}.sql"
            else:
                filename = f"backup_{timestamp}.sql.gz"

        # مسیر کامل فایل
        backup_file = os.path.join(output_dir, filename)

        # دریافت اطلاعات پایگاه داده از تنظیمات
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        # اگر کاربر دیتابیس‌های مشخصی را درخواست کرده، استفاده از آن‌ها
        if databases:
            db_list = databases.split(',')
        else:
            db_list = [db_name]

        # تبدیل لیست جدول‌های مستثنی به آرگومان‌های دستور
        exclude_args = []
        if exclude_tables:
            for table in exclude_tables.split(','):
                exclude_args.extend(['-T', table.strip()])

        # انجام پشتیبان‌گیری برای هر پایگاه داده
        successful_backups = []
        failed_backups = []

        for db in db_list:
            # تنظیم نام فایل برای چندین پایگاه داده
            if len(db_list) > 1:
                db_filename = filename.replace('.sql', f"_{db}.sql").replace('.gz', f"_{db}.gz")
                db_backup_file = os.path.join(output_dir, db_filename)
            else:
                db_backup_file = backup_file

            self.stdout.write(f"تهیه پشتیبان از پایگاه داده {db}...")

            try:
                # تنظیم متغیر محیطی PGPASSWORD برای دسترسی بدون نیاز به رمز عبور
                os.environ['PGPASSWORD'] = db_password

                # ساخت دستور pg_dump
                command = [
                    'pg_dump',
                    '-h', db_host,
                    '-p', db_port,
                    '-U', db_user,
                    '-d', db,
                    '-F', 'c',  # فرمت سفارشی (قابل استفاده با pg_restore)
                    *exclude_args,
                    '-v'  # حالت verbose
                ]

                # اضافه کردن فشرده‌سازی اگر نیاز باشد
                if no_compression:
                    with open(db_backup_file, 'wb') as f:
                        subprocess.run(command, stdout=f, check=True)
                else:
                    process = subprocess.Popen(command, stdout=subprocess.PIPE)
                    with open(db_backup_file, 'wb') as f:
                        subprocess.run(['gzip'], stdin=process.stdout, stdout=f, check=True)
                    process.wait()

                successful_backups.append((db, db_backup_file))
                self.stdout.write(
                    self.style.SUCCESS(f"پشتیبان از پایگاه داده {db} با موفقیت در {db_backup_file} ذخیره شد."))

            except subprocess.SubprocessError as e:
                failed_backups.append((db, str(e)))
                self.stdout.write(self.style.ERROR(f"خطا در تهیه پشتیبان از پایگاه داده {db}: {str(e)}"))

            finally:
                # پاک کردن متغیر محیطی PGPASSWORD
                if 'PGPASSWORD' in os.environ:
                    del os.environ['PGPASSWORD']

        # آپلود در Amazon S3 اگر درخواست شده باشد
        if upload_s3 and successful_backups:
            self.upload_to_s3(successful_backups, keep_local)

        # ارسال ایمیل اگر درخواست شده باشد
        if email and successful_backups:
            self.send_email(email, successful_backups, failed_backups)

        # نمایش خلاصه
        self.stdout.write(
            self.style.SUCCESS(f"پشتیبان‌گیری از {len(successful_backups)} پایگاه داده با موفقیت انجام شد."))
        if failed_backups:
            self.stdout.write(self.style.ERROR(f"پشتیبان‌گیری از {len(failed_backups)} پایگاه داده ناموفق بود."))

    def upload_to_s3(self, successful_backups, keep_local):
        """آپلود فایل‌های پشتیبان در Amazon S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            # دریافت تنظیمات S3 از تنظیمات پروژه
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            s3_bucket = getattr(settings, 'AWS_BACKUP_BUCKET_NAME', None)

            if not (aws_access_key and aws_secret_key and s3_bucket):
                self.stdout.write(self.style.ERROR("تنظیمات AWS S3 ناقص است. آپلود انجام نشد."))
                return

            # ایجاد کلاینت S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )

            # آپلود هر فایل
            for db, file_path in successful_backups:
                try:
                    file_name = os.path.basename(file_path)
                    s3_key = f"database_backups/{file_name}"

                    self.stdout.write(f"آپلود {file_name} در S3...")

                    # آپلود فایل
                    s3_client.upload_file(
                        file_path,
                        s3_bucket,
                        s3_key,
                        ExtraArgs={'StorageClass': 'STANDARD_IA'}  # کلاس ذخیره‌سازی کم‌هزینه
                    )

                    self.stdout.write(self.style.SUCCESS(f"فایل {file_name} با موفقیت در S3 آپلود شد."))

                    # حذف فایل محلی اگر درخواست شده باشد
                    if not keep_local:
                        os.remove(file_path)
                        self.stdout.write(f"فایل محلی {file_name} حذف شد.")

                except ClientError as e:
                    self.stdout.write(self.style.ERROR(f"خطا در آپلود {file_name} در S3: {str(e)}"))

        except ImportError:
            self.stdout.write(self.style.ERROR("پکیج boto3 نصب نشده است. برای آپلود در S3 به boto3 نیاز دارید."))

    def send_email(self, email, successful_backups, failed_backups):
        """ارسال ایمیل با پیوست فایل‌های پشتیبان"""
        try:
            # ساخت متن ایمیل
            subject = f"پشتیبان پایگاه داده Ma2tA - {timezone.now().strftime('%Y-%m-%d')}"

            message = f"""سلام،

پشتیبان پایگاه داده Ma2tA در تاریخ {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} تهیه شد.

"""

            if successful_backups:
                message += "پشتیبان‌گیری موفق:\n"
                for db, file_path in successful_backups:
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # مگابایت
                    message += f"- {db}: {file_name} ({file_size:.2f} MB)\n"

            if failed_backups:
                message += "\nپشتیبان‌گیری ناموفق:\n"
                for db, error in failed_backups:
                    message += f"- {db}: {error}\n"

            message += "\nاین ایمیل به صورت خودکار توسط سیستم ارسال شده است.\n\nبا احترام،\nتیم Ma2tA"

            # ساخت ایمیل
            email_message = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )

            # پیوست کردن فایل‌های پشتیبان
            for db, file_path in successful_backups:
                # فقط فایل‌های کوچکتر از 10 مگابایت پیوست شوند
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # مگابایت
                if file_size <= 10:
                    file_name = os.path.basename(file_path)
                    with open(file_path, 'rb') as f:
                        email_message.attach(file_name, f.read(), 'application/octet-stream')
                else:
                    message += f"\nفایل {os.path.basename(file_path)} به دلیل حجم زیاد ({file_size:.2f} MB) پیوست نشد."

            # ارسال ایمیل
            email_message.send()
            self.stdout.write(self.style.SUCCESS(f"ایمیل پشتیبان با موفقیت به {email} ارسال شد."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطا در ارسال ایمیل: {str(e)}"))