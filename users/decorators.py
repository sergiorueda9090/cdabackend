from functools                  import wraps
from rest_framework.response    import Response
from rest_framework             import status

def check_role(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Validar si el idrol del usuario está en los roles permitidos
            if not user.idrol or user.idrol.id not in allowed_roles:
                return Response(
                    {"error": "No tienes permisos para acceder a este recurso."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Si pasa la validación, ejecutamos la vista original
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator