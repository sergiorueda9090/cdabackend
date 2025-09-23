#from .models import Room, Message  # new import
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
#from django.contrib.auth import get_user_model
import logging
logger = logging.getLogger(__name__)

class ChatConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 👈 pequeño fix, antes tenías (args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None

    def connect(self):
        from .models import Room, Message
        from django.contrib.auth import get_user_model  # ✅ lazy
        User = get_user_model()
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.room = Room.objects.get(name=self.room_name)
        self.user = self.scope['user']

        self.accept()

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        if self.user.is_authenticated:
            # Agregar usuario a la lista online
            self.room.online.add(self.user)
            print("🔑 Usuario conectado:", self.user, self.user.is_authenticated)
            # Enviar lista actualizada a todos
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "user_list",
                    "users": [u.username for u in self.room.online.all()],
                }
            )

    def disconnect(self, close_code):
        from .models import Room, Message
        from django.contrib.auth import get_user_model  # ✅ lazy
        User = get_user_model()
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

        if self.user.is_authenticated:
            # Notificar que salió
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "user_leave",
                    "user": self.user.username,
                }
            )
            self.room.online.remove(self.user)

    def receive(self, text_data=None, bytes_data=None):
        from .models import Room, Message
        from django.contrib.auth import get_user_model  # ✅ lazy
        User = get_user_model()
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        if not self.user.is_authenticated:
            return

        # Mensaje privado
        if message.startswith("/pm "):
            split = message.split(" ", 2)
            target = split[1]
            target_msg = split[2]

            # Mandar al inbox del target
            async_to_sync(self.channel_layer.group_send)(
                f"inbox_{target}",
                {
                    "type": "private_message",
                    "user": self.user.username,
                    "message": target_msg,
                }
            )
            # Confirmar al remitente
            self.send(json.dumps({
                "type": "private_message_delivered",
                "target": target,
                "message": target_msg,
            }))
            return

        # Mensaje normal al grupo
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat_message",
                "user": self.user.username,
                "message": message,
            }
        )
        Message.objects.create(user=self.user, room=self.room, content=message)

    # Handlers para eventos de grupo
    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))

    def user_list(self, event):
        users_data = []
        for u in self.room.online.all():
            users_data.append({
                "username": u.username,
                "image": getattr(u.profile, "image", None).url if hasattr(u, "profile") and u.profile.image else "/static/default-avatar.png"
            })

        self.send(text_data=json.dumps({
            "type": "user_list",
            "users": users_data,
        }))

    def private_message(self, event):
        self.send(text_data=json.dumps(event))

    def private_message_delivered(self, event):
        self.send(text_data=json.dumps(event))



class TableConsumer(WebsocketConsumer):
    def connect(self):
        token = self.scope['query_string'].decode().split('=')[1]  # tu token JWT
        # Aquí normalmente validas el token y obtienes el usuario
        from django.contrib.auth import get_user_model
        import jwt
        from django.conf import settings

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            User = get_user_model()
            self.user = User.objects.get(id=user_id)
        except:
            self.close()
            return

        self.group_name = "table_group"
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        event_type = data.get("type")
        print("📥 Evento recibido en backend:", event_type, data)
        if event_type == "cell_click":
            print("📤 cell_click recibido en backend:", data)
            row_id = data.get("rowId")
            column = data.get("column")
            # Enviar evento a todos los clientes del grupo
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "cell_update",
                    "user": self.user.username,
                    "rowId": row_id,
                    "column": column,
                }
            )

        if event_type == "update_etiqueta":
            row_id     = data.get("rowId")
            new_value  = data.get("value")
            user       = data.get("user")

            print("📤 update_etiqueta recibido en backend:", row_id, new_value)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "etiqueta_update",  # 👈 debe coincidir con el handler abajo
                    "user": user,
                    "rowId": row_id,
                    "value": new_value,
                }
            )

        if event_type == "update_link":
            row_id = data.get("rowId")
            new_value = data.get("value")
            user = data.get("user")

            print("📤 update_link recibido en backend:", row_id, new_value)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "link_update",
                    "user": user,
                    "rowId": row_id,
                    "value": new_value,
                }
            )

        if event_type == "copy_link":
            row_id = data.get("rowId")
            user = data.get("user")

            print(f"📤 copy_link recibido en backend: fila {row_id} por {user}")

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "link_copy_update",  # 👈 handler abajo
                    "user": user,
                    "rowId": row_id,
                }
            )

        if event_type == "stop_loading":
            row_id = data.get("rowId")
            user = data.get("user")

            print(f"📤 stop_loading recibido en backend: fila {row_id} por {user}")

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "loading_stop_update",  # 👈 nuevo handler abajo
                    "user": user,
                    "rowId": row_id,
                }
            )

        if event_type == "update_email":
            row_id = data.get("rowId")
            new_value = data.get("value")
            user = data.get("user")

            print("📤 update_email recibido en backend:", row_id, new_value)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "email_update",
                    "user": user,
                    "rowId": row_id,
                    "value": new_value,
                }
            )

        if event_type == "refresh_request":
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "refresh_order",
                }
            )
    
    # Este método se llama para todos los clientes del grupo
    def cell_update(self, event):
        self.send(text_data=json.dumps({
            "type": "cell_click",
            "user": event["user"],
            "rowId": event["rowId"],
            "column": event["column"],
        }))

    def etiqueta_update(self, event):
        self.send(text_data=json.dumps({
            "type": "update_etiqueta",
            "user": event["user"],
            "rowId": event["rowId"],
            "value": event["value"],
        }))

    def link_update(self, event):
        self.send(text_data=json.dumps({
            "type": "update_link",
            "user": event["user"],
            "rowId": event["rowId"],
            "value": event["value"],
        }))

    def link_copy_update(self, event):
        self.send(text_data=json.dumps({
            "type": "copy_link",
            "user": event["user"],
            "rowId": event["rowId"],
        }))

    def loading_stop_update(self, event):
        self.send(text_data=json.dumps({
            "type": "stop_loading",
            "user": event["user"],
            "rowId": event["rowId"],
        }))

    def email_update(self, event):
        self.send(text_data=json.dumps({
            "type": "update_email",
            "user": event["user"],
            "rowId": event["rowId"],
            "value": event["value"],
        }))

    def refresh_order(self, event):
        self.send(text_data=json.dumps({
            "type": "refresh_request",
        }))

"""from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()  # ❌ No autenticado
        else:
            await self.accept()  # ✅ Conectado
            await self.send(text_data=json.dumps({
                "message": f"Bienvenido {user.username}, estás autenticado 🎉"
            }))"""