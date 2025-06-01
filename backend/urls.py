"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include


from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test CDA",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="sergiorueda90@hotmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
)


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns = [
   path('docs/',                schema_view.with_ui('swagger', cache_timeout=0) , name='schema-swagger-ui'),
   path('redoc/',               schema_view.with_ui('redoc', cache_timeout=0)   , name='schema-redoc'),
   path('admin/',               admin.site.urls),
   path('auth/',                TokenObtainPairView.as_view()                   , name='token_obtain_pair'),
   path('auth/refresh/',        TokenRefreshView.as_view()                      , name='token_refresh'),
   path('users/',               include('users.api.urls')                       , name="users"),
   path('clientes/',            include('clientes.api.urls')                    , name="clientes"),
   path('cotizador/',           include('cotizador.api.urls')                   , name="cotizador"),
   path('tramites/',            include('tramites.api.urls')                    , name="tramites"),
   path('etiquetas/',           include('etiquetas.api.urls')                   , name="etiquetas"),
   path('cuentasbancarias/',    include('cuentasbancarias.api.urls')            , name="cuentasbancarias"),
   path('registrotarjetas/',    include('registroTarjetas.api.urls')            , name="registrotarjetas"),
   path('recepcionpago/',       include('recepcionPago.api.urls')               , name="recepcionpago"),
   path('devolucion/',          include('devoluciones.api.urls')                , name="devoluciones"),
   path('ajustessaldo/',        include('ajustesaldos.api.urls')                , name="ajustesaldos"),
   path('gastos/',              include('gastos.api.urls')                      , name="gastos"),
   path('gastosgenerales/',     include('gastosgenerales.api.urls')             , name="gastosgenerales"),
   path('utilidadocacional/',   include('utilidadocacional.api.urls')           , name="utilidadocacional"),
   path('downloadpdf/',         include('cuentasbancarias.urls')                , name="downloadpdf"),
   path('fichacliente/',        include('fichacliente.api.urls')                , name="fichacliente"),
   path('archivocotizacionesantiguas/', include('archivocotizacionesantiguas.api.urls'),     name="archivocotizacionesantiguas"),
   path('historialtramitesemitidos/',   include('historialtramitesemitidos.api.urls'),        name="historialtramitesemitidos"),
   path('proveedores/',         include('proveedores.api.urls')                 , name="proveedores"),
   path('fichaproveedores/',    include('fichaproveedor.api.urls'),               name="fichaproveedor"),
   path('permisos/',            include('rolespermisos.api.urls'),                name="rolespermisos"),
   path('balancegeneral/',      include('balancegeneral.api.urls'),               name="balancegeneral"),
   path('utilidad/',            include('utilidad.api.urls'),                     name="utilidad"),
]

# Servir archivos de media en modo debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)