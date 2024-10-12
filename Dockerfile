FROM python:3.11
ENV PYTHONUNBUFFERED 1
WORKDIR /jobPortal
COPY requirements.txt .
RUN pip install -r requirements.txt
# Copy toàn bộ mã nguồn vào container
COPY . .

## Tạo migrations và áp dụng chúng
#RUN python manage.py makemigrations
#RUN python manage.py migrate

# Sao chép script khởi động vào container
COPY entrypoint.sh /entrypoint.sh
# Cấp quyền thực thi cho script khởi động
RUN chmod +x /entrypoint.sh
# Thiết lập script khởi động là ENTRYPOINT
ENTRYPOINT ["/entrypoint.sh"]
#CMD  python manage.py runserver 0.0.0.0:8000
# Lệnh mặc định để chạy server Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

