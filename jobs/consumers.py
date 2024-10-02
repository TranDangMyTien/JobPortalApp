import json
from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser
from oauth2_provider.models import AccessToken
from asgiref.sync import async_to_sync
from .models import Chat, Message

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # Accept WebSocket connection
        self.accept()

        # Lấy token từ URL query string
        query_string = self.scope['query_string'].decode()
        token = query_string.split('token=')[1] if 'token=' in query_string else None

        # Xác thực token và lưu thông tin người dùng vào self.scope['user']
        user = self.get_user_from_token(token)
        self.scope['user'] = user

        # Kiểm tra nếu token không hợp lệ hoặc người dùng không đăng nhập thì từ chối kết nối
        if isinstance(user, AnonymousUser):
            self.close()
            raise DenyConnection("Authentication required")

        # Lấy chat_id từ URL
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id', None)
        if not self.chat_id:
            self.close()
            raise DenyConnection("Missing chat_id")

        # Tạo tên nhóm chat từ chat_id
        self.chat_group_name = f'chat_{self.chat_id}'

        # Tham gia vào group chat
        async_to_sync(self.channel_layer.group_add)(
            self.chat_group_name,
            self.channel_name
        )

    def disconnect(self, close_code):
        # Rời khỏi group chat nếu có self.chat_group_name
        if hasattr(self, 'chat_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.chat_group_name,
                self.channel_name
            )

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', None)
        user = self.scope.get('user', None)

        if not user or not user.is_authenticated:
            self.send(text_data=json.dumps({
                'error': 'You must be logged in to send messages.'
            }))
            return

        if not message:
            self.send(text_data=json.dumps({
                'error': 'Empty message cannot be sent.'
            }))
            return

        try:
            chat = Chat.objects.get(id=self.chat_id)
            new_message = Message.objects.create(chat=chat, sender=user, text=message)
            async_to_sync(self.channel_layer.group_send)(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': user.username,
                    'created_at': new_message.created_at.isoformat(),
                }
            )
        except Chat.DoesNotExist:
            self.send(text_data=json.dumps({
                'error': 'Chat not found.'
            }))
            return


    def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        created_at = event['created_at']

        self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'created_at': created_at,
        }))

    def get_user_from_token(self, token):
        # Xác thực token và lấy user
        if not token:
            return AnonymousUser()  # Trả về AnonymousUser nếu không có token
        try:
            access_token = AccessToken.objects.get(token=token)
            return access_token.user
        except AccessToken.DoesNotExist:
            return AnonymousUser()  # Trả về AnonymousUser nếu token không tồn tại
