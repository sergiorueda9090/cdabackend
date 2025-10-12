import requests
from decouple import config
from django.core.mail import send_mail, BadHeaderError, EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import datetime

def enviar_mensaje_whatsapp(telefono, mensaje):
    """
    Envía un mensaje de WhatsApp utilizando el API de Meta.
    """
    try:
        # Configuración del token y la URL
        access_token = config("TOKEN_WHATSAPP")
        url = "https://graph.facebook.com/v21.0/251081758099306/messages"
        mensaje = ""
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

def enviar_documento_whatsapp(telefono, link_documento, caption=None):
    """
    Envía un documento PDF (u otro archivo soportado) por WhatsApp utilizando el API de Meta.
    """
    try:
        # Configuración del token y la URL
        access_token = config("TOKEN_WHATSAPP")
        url_ws       = config("URL_WHATSAPP")
        url = url_ws #"https://graph.facebook.com/v21.0/251081758099306/messages"

        if not caption:
            caption = "📑 CDA Movilidad 2A le envía el soporte ✅."


        # Validación básica
        if not telefono or not link_documento:
            return {"error": "El número de teléfono y el link del documento son obligatorios."}
        print("whatsapp numero ",telefono)
        # Estructura del payload
        payload = {
            "messaging_product": "whatsapp",
            "to": telefono,
            "type": "document",
            "document": {
                "link": link_documento,
                "caption": caption
            }
        }

        # Headers para la solicitud
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Envío de la solicitud
        response = requests.post(url, headers=headers, json=payload)
        print("Código de estado:", response.status_code)
        print("Cuerpo de la respuesta:", response.json())

        if response.status_code == 200:
            return {"success": True, "message": "Documento enviado correctamente."}
        else:
            return {
                "success": False,
                "error": "Error al enviar el documento.",
                "details": response.json(),
            }

    except Exception as e:
        return {"success": False, "error": f"Excepción ocurrida: {str(e)}"}
    

# def send_email(email, pdf):
#     """
#     Envía un correo HTML con link al PDF usando WorkMail SMTP
#     """
#     subject = 'CDA Movilidad 2 A'
#     from_email = 'tramites@movilidad2a.com'
#     to = [email]

#     # Renderiza plantilla HTML (puedes crear tu archivo email_template.html)
#     html_content = render_to_string('email_template.html', {'pdf_url': pdf})

#     try:
#         # Crear correo con HTML
#         msg = EmailMultiAlternatives(subject, 'Si no puedes ver el correo, revisa en HTML', from_email, to)
#         msg.attach_alternative(html_content, "text/html")
#         msg.send(fail_silently=False)
#         print("Correo enviado correctamente")
#         return True
#     except BadHeaderError:
#         print("Error: encabezado inválido en el correo")
#         return False
#     except Exception as e:
#         print(f"Error al enviar correo: {e}")
#         return False


def send_email(email, pdf_url, placa_te):
    subject = f'Placa {placa_te} - SOAT emitido con éxito'
    from_email = 'tramites@movilidad2a.com'
    to = [email]

    html_content = render_to_string('email_template.html', {
        'placa': placa_te,
        'year': datetime.now().year,
    })

    try:
        headers = {'Accept-Encoding': 'identity'}  # evita compresión
        response = requests.get(pdf_url, stream=True, headers=headers)
        response.raise_for_status()

        # Validar tipo de contenido
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            print("⚠️ El archivo no parece un PDF válido. Tipo:", content_type)

        pdf_content = response.content
        print("✅ Tamaño del PDF descargado:", len(pdf_content), "bytes")

        # Crear correo
        msg = EmailMultiAlternatives(subject, 'SOAT emitido con éxito', from_email, to)
        msg.attach_alternative(html_content, "text/html")

        # Adjuntar el PDF correctamente como binario
        msg.attach(f"SOAT_{placa_te}.pdf", pdf_content, "application/pdf")

        msg.send(fail_silently=False)
        print("✅ Correo enviado correctamente")
        return True

    except BadHeaderError:
        print("❌ Error: encabezado inválido en el correo")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar el PDF: {e}")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

    return False