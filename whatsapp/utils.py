import requests
from decouple import config

def enviar_mensaje_whatsapp(telefono, mensaje):
    """
    Envía un mensaje de WhatsApp utilizando el API de Meta.
    """
    try:
        # Configuración del token y la URL
        access_token = config("TOKEN_WHATSAPP")
        url = "https://graph.facebook.com/v21.0/251081758099306/messages"

        # Validación básica
        if not telefono or not mensaje:
            return {"error": "El número de teléfono y el mensaje son obligatorios."}

        # Estructura del payload
        payload = {
            "messaging_product": "whatsapp",
            "preview_url": False,
            "recipient_type": "individual",
            "to": telefono,
            "type": "text",
            "text": {"body": mensaje},
        }

        # Headers para la solicitud
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Envío de la solicitud
        response = requests.post(url, headers=headers, json=payload)
        # Imprimir respuesta completa
        print("Código de estado:", response.status_code)
        print("Cuerpo de la respuesta:", response.json())
        # Verificar la respuesta
        if response.status_code == 200:
            return {"success": True, "message": "Mensaje enviado correctamente."}
        else:
            return {
                "success": False,
                "error": "Error al enviar el mensaje.",
                "details": response.json(),
            }

    except Exception as e:
        return {"success": False, "error": f"Excepción ocurrida: {str(e)}"}
