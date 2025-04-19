"""
واردکننده تنظیمات Django با انتخاب خودکار محیط.
"""

import os

# انتخاب فایل تنظیمات بر اساس متغیر محیطی
environment = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *  # noqa
elif environment == 'test':
    from .test import *  # noqa
else:
    from .development import *  # noqa