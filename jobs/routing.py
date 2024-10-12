from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
# ws://localhost:8000/ws/chat/1/
# localhost:8000 là địa chỉ máy chủ chạy Django.
# ws là giao thức WebSocket.
# /ws/chat/1/ là endpoint WebSocket mà bạn đã cấu hình (với chat_id là 1).

# ws://192.168.1.7:8000/ws/chat/1/
# ws://localhost:8000/ws/chat/{chat_id}/?token=YOUR_ACCESS_TOKEN