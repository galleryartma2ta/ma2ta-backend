# Dockerfile

# ایمیج پایه Python
FROM python:3.11-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# نصب پکیج‌های مورد نیاز
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    gettext \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ایجاد دایرکتوری کاری
WORKDIR /app

# کپی requirements.txt
COPY requirements.txt .

# نصب پکیج‌های Python
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# کپی پروژه
COPY . .

# ایجاد یک کاربر غیر root
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# اکسپوز کردن پورت
EXPOSE 8000

# دستور پیش‌فرض
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]