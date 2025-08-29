"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Primero, establece la variable de entorno para las configuraciones de Django.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Luego, inicializa la aplicación ASGI de Django.
# Esto cargará las configuraciones de Django y el registro de aplicaciones.
django_asgi_app = get_asgi_application()

# Ahora que Django está configurado, puedes importar otros módulos
# que dependen de las configuraciones, como tus middlewares y routings.
from channels.routing import ProtocolTypeRouter, URLRouter
import cotizador.routing
from cotizador.middleware import JWTAuthMiddlewareStack # Ahora esta importación funcionará

application = ProtocolTypeRouter({
    "http": django_asgi_app, # Usa la aplicación ASGI de Django ya inicializada para HTTP
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(
            cotizador.routing.websocket_urlpatterns
        )
    ),
})
