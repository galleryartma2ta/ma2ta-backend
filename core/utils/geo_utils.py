# core/utils/geo_utils.py

import math
import requests
import logging
from typing import Tuple, Dict, Optional, List
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

logger = logging.getLogger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float,
                       unit: str = 'km') -> float:
    """
    محاسبه فاصله بین دو نقطه جغرافیایی با استفاده از فرمول هاورساین.

    Args:
        lat1: عرض جغرافیایی نقطه اول (درجه)
        lon1: طول جغرافیایی نقطه اول (درجه)
        lat2: عرض جغرافیایی نقطه دوم (درجه)
        lon2: طول جغرافیایی نقطه دوم (درجه)
        unit: واحد اندازه‌گیری ('km' یا 'm')

    Returns:
        float: فاصله بین دو نقطه در واحد مشخص شده
    """
    # تبدیل درجه به رادیان
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # اختلاف طول و عرض جغرافیایی
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # فرمول هاورساین
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # شعاع کره زمین (کیلومتر)
    radius = 6371.0

    # محاسبه فاصله
    distance = radius * c

    # تبدیل واحد
    if unit == 'm':
        distance *= 1000

    return distance


def get_nearby_objects(queryset, lat: float, lon: float,
                       distance_km: float, location_field: str = 'location'):
    """
    یافتن اشیاء نزدیک به یک موقعیت جغرافیایی.

    Args:
        queryset: کوئری اشیاء
        lat: عرض جغرافیایی مرکز جستجو
        lon: طول جغرافیایی مرکز جستجو
        distance_km: حداکثر فاصله (کیلومتر)
        location_field: نام فیلد موقعیت در مدل

    Returns:
        QuerySet: اشیاء نزدیک به موقعیت با فاصله مشخص شده
    """
    user_location = Point(lon, lat, srid=4326)
    distance_m = distance_km * 1000

    # فیلتر کردن اشیاء بر اساس فاصله
    return queryset.filter(**{
        f"{location_field}__distance_lte": (user_location, Distance(m=distance_m))
    }).distance(user_location).order_by('distance')


def get_coordinates_from_address(address: str) -> Optional[Tuple[float, float]]:
    """
    دریافت مختصات جغرافیایی از آدرس با استفاده از سرویس‌های ژئوکدینگ.

    Args:
        address: آدرس مورد نظر

    Returns:
        Optional[Tuple[float, float]]: مختصات (عرض و طول جغرافیایی) یا None در صورت عدم موفقیت
    """
    # API کلید OpenStreetMap Nominatim
    nominatim_url = "https://nominatim.openstreetmap.org/search"

    try:
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }

        headers = {
            'User-Agent': 'Ma2tA/1.0'
        }

        response = requests.get(nominatim_url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon

        return None

    except Exception as e:
        logger.error(f"خطا در دریافت مختصات از آدرس: {str(e)}")
        return None


def get_city_province(lat: float, lon: float) -> Optional[Dict[str, str]]:
    """
    دریافت نام شهر و استان بر اساس مختصات جغرافیایی.

    Args:
        lat: عرض جغرافیایی
        lon: طول جغرافیایی

    Returns:
        Optional[Dict[str, str]]: دیکشنری شامل شهر و استان یا None در صورت عدم موفقیت
    """
    # API کلید OpenStreetMap Nominatim برای معکوس ژئوکدینگ
    nominatim_url = "https://nominatim.openstreetmap.org/reverse"

    try:
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1
        }

        headers = {
            'User-Agent': 'Ma2tA/1.0'
        }

        response = requests.get(nominatim_url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        if 'address' in data:
            address = data['address']
            city = address.get('city') or address.get('town') or address.get('village') or address.get('hamlet')
            province = address.get('state') or address.get('province')

            if city or province:
                return {
                    'city': city,
                    'province': province
                }

        return None

    except Exception as e:
        logger.error(f"خطا در دریافت شهر و استان از مختصات: {str(e)}")
        return None


def get_iran_provinces() -> List[str]:
    """
    دریافت لیست استان‌های ایران.

    Returns:
        List[str]: لیست استان‌های ایران
    """
    return [
        'آذربایجان شرقی',
        'آذربایجان غربی',
        'اردبیل',
        'اصفهان',
        'البرز',
        'ایلام',
        'بوشهر',
        'تهران',
        'چهارمحال و بختیاری',
        'خراسان جنوبی',
        'خراسان رضوی',
        'خراسان شمالی',
        'خوزستان',
        'زنجان',
        'سمنان',
        'سیستان و بلوچستان',
        'فارس',
        'قزوین',
        'قم',
        'کردستان',
        'کرمان',
        'کرمانشاه',
        'کهگیلویه و بویراحمد',
        'گلستان',
        'گیلان',
        'لرستان',
        'مازندران',
        'مرکزی',
        'هرمزگان',
        'همدان',
        'یزد'
    ]