#!/bin/bash
set -e

# Đợi cho MySQL sẵn sàng (tùy chỉnh thời gian đợi nếu cần)
echo "Waiting for MySQL to be ready..."
sleep 10

# Tạo và áp dụng migrations
echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

# Tạo superuser nếu chưa tồn tại
echo "Creating Django superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='mtie').exists():
    User.objects.create_superuser(
        username='mtie',
        email='mytien.2682003@gmail.com',
        password='m1234567890'
    )
EOF

# Tạo dữ liệu mẫu
echo "Creating sample data..."
python scripts/seed_data.py



# Khởi động server Django
echo "Starting Django server..."

# DÙNG CHO DOCKER ; JENKINS CI/CD
#exec "$@"

# DÙNG CHO DEPLOY
exec gunicorn jobPortal.wsgi:application --log-file -
