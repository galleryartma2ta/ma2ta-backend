# core/management/commands/generate_report.py

import os
import csv
import json
import logging
import datetime
from io import StringIO
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum, Count, Avg, Min, Max, F, Q
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

User = get_user_model()
logger = logging.getLogger('commands')


class Command(BaseCommand):
    """
    دستور مدیریتی برای تولید گزارش‌های آماری و تحلیلی از داده‌ها.

    این دستور می‌تواند گزارش‌های زیر را تولید کند:
    - گزارش کاربران
    - گزارش محصولات و آثار هنری
    - گزارش فروش و سفارشات
    - گزارش فعالیت هنرمندان
    - گزارش مالی
    """

    help = 'تولید گزارش‌های آماری و تحلیلی از داده‌ها'

    def add_arguments(self, parser):
        """تعریف آرگومان‌های دستور"""
        parser.add_argument(
            '--type',
            dest='report_type',
            type=str,
            choices=['users', 'products', 'sales', 'artists', 'financial', 'all'],
            default='all',
            help='نوع گزارش (پیش‌فرض: all)',
        )

        parser.add_argument(
            '--format',
            dest='report_format',
            type=str,
            choices=['csv', 'json', 'html', 'text'],
            default='csv',
            help='قالب گزارش (پیش‌فرض: csv)',
        )

        parser.add_argument(
            '--period',
            dest='period',
            type=str,
            choices=['day', 'week', 'month', 'quarter', 'year', 'all'],
            default='month',
            help='دوره زمانی گزارش (پیش‌فرض: month)',
        )

        parser.add_argument(
            '--start-date',
            dest='start_date',
            type=str,
            help='تاریخ شروع گزارش (YYYY-MM-DD)',
        )

        parser.add_argument(
            '--end-date',
            dest='end_date',
            type=str,
            help='تاریخ پایان گزارش (YYYY-MM-DD)',
        )

        parser.add_argument(
            '--output',
            dest='output',
            type=str,
            help='مسیر فایل خروجی',
        )

        parser.add_argument(
            '--email',
            dest='email',
            type=str,
            help='آدرس ایمیل برای ارسال گزارش',
        )

    def handle(self, *args, **options):
        """اجرای دستور"""
        report_type = options['report_type']
        report_format = options['report_format']
        period = options['period']

        # پردازش تاریخ‌ها
        start_date, end_date = self.get_date_range(period, options)

        # مسیر خروجی
        output_path = options['output']
        if not output_path:
            # تنظیم مسیر پیش‌فرض
            reports_dir = os.path.join(settings.BASE_DIR, 'reports')
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)

            filename = f"{report_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.{report_format}"
            output_path = os.path.join(reports_dir, filename)

        # تولید گزارش
        self.stdout.write(
            f"تولید گزارش {report_type} از {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')}...")

        report_data = None

        if report_type == 'users' or report_type == 'all':
            report_data = self.generate_users_report(start_date, end_date)
            self.save_report(report_data, output_path, report_format, 'users')

        if report_type == 'products' or report_type == 'all':
            report_data = self.generate_products_report(start_date, end_date)
            self.save_report(report_data, output_path, report_format, 'products')

        if report_type == 'sales' or report_type == 'all':
            report_data = self.generate_sales_report(start_date, end_date)
            self.save_report(report_data, output_path, report_format, 'sales')

        if report_type == 'artists' or report_type == 'all':
            report_data = self.generate_artists_report(start_date, end_date)
            self.save_report(report_data, output_path, report_format, 'artists')

        if report_type == 'financial' or report_type == 'all':
            report_data = self.generate_financial_report(start_date, end_date)
            self.save_report(report_data, output_path, report_format, 'financial')

        # ارسال گزارش به ایمیل (اگر درخواست شده باشد)
        if options['email'] and report_data:
            self.send_report_email(options['email'], report_data, report_type, start_date, end_date, output_path)

        self.stdout.write(self.style.SUCCESS(f"گزارش با موفقیت در {output_path} ذخیره شد."))

    def get_date_range(self, period, options):
        """محاسبه بازه زمانی گزارش"""
        end_date = timezone.now().date()
        if options['end_date']:
            try:
                end_date = datetime.datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('فرمت تاریخ نامعتبر است. از فرمت YYYY-MM-DD استفاده کنید.')

        start_date = None
        if options['start_date']:
            try:
                start_date = datetime.datetime.strptime(options['start_date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('فرمت تاریخ نامعتبر است. از فرمت YYYY-MM-DD استفاده کنید.')
        else:
            # محاسبه تاریخ شروع بر اساس دوره
            if period == 'day':
                start_date = end_date - datetime.timedelta(days=1)
            elif period == 'week':
                start_date = end_date - datetime.timedelta(days=7)
            elif period == 'month':
                start_date = end_date.replace(day=1)
                if start_date.month == 1:
                    start_date = start_date.replace(year=start_date.year - 1, month=12)
                else:
                    start_date = start_date.replace(month=start_date.month - 1)
            elif period == 'quarter':
                months_to_subtract = 3
                year = end_date.year
                month = end_date.month - months_to_subtract
                if month <= 0:
                    month += 12
                    year -= 1
                start_date = end_date.replace(year=year, month=month, day=1)
            elif period == 'year':
                start_date = end_date.replace(year=end_date.year - 1)
            elif period == 'all':
                # استفاده از تاریخ بسیار قدیمی
                start_date = datetime.date(2000, 1, 1)

        # تبدیل به datetime با timezone
        start_datetime = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
        end_datetime = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))

        return start_datetime, end_datetime

    def generate_users_report(self, start_date, end_date):
        """تولید گزارش کاربران"""
        self.stdout.write("تولید گزارش کاربران...")

        # آمار کاربران جدید در بازه زمانی
        new_users = User.objects.filter(
            date_joined__gte=start_date,
            date_joined__lte=end_date
        )

        # آمار کاربران فعال (با حداقل یک ورود در بازه زمانی)
        active_users = User.objects.filter(
            last_login__gte=start_date,
            last_login__lte=end_date
        )

        # آمار کاربران تأیید شده
        verified_users = User.objects.filter(
            email_verified=True
        )

        # آمار کاربران تقسیم‌بندی شده بر اساس نوع (معمولی، هنرمند، مدیر)
        user_types = {
            'normal': User.objects.filter(is_staff=False, is_superuser=False).count(),
            'artist': User.objects.filter(Q(artist_profile__isnull=False)).count(),
            'staff': User.objects.filter(is_staff=True).count(),
            'admin': User.objects.filter(is_superuser=True).count(),
        }

        # تعداد کاربران غیرفعال
        inactive_users = User.objects.filter(is_active=False).count()

        # تقسیم‌بندی کاربران بر اساس ماه ثبت‌نام
        users_by_month = {}
        for user in new_users:
            month = user.date_joined.strftime('%Y-%m')
            if month not in users_by_month:
                users_by_month[month] = 0
            users_by_month[month] += 1

        # تقسیم‌بندی کاربران بر اساس کشور/استان (اگر در مدل کاربر وجود داشته باشد)
        users_by_location = {}
        if hasattr(User, 'province'):
            location_users = User.objects.values('province').annotate(count=Count('id'))
            for item in location_users:
                if item['province']:
                    users_by_location[item['province']] = item['count']

        # ساخت دیکشنری نتیجه
        report = {
            'total_users': User.objects.count(),
            'new_users': new_users.count(),
            'active_users': active_users.count(),
            'verified_users': verified_users.count(),
            'inactive_users': inactive_users,
            'user_types': user_types,
            'users_by_month': users_by_month,
            'users_by_location': users_by_location,
        }

        return report

    def generate_products_report(self, start_date, end_date):
        """تولید گزارش محصولات و آثار هنری"""
        self.stdout.write("تولید گزارش محصولات...")

        try:
            # تلاش برای واردسازی مدل‌های مورد نیاز
            from apps.products.models import Artwork

            # آمار کل آثار هنری
            total_artworks = Artwork.objects.count()

            # آثار هنری اضافه شده در بازه زمانی
            new_artworks = Artwork.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            # آثار هنری فروخته شده
            sold_artworks = Artwork.objects.filter(status='sold')

            # آثار هنری بر اساس نوع
            artworks_by_type = {}
            type_stats = Artwork.objects.values('type').annotate(count=Count('id'))
            for item in type_stats:
                if item['type']:
                    artworks_by_type[item['type']] = item['count']

            # آثار هنری بر اساس قیمت
            price_ranges = {
                'low': (0, 1000000),  # 0 تا 1 میلیون تومان
                'medium': (1000000, 5000000),  # 1 تا 5 میلیون تومان
                'high': (5000000, 20000000),  # 5 تا 20 میلیون تومان
                'premium': (20000000, float('inf')),  # بالای 20 میلیون تومان
            }

            artworks_by_price = {}
            for range_name, (min_price, max_price) in price_ranges.items():
                count = Artwork.objects.filter(price__gte=min_price, price__lt=max_price).count()
                artworks_by_price[range_name] = count

            # میانگین قیمت آثار هنری
            avg_price = Artwork.objects.aggregate(avg_price=Avg('price'))['avg_price'] or 0

            # آمار بازدید آثار هنری
            total_views = Artwork.objects.aggregate(total_views=Sum('view_count'))['total_views'] or 0

            # پربازدیدترین آثار هنری
            top_viewed = Artwork.objects.order_by('-view_count')[:10].values('id', 'title', 'view_count')

            # ساخت دیکشنری نتیجه
            report = {
                'total_artworks': total_artworks,
                'new_artworks': new_artworks.count(),
                'sold_artworks': sold_artworks.count(),
                'artworks_by_type': artworks_by_type,
                'artworks_by_price': artworks_by_price,
                'avg_price': avg_price,
                'total_views': total_views,
                'top_viewed': list(top_viewed),
            }

            return report

        except ImportError:
            self.stdout.write("مدل‌های محصولات یافت نشد.")
            return {
                'error': 'مدل‌های محصولات یافت نشد.',
            }

    def generate_sales_report(self, start_date, end_date):
        """تولید گزارش فروش و سفارشات"""
        self.stdout.write("تولید گزارش فروش...")

        try:
            # تلاش برای واردسازی مدل‌های مورد نیاز
            from apps.orders.models import Order, OrderItem

            # آمار سفارشات در بازه زمانی
            orders = Order.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            # تعداد کل سفارشات
            total_orders = orders.count()

            # مجموع مبلغ سفارشات
            total_amount = orders.aggregate(total=Sum('total_amount'))['total'] or 0

            # سفارشات بر اساس وضعیت
            orders_by_status = {}
            status_stats = orders.values('status').annotate(count=Count('id'))
            for item in status_stats:
                if item['status']:
                    orders_by_status[item['status']] = item['count']

            # سفارشات بر اساس روز هفته
            orders_by_weekday = {}
            for i in range(7):
                weekday_name = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه', 'یک‌شنبه'][i]
                count = orders.filter(created_at__week_day=i + 1).count()
                orders_by_weekday[weekday_name] = count

            # تعداد آیتم‌های فروخته شده
            total_items = OrderItem.objects.filter(
                order__created_at__gte=start_date,
                order__created_at__lte=end_date
            ).count()

            # محصولات پرفروش
            top_products = OrderItem.objects.filter(
                order__created_at__gte=start_date,
                order__created_at__lte=end_date
            ).values('artwork__title').annotate(
                count=Count('id')
            ).order_by('-count')[:10]

            # میانگین ارزش سفارش
            avg_order_value = total_amount / total_orders if total_orders > 0 else 0

            # ساخت دیکشنری نتیجه
            report = {
                'total_orders': total_orders,
                'total_amount': total_amount,
                'avg_order_value': avg_order_value,
                'total_items': total_items,
                'orders_by_status': orders_by_status,
                'orders_by_weekday': orders_by_weekday,
                'top_products': list(top_products),
            }

            return report

        except ImportError:
            self.stdout.write("مدل‌های سفارشات یافت نشد.")
            return {
                'error': 'مدل‌های سفارشات یافت نشد.',
            }

    def generate_artists_report(self, start_date, end_date):
        """تولید گزارش فعالیت هنرمندان"""
        self.stdout.write("تولید گزارش هنرمندان...")

        try:
            # تلاش برای واردسازی مدل‌های مورد نیاز
            from apps.artists.models import Artist

            # آمار کل هنرمندان
            total_artists = Artist.objects.count()

            # هنرمندان جدید در بازه زمانی
            new_artists = Artist.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            # هنرمندان فعال (با حداقل یک اثر)
            active_artists = Artist.objects.annotate(
                artwork_count=Count('artworks')
            ).filter(artwork_count__gt=0)

            # هنرمندان تأیید شده
            verified_artists = Artist.objects.filter(is_verified=True)

            # هنرمندان بر اساس سطح
            artists_by_level = {}
            level_stats = Artist.objects.values('level').annotate(count=Count('id'))
            for item in level_stats:
                if item['level']:
                    artists_by_level[item['level']] = item['count']

            # هنرمندان برتر بر اساس فروش
            top_artists = Artist.objects.annotate(
                sales_count=Count('artworks__orderitem', filter=Q(
                    artworks__orderitem__order__created_at__gte=start_date,
                    artworks__orderitem__order__created_at__lte=end_date,
                    artworks__orderitem__order__status='completed'
                ))
            ).order_by('-sales_count')[:10].values('id', 'user__username', 'sales_count')

            # میانگین تعداد آثار هر هنرمند
            avg_artworks = Artist.objects.annotate(
                artwork_count=Count('artworks')
            ).aggregate(avg=Avg('artwork_count'))['avg'] or 0

            # ساخت دیکشنری نتیجه
            report = {
                'total_artists': total_artists,
                'new_artists': new_artists.count(),
                'active_artists': active_artists.count(),
                'verified_artists': verified_artists.count(),
                'artists_by_level': artists_by_level,
                'top_artists': list(top_artists),
                'avg_artworks': avg_artworks,
            }

            return report

        except ImportError:
            self.stdout.write("مدل‌های هنرمندان یافت نشد.")
            return {
                'error': 'مدل‌های هنرمندان یافت نشد.',
            }

    def generate_financial_report(self, start_date, end_date):
        """تولید گزارش مالی"""
        self.stdout.write("تولید گزارش مالی...")

        try:
            # تلاش برای واردسازی مدل‌های مورد نیاز
            from apps.orders.models import Order
            from apps.payments.models import Payment, Commission

            # درآمد کل در بازه زمانی
            total_revenue = Order.objects.filter(
                status='completed',
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            # درآمد کمیسیون
            commission_revenue = Commission.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(total=Sum('amount'))['total'] or 0

            # تراکنش‌های موفق
            successful_payments = Payment.objects.filter(
                status='successful',
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            # تراکنش‌های ناموفق
            failed_payments = Payment.objects.filter(
                status='failed',
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            # نسبت موفقیت پرداخت
            total_payment_attempts = successful_payments.count() + failed_payments.count()
            payment_success_rate = (
                        successful_payments.count() / total_payment_attempts * 100) if total_payment_attempts > 0 else 0

            # درآمد بر اساس روش پرداخت
            revenue_by_method = {}
            method_stats = successful_payments.values('method').annotate(
                total=Sum('amount')
            )
            for item in method_stats:
                if item['method']:
                    revenue_by_method[item['method']] = item['total']

            # درآمد بر اساس ماه
            revenue_by_month = {}
            for payment in successful_payments:
                month = payment.created_at.strftime('%Y-%m')
                if month not in revenue_by_month:
                    revenue_by_month[month] = 0
                revenue_by_month[month] += payment.amount

            # ساخت دیکشنری نتیجه
            report = {
                'total_revenue': total_revenue,
                'commission_revenue': commission_revenue,
                'successful_payments': successful_payments.count(),
                'failed_payments': failed_payments.count(),
                'payment_success_rate': payment_success_rate,
                'revenue_by_method': revenue_by_method,
                'revenue_by_month': revenue_by_month,
            }

            return report

        except ImportError:
            self.stdout.write("مدل‌های مالی یافت نشد.")
            return {
                'error': 'مدل‌های مالی یافت نشد.',
            }

    def save_report(self, report_data, output_path, report_format, report_type):
        """ذخیره گزارش در فرمت مشخص شده"""
        if report_data is None:
            return

        # ایجاد مسیر در صورت نیاز
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # تغییر نام فایل برای گزارش‌های متعدد
        base_path, ext = os.path.splitext(output_path)
        if report_type != 'all':
            output_path = f"{base_path}_{report_type}{ext}"

        if report_format == 'csv':
            self.save_as_csv(report_data, output_path, report_type)
        elif report_format == 'json':
            self.save_as_json(report_data, output_path)
        elif report_format == 'html':
            self.save_as_html(report_data, output_path, report_type)
        elif report_format == 'text':
            self.save_as_text(report_data, output_path, report_type)

    def save_as_csv(self, report_data, output_path, report_type):
        """ذخیره گزارش به صورت CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # نوشتن سرصفحه
            writer.writerow(['شاخص', 'مقدار'])

            # نوشتن داده‌ها
            for key, value in report_data.items():
                if isinstance(value, dict):
                    writer.writerow([key, ''])
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"  {sub_key}", sub_value])
                elif isinstance(value, list):
                    writer.writerow([key, f"{len(value)} items"])
                    if value and isinstance(value[0], dict):
                        # نوشتن سرصفحه برای لیست اشیاء
                        headers = ['ردیف'] + list(value[0].keys())
                        writer.writerow(headers)
                        for i, item in enumerate(value, 1):
                            writer.writerow([i] + list(item.values()))
                else:
                    writer.writerow([key, value])

    def save_as_json(self, report_data, output_path):
        """ذخیره گزارش به صورت JSON"""
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(report_data, jsonfile, ensure_ascii=False, indent=2)

    def save_as_html(self, report_data, output_path, report_type):
        """ذخیره گزارش به صورت HTML"""
        # قالب HTML ساده برای گزارش
        html_template = """<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>گزارش {{ report_type }}</title>
    <style>
        body {
            font-family: 'Vazir', 'Tahoma', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            direction: rtl;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        h1, h2 {
            color: #2c3e50;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: right;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .section {
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>گزارش {{ report_title }}</h1>

        <div class="section">
            <table>
                <tr><th>شاخص</th><th>مقدار</th></tr>
                {% for key, value in report_data.items() %}
                    {% if key != 'error' and not isinstance(value, dict) and not isinstance(value, list) %}
                        <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
                    {% endif %}
                {% endfor %}
            </table>
        </div>

        {% for key, value in report_data.items() %}
            {% if isinstance(value, dict) %}
                <div class="section">
                    <h2>{{ key }}</h2>
                    <table>
                        <tr><th>شاخص</th><th>مقدار</th></tr>
                        {% for sub_key, sub_value in value.items() %}
                            <tr><td>{{ sub_key }}</td><td>{{ sub_value }}</td></tr>
                        {% endfor %}
                    </table>
                </div>
            {% elif isinstance(value, list) and value %}
                <div class="section">
                    <h2>{{ key }}</h2>
                    <table>
                        <tr>
                            <th>ردیف</th>
                            {% for header in value[0].keys() %}
                                <th>{{ header }}</th>
                            {% endfor %}
                        </tr>
                        {% for i, item in enumerate(value, 1) %}
                            <tr>
                                <td>{{ i }}</td>
                                {% for v in item.values() %}
                                    <td>{{ v }}</td>
                                {% endfor %}
                            </tr>
                        {% endfor %}
                    </table>
                </div>
            {% endif %}
        {% endfor %}
    </div>
</body>
</html>"""

        # تعیین عنوان گزارش بر اساس نوع آن
        report_titles = {
            'users': 'کاربران',
            'products': 'محصولات و آثار هنری',
            'sales': 'فروش و سفارشات',
            'artists': 'هنرمندان',
            'financial': 'مالی',
            'all': 'جامع',
        }

        report_title = report_titles.get(report_type, report_type)

        # جایگزینی متغیرها در قالب
        html_content = html_template.replace('{{ report_type }}', report_type)
        html_content = html_content.replace('{{ report_title }}', report_title)

        # پردازش بخش‌های قالب
        for key, value in report_data.items():
            if key != 'error':
                placeholder = f"{{ {key} }}"
                if isinstance(value, (dict, list)):
                    html_content = html_content.replace(placeholder, str(value))
                else:
                    html_content = html_content.replace(placeholder, str(value))

        # تعریف تابع isinstance برای استفاده در قالب
        html_content = html_content.replace('{% if isinstance(value, dict) %}', '{% if value is mapping %}')
        html_content = html_content.replace('{% if isinstance(value, list) %}',
                                            '{% if value is sequence and value is not string %}')
        html_content = html_content.replace(
            '{% if key != \'error\' and not isinstance(value, dict) and not isinstance(value, list) %}',
            '{% if key != \'error\' and value is not mapping and (value is not sequence or value is string) %}')

        # ذخیره فایل HTML
        with open(output_path, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(html_content)

    def save_as_text(self, report_data, output_path, report_type):
        """ذخیره گزارش به صورت متن ساده"""
        with open(output_path, 'w', encoding='utf-8') as textfile:
            textfile.write(f"گزارش {report_type}\n")
            textfile.write("=" * 50 + "\n\n")

            def write_dict(data, indent=0):
                for key, value in data.items():
                    if isinstance(value, dict):
                        textfile.write(f"{' ' * indent}{key}:\n")
                        write_dict(value, indent + 2)
                    elif isinstance(value, list):
                        textfile.write(f"{' ' * indent}{key} ({len(value)} items):\n")
                        for i, item in enumerate(value, 1):
                            if isinstance(item, dict):
                                textfile.write(f"{' ' * (indent + 2)}Item {i}:\n")
                                write_dict(item, indent + 4)
                            else:
                                textfile.write(f"{' ' * (indent + 2)}Item {i}: {item}\n")
                    else:
                        textfile.write(f"{' ' * indent}{key}: {value}\n")

            write_dict(report_data)

    def send_report_email(self, email, report_data, report_type, start_date, end_date, output_path):
        """ارسال گزارش به ایمیل"""
        self.stdout.write(f"ارسال گزارش به {email}...")

        # تعیین عنوان گزارش بر اساس نوع آن
        report_titles = {
            'users': 'کاربران',
            'products': 'محصولات و آثار هنری',
            'sales': 'فروش و سفارشات',
            'artists': 'هنرمندان',
            'financial': 'مالی',
            'all': 'جامع',
        }

        report_title = report_titles.get(report_type, report_type)

        # ساخت متن ایمیل
        subject = f"گزارش {report_title} Ma2tA - {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')}"
        message = f"""سلام،

گزارش {report_title} برای دوره زمانی {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')} به پیوست ارسال می‌شود.

این گزارش به صورت خودکار توسط سیستم تولید شده است.

با احترام،
تیم Ma2tA
"""

        # ساخت ایمیل
        email_message = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )

        # پیوست کردن فایل گزارش
        with open(output_path, 'rb') as f:
            file_name = os.path.basename(output_path)
            email_message.attach(file_name, f.read(), 'application/octet-stream')

        # ارسال ایمیل
        try:
            email_message.send()
            self.stdout.write(self.style.SUCCESS(f"گزارش با موفقیت به {email} ارسال شد."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطا در ارسال ایمیل: {str(e)}"))