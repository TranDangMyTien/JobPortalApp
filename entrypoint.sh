#!/bin/bash
set -e

# Đợi cho MySQL sẵn sàng (tùy chỉnh thời gian đợi nếu cần)
echo "Waiting for MySQL to be ready..."
sleep 10

# Tạo và áp dụng migrations
echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

## Hàm để kiểm tra và tạo cơ sở dữ liệu nếu chưa tồn tại
#create_database() {
#    local db_name="$DATABASE_NAME"
#    local db_user="$DATABASE_USER"
#    local db_password="$DATABASE_PASSWORD"
#    local db_host=""
#
#    # Kiểm tra nếu cơ sở dữ liệu đã tồn tại
#    if ! mysql -h "$db_host" -u "$db_user" -p"$db_password" -e "USE $db_name"; then
#        echo "Database $db_name does not exist. Creating..."
#        mysql -h "$db_host" -u "$db_user" -p"$db_password" -e "CREATE DATABASE $db_name"
#    else
#        echo "Database $db_name already exists."
#    fi
#}
#
## Tạo cơ sở dữ liệu
#create_database


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
exec "$@"
