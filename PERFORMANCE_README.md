# Guia de Optimizacion de Rendimiento — Backend CDA

Este documento detalla paso a paso las mejoras necesarias para resolver los problemas de rendimiento detectados en los endpoints del backend Django.

---

## Tabla de Contenidos

1. [Configuracion de Django (settings.py)](#1-configuracion-de-django)
2. [Eliminar problema N+1 en Cotizador](#2-eliminar-problema-n1-en-cotizador)
3. [Eliminar problema N+1 en Tramites](#3-eliminar-problema-n1-en-tramites)
4. [Agregar select_related en vistas con ForeignKey](#4-agregar-select_related-en-vistas-con-foreignkey)
5. [Optimizar balancegeneral](#5-optimizar-balancegeneral)
6. [Agregar indices a la base de datos](#6-agregar-indices-a-la-base-de-datos)
7. [Agregar prefetch_related en Clientes](#7-agregar-prefetch_related-en-clientes)
8. [Habilitar cache con Redis](#8-habilitar-cache-con-redis)
9. [Convertir IntegerField a ForeignKey](#9-convertir-integerfield-a-foreignkey)
10. [Convertir campos monetarios TextField a DecimalField](#10-convertir-campos-monetarios-textfield-a-decimalfield)
11. [Optimizar importacion masiva desde Excel](#11-optimizar-importacion-masiva-desde-excel)
12. [Usar bulk_create para logs](#12-usar-bulk_create-para-logs)
13. [Eliminar print() de produccion](#13-eliminar-print-de-produccion)
14. [Monitoreo y validacion](#14-monitoreo-y-validacion)

---

## 1. Configuracion de Django

**Archivo:** `backend/settings.py`

**Impacto:** Alto — afecta todas las peticiones sin cambiar codigo de vistas.

### Paso 1.1 — Connection Pooling

Agregar `CONN_MAX_AGE` para reutilizar conexiones MySQL en lugar de abrir/cerrar una por cada request:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT'),
        'CONN_MAX_AGE': 60,  # <-- AGREGAR: reutilizar conexiones por 60 segundos
    }
}
```

### Paso 1.2 — Paginacion Global

Agregar paginacion por defecto a todos los endpoints de listado:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}
```

> **Nota:** Los endpoints que construyen respuestas manualmente (sin usar serializers de DRF) no se benefician automaticamente de esta configuracion. Para esos casos, ver paso 1.3.

### Paso 1.3 — Paginacion manual para vistas funcionales

Para las vistas que retornan listas construidas manualmente (como `get_cotizadores`), implementar paginacion manual:

```python
from rest_framework.pagination import PageNumberPagination

@api_view(['GET'])
def get_cotizadores(request):
    cotizadores = Cotizador.objects.filter(cotizadorModulo="1")

    paginator = PageNumberPagination()
    paginator.page_size = 50
    page = paginator.paginate_queryset(cotizadores, request)

    # construir data solo para los registros de la pagina actual
    data = []
    for cotizador in page:
        # ... construir item ...
        data.append(item)

    return paginator.get_paginated_response(data)
```

### Paso 1.4 — Verificar DEBUG en produccion

En el archivo `.env` de produccion, asegurar:

```
DEBUG=False
```

Con `DEBUG=True`, Django acumula todas las queries SQL en memoria, lo que agrava todos los demas problemas.

---

## 2. Eliminar problema N+1 en Cotizador

**Archivo:** `cotizador/api/views.py`

**Impacto:** Critico — pasa de ~3,001 queries a ~4 queries con 1,000 registros.

**Funciones afectadas:** `get_cotizadores`, `get_cotizadores_tramites`, `get_cotizadores_confirmacion_precios`, `get_cotizadores_pdfs`, `get_cotizadores_filter_date`, `get_cotizadores_trasabilidad_filter_date`, `get_cotizadores_confirmacion_filter_date`, `get_cotizadores_pdf_filter_date`, `search_cotizadores`.

### Paso 2.1 — Pre-cargar datos relacionados en diccionarios

**Antes (lento):**
```python
cotizadores = Cotizador.objects.filter(cotizadorModulo="1")
data = []
for cotizador in cotizadores:
    usuario = get_object_or_404(User, id=cotizador.idUsuario)       # 1 query por fila
    cliente = get_object_or_404(Cliente, id=cotizador.idCliente)     # 1 query por fila
    etiqueta = get_object_or_404(Etiqueta, id=cotizador.idEtiqueta) # 1 query por fila
    data.append({
        "usuario": usuario.username,
        "cliente": cliente.nombre,
        "etiqueta": etiqueta.nombre,
        ...
    })
```

**Despues (optimizado):**
```python
cotizadores = Cotizador.objects.filter(cotizadorModulo="1")

# Recolectar todos los IDs unicos
user_ids = set(cotizadores.values_list('idUsuario', flat=True))
cliente_ids = set(cotizadores.values_list('idCliente', flat=True))
etiqueta_ids = set(cotizadores.values_list('idEtiqueta', flat=True))

# Pre-cargar en diccionarios (3 queries en total, sin importar cuantos registros haya)
users_dict = {u.id: u for u in User.objects.filter(id__in=user_ids)}
clientes_dict = {c.id: c for c in Cliente.objects.filter(id__in=cliente_ids)}
etiquetas_dict = {e.id: e for e in Etiqueta.objects.filter(id__in=etiqueta_ids)}

data = []
for cotizador in cotizadores:
    usuario = users_dict.get(cotizador.idUsuario)
    cliente = clientes_dict.get(cotizador.idCliente)
    etiqueta = etiquetas_dict.get(cotizador.idEtiqueta)
    data.append({
        "usuario": usuario.username if usuario else None,
        "cliente": cliente.nombre if cliente else None,
        "etiqueta": etiqueta.nombre if etiqueta else None,
        ...
    })
```

### Paso 2.2 — Crear una funcion auxiliar reutilizable

Como el patron se repite en 8+ funciones, crear un helper:

```python
# cotizador/api/utils.py
from users.models import User
from clientes.models import Cliente
from etiquetas.models import Etiqueta


def preload_cotizador_relations(cotizadores_qs):
    """Pre-carga Users, Clientes y Etiquetas para un queryset de Cotizador."""
    user_ids = set(cotizadores_qs.values_list('idUsuario', flat=True))
    cliente_ids = set(cotizadores_qs.values_list('idCliente', flat=True))
    etiqueta_ids = set(cotizadores_qs.values_list('idEtiqueta', flat=True))

    return {
        'users': {u.id: u for u in User.objects.filter(id__in=user_ids)},
        'clientes': {c.id: c for c in Cliente.objects.filter(id__in=cliente_ids)},
        'etiquetas': {e.id: e for e in Etiqueta.objects.filter(id__in=etiqueta_ids)},
    }
```

Luego en cada vista:

```python
from cotizador.api.utils import preload_cotizador_relations

@api_view(['GET'])
def get_cotizadores(request):
    cotizadores = Cotizador.objects.filter(cotizadorModulo="1")
    relations = preload_cotizador_relations(cotizadores)

    for cotizador in cotizadores:
        usuario = relations['users'].get(cotizador.idUsuario)
        cliente = relations['clientes'].get(cotizador.idCliente)
        etiqueta = relations['etiquetas'].get(cotizador.idEtiqueta)
        # ...
```

### Paso 2.3 — Aplicar en todas las funciones afectadas

Repetir el patron para cada una de estas funciones:

- [ ] `get_cotizadores` (~linea 447)
- [ ] `get_cotizadores_tramites` (~linea 815)
- [ ] `get_cotizadores_confirmacion_precios` (~linea 847)
- [ ] `get_cotizadores_pdfs` (~linea 903)
- [ ] `get_cotizadores_filter_date` (~linea 489)
- [ ] `get_cotizadores_trasabilidad_filter_date` (~linea 951)
- [ ] `get_cotizadores_confirmacion_filter_date` (~linea 1015)
- [ ] `get_cotizadores_pdf_filter_date` (~linea 1079)
- [ ] `search_cotizadores` (~linea 533)

---

## 3. Eliminar problema N+1 en Tramites

**Archivo:** `tramites/api/views.py`

**Impacto:** Alto — mismo patron que cotizador.

### Paso 3.1 — Pre-cargar relaciones

**Antes:**
```python
tramites = Tramite.objects.all()
for tramite in tramites:
    usuario = get_object_or_404(User, id=tramite.idUsuario)
    cliente = get_object_or_404(Cliente, id=tramite.idCliente)
```

**Despues:**
```python
tramites = Tramite.objects.all()

user_ids = set(tramites.values_list('idUsuario', flat=True))
cliente_ids = set(tramites.values_list('idCliente', flat=True))

users_dict = {u.id: u for u in User.objects.filter(id__in=user_ids)}
clientes_dict = {c.id: c for c in Cliente.objects.filter(id__in=cliente_ids)}

for tramite in tramites:
    usuario = users_dict.get(tramite.idUsuario)
    cliente = clientes_dict.get(tramite.idCliente)
    # ...
```

### Paso 3.2 — Funciones afectadas

- [ ] `get_tramites` (~linea 62)
- [ ] Cualquier otra funcion de listado en tramites que siga el mismo patron

---

## 4. Agregar select_related en vistas con ForeignKey

**Impacto:** Alto — una linea de cambio por vista, elimina N queries.

Estas apps ya usan `ForeignKey` correctamente en sus modelos, pero las vistas no usan `select_related()`.

### Paso 4.1 — recepcionPago/api/views.py

```python
# ANTES
recepciones = RecepcionPago.objects.all()

# DESPUES
recepciones = RecepcionPago.objects.select_related(
    'cliente', 'id_tarjeta_bancaria'
).all()
```

Luego eliminar los `get_object_or_404` redundantes dentro del loop. El objeto relacionado ya esta cargado:

```python
# ANTES
for recepcion in recepciones:
    tarjeta = get_object_or_404(RegistroTarjetas, id=recepcion.id_tarjeta_bancaria_id)
    cliente = get_object_or_404(Cliente, id=recepcion.cliente_id)

# DESPUES
for recepcion in recepciones:
    tarjeta = recepcion.id_tarjeta_bancaria  # ya esta cargado por select_related
    cliente = recepcion.cliente               # ya esta cargado por select_related
```

**Funciones:** `listar_recepciones_pago`, `listar_recepciones_pago_filtradas`

### Paso 4.2 — devoluciones/api/views.py

```python
# DESPUES
devoluciones = Devoluciones.objects.select_related(
    'id_cliente', 'id_tarjeta_bancaria'
).all()
```

**Funciones:** `listar_devoluciones`, `listar_devoluciones_filtro`

### Paso 4.3 — ajustesaldos/api/views.py

```python
# DESPUES
ajustes = Ajustesaldo.objects.select_related('id_cliente').all()
```

**Funciones:** `listar_ajustessaldos`, `listar_ajustessaldo_filtradas`

### Paso 4.4 — gastosgenerales/api/views.py

```python
# DESPUES
gastos = Gastogenerales.objects.select_related(
    'id_tipo_gasto', 'id_tarjeta_bancaria'
).all()
```

Luego eliminar los `get_object_or_404` redundantes del loop:

```python
# ANTES (doble consulta innecesaria)
tarjeta_id = gasto.id_tarjeta_bancaria.pk
tarjeta = get_object_or_404(RegistroTarjetas, id=tarjeta_id)  # redundante

# DESPUES
tarjeta = gasto.id_tarjeta_bancaria  # ya esta cargado
```

**Funciones:** `listar_gastos_generales`, `listar_gastos_generales_filtradas`

### Paso 4.5 — utilidadocacional/api/views.py

```python
# DESPUES
utilidades = Utilidadocacional.objects.select_related('id_tarjeta_bancaria').all()
```

**Funciones:** `listar_utilidad_general`, `obtener_cutilidad_general_filtradas`

### Paso 4.6 — fichaproveedor/api/views.py

```python
# DESPUES
fichas = FichaProveedor.objects.select_related('idproveedor', 'idcotizador').all()
```

**Funciones:** `get_all_fecha_proveedores`, `get_ficha_proveedor_por_id`, `get_ficha_proveedor_por_id_total`

### Paso 4.7 — utilidad/api/views.py

```python
# DESPUES
fichas = FichaProveedor.objects.select_related('idproveedor', 'idcotizador').all()
```

**Funcion:** `get_ficha_utilidades`

---

## 5. Optimizar balancegeneral

**Archivo:** `balancegeneral/api/views.py`

**Impacto:** Critico — de 130+ queries a ~8 queries.

### Paso 5.1 — Reemplazar loop por queries agrupadas

**Antes (13 queries por tarjeta):**
```python
cuentas = RegistroTarjetas.objects.all()
for i in range(len(serializer.data)):
    tarjeta_id = serializer.data[i]['id']
    rtaRecepcionPago = RecepcionPago.objects.filter(
        id_tarjeta_bancaria=tarjeta_id
    ).aggregate(...)
    rtaDevoluciones = Devoluciones.objects.filter(
        id_tarjeta_bancaria=tarjeta_id
    ).aggregate(...)
    # ... 11 queries mas por tarjeta
```

**Despues (1 query agrupada por modelo):**
```python
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce, Replace, Cast

# UNA sola query por modelo, agrupada por tarjeta
recepciones_por_tarjeta = (
    RecepcionPago.objects
    .values('id_tarjeta_bancaria')
    .annotate(
        total=Sum(Cast(Replace('valor', Value('.'), Value('')), output_field=IntegerField()))
    )
)

devoluciones_por_tarjeta = (
    Devoluciones.objects
    .values('id_tarjeta_bancaria')
    .annotate(
        total=Sum(Cast(Replace('valor', Value('.'), Value('')), output_field=IntegerField()))
    )
)

# Convertir a diccionarios para acceso O(1)
recepciones_dict = {
    r['id_tarjeta_bancaria']: r['total'] or 0
    for r in recepciones_por_tarjeta
}
devoluciones_dict = {
    d['id_tarjeta_bancaria']: d['total'] or 0
    for d in devoluciones_por_tarjeta
}

# Repetir para: CuentaBancaria, Gastogenerales, Utilidadocacional,
# Tarjetastrasladofondo (envia y recibe), Cargosnodesados

# Luego iterar sobre tarjetas sin queries adicionales
for tarjeta in cuentas:
    total_recepciones = recepciones_dict.get(tarjeta.id, 0)
    total_devoluciones = devoluciones_dict.get(tarjeta.id, 0)
    # ...
```

### Paso 5.2 — Reemplazar sumas en Python por aggregates de BD

**Antes:**
```python
# safe_sum() — carga todos los valores en Python y suma en loop
def safe_sum(queryset, field_name):
    valores = queryset.values_list(field_name, flat=True)
    total = Decimal(0)
    for valor in valores:
        total += valor_decimal
    return total
```

**Despues:**
```python
from django.db.models import Sum, DecimalField
from django.db.models.functions import Cast, Replace, Coalesce

def safe_sum(queryset, field_name):
    result = queryset.aggregate(
        total=Coalesce(
            Sum(Cast(Replace(field_name, Value('.'), Value('')), output_field=DecimalField())),
            Value(0)
        )
    )
    return result['total']
```

### Paso 5.3 — Optimizar calcular_total_tarjetas y calcular_total_cuatro_por_mil

Estas funciones hacen loops adicionales sobre tarjetas. Aplicar el mismo patron de queries agrupadas del paso 5.1 y reutilizar los diccionarios ya calculados.

---

## 6. Agregar indices a la base de datos

**Impacto:** Medio-alto — acelera todas las consultas de filtrado y joins.

### Paso 6.1 — Cotizador (cotizador/models.py)

```python
class Cotizador(models.Model):
    idUsuario  = models.IntegerField(db_index=True)    # agregar db_index
    idCliente  = models.IntegerField(db_index=True)    # agregar db_index
    idEtiqueta = models.IntegerField(db_index=True)    # agregar db_index
    placa      = models.CharField(max_length=50, db_index=True)  # agregar db_index
    fechaCreacion = models.DateTimeField(db_index=True, ...)     # agregar db_index
    # ...
```

### Paso 6.2 — Tramite (tramites/models.py)

```python
class Tramite(models.Model):
    idUsuario     = models.IntegerField(db_index=True)
    idCliente     = models.IntegerField(db_index=True)
    placa         = models.CharField(max_length=50, db_index=True)
    fechaCreacion = models.DateTimeField(db_index=True, ...)
    # ...
```

### Paso 6.3 — CuentaBancaria (cuentasbancarias/models.py)

```python
class CuentaBancaria(models.Model):
    idCotizador = models.IntegerField(db_index=True)
    idBanco     = models.IntegerField(db_index=True)
    # ...
```

### Paso 6.4 — Generar y aplicar migraciones

```bash
python manage.py makemigrations cotizador tramites cuentasbancarias
python manage.py migrate
```

> **Nota:** En tablas grandes, agregar indices puede tomar unos minutos. Hacerlo en horario de bajo trafico.

---

## 7. Agregar prefetch_related en Clientes

**Archivo:** `clientes/api/views.py`

**Impacto:** Medio — elimina N+1 del serializer anidado `precios_ley`.

```python
# ANTES
clientes = Cliente.objects.all()

# DESPUES
clientes = Cliente.objects.prefetch_related('precios_ley').all()
```

Con 100 clientes: pasa de 101 queries a 2 queries.

---

## 8. Habilitar cache con Redis

**Impacto:** Alto para endpoints de reporte que recalculan todo el historial financiero.

### Paso 8.1 — Configurar cache en settings.py

Redis ya esta disponible en el proyecto (usado para Django Channels):

```bash
pip install django-redis
```

```python
# backend/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  # usar DB 1 (DB 0 es para Channels)
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 300,  # 5 minutos por defecto
    }
}
```

### Paso 8.2 — Cachear endpoints pesados

```python
from django.core.cache import cache

@api_view(['GET'])
def obtener_balancegeneral(request):
    cache_key = 'balance_general'
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    # ... calcular balance ...

    cache.set(cache_key, data, timeout=300)  # cache por 5 minutos
    return Response(data)
```

### Paso 8.3 — Invalidar cache cuando hay cambios

En las vistas de creacion/actualizacion de transacciones financieras, invalidar el cache:

```python
from django.core.cache import cache

@api_view(['POST'])
def crear_recepcion_pago(request):
    # ... crear recepcion ...
    cache.delete('balance_general')
    return Response(data)
```

Aplicar invalidacion en las vistas de escritura de: `recepcionPago`, `devoluciones`, `gastosgenerales`, `utilidadocacional`, `cuentasbancarias`, `tarjetastrasladofondo`.

---

## 9. Convertir IntegerField a ForeignKey

**Impacto:** Medio-largo plazo — habilita `select_related` nativo y mejora la integridad de datos.

### Paso 9.1 — Cotizador

```python
# ANTES
class Cotizador(models.Model):
    idUsuario  = models.IntegerField()
    idCliente  = models.IntegerField()
    idEtiqueta = models.IntegerField()

# DESPUES
class Cotizador(models.Model):
    idUsuario  = models.ForeignKey(User, on_delete=models.CASCADE, db_column='idUsuario')
    idCliente  = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='idCliente')
    idEtiqueta = models.ForeignKey(Etiqueta, on_delete=models.CASCADE, db_column='idEtiqueta')
```

> **Precaucion:** `db_column` preserva el nombre de columna existente para no romper datos. Verificar que no existan registros con IDs huerfanos antes de migrar (`SELECT * FROM cotizador WHERE idCliente NOT IN (SELECT id FROM clientes)`).

### Paso 9.2 — Tramite

```python
# DESPUES
class Tramite(models.Model):
    idUsuario = models.ForeignKey(User, on_delete=models.CASCADE, db_column='idUsuario')
    idCliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='idCliente')
```

### Paso 9.3 — CuentaBancaria

```python
# DESPUES
class CuentaBancaria(models.Model):
    idCotizador = models.ForeignKey(Cotizador, on_delete=models.CASCADE, db_column='idCotizador')
    idBanco     = models.ForeignKey(RegistroTarjetas, on_delete=models.CASCADE, db_column='idBanco')
```

### Paso 9.4 — Actualizar vistas

Despues de convertir a ForeignKey, las vistas pueden usar `select_related`:

```python
# Ahora esto es posible
cotizadores = Cotizador.objects.select_related(
    'idUsuario', 'idCliente', 'idEtiqueta'
).filter(cotizadorModulo="1")

for cotizador in cotizadores:
    nombre_usuario = cotizador.idUsuario.username   # sin query adicional
    nombre_cliente = cotizador.idCliente.nombre      # sin query adicional
```

### Paso 9.5 — Generar y aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

> **Nota:** Hacer backup de la base de datos antes de esta migracion. Probar primero en un entorno de desarrollo.

---

## 10. Convertir campos monetarios TextField a DecimalField

**Impacto:** Medio — elimina las conversiones Cast/Replace en cada aggregation.

### Paso 10.1 — Identificar modelos afectados

| Modelo | Campo | Archivo |
|---|---|---|
| RecepcionPago | `valor`, `cuatro_por_mil` | `recepcionPago/models.py` |
| Devoluciones | `valor`, `cuatro_por_mil` | `devoluciones/models.py` |
| Ajustesaldo | `valor` | `ajustesaldos/models.py` |
| Gastogenerales | `valor`, `cuatro_por_mil` | `gastosgenerales/models.py` |
| Utilidadocacional | `valor`, `cuatro_por_mil` | `utilidadocacional/models.py` |
| CuentaBancaria | `valor` | `cuentasbancarias/models.py` |

### Paso 10.2 — Cambiar tipo de campo

```python
# ANTES
valor = models.TextField(verbose_name="Valor")
cuatro_por_mil = models.TextField(null=True, blank=True)

# DESPUES
valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
cuatro_por_mil = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
```

### Paso 10.3 — Migracion de datos

Crear una migracion de datos para convertir los valores existentes:

```bash
python manage.py makemigrations recepcionPago --empty -n convert_valor_to_decimal
```

Editar la migracion generada:

```python
from django.db import migrations

def convert_text_to_decimal(apps, schema_editor):
    RecepcionPago = apps.get_model('recepcionPago', 'RecepcionPago')
    for pago in RecepcionPago.objects.all():
        try:
            pago.valor_new = float(str(pago.valor).replace('.', '').replace(',', '.'))
        except (ValueError, TypeError):
            pago.valor_new = 0
        pago.save(update_fields=['valor_new'])

class Migration(migrations.Migration):
    dependencies = [...]
    operations = [
        migrations.RunPython(convert_text_to_decimal),
    ]
```

> **Precaucion:** Requiere una estrategia de migracion cuidadosa. Hacer backup completo de la BD antes. Probar con un subconjunto de datos primero.

### Paso 10.4 — Actualizar serializers y vistas

Despues de la migracion, simplificar las aggregaciones:

```python
# ANTES (con TextField)
RecepcionPago.objects.aggregate(
    total=Sum(Cast(Replace('valor', Value('.'), Value('')), output_field=IntegerField()))
)

# DESPUES (con DecimalField)
RecepcionPago.objects.aggregate(total=Sum('valor'))
```

---

## 11. Optimizar importacion masiva desde Excel

**Archivo:** `cotizador/api/views.py`

**Impacto:** Medio — afecta `create_cotizador_excel` y `create_cotizador_tramites_excel`.

### Paso 11.1 — Pre-cargar datos antes del loop

**Antes (1 query por fila por cada lookup):**
```python
for row in excel_data:
    cliente = Cliente.objects.filter(nombre=row['nombre']).first()      # +1 query
    etiqueta = Etiqueta.objects.filter(nombre=row['etiqueta']).first()  # +1 query
    existente = Cotizador.objects.filter(placa=row['placa']).first()    # +1 query
```

**Despues:**
```python
# Pre-cargar ANTES del loop
clientes_dict = {c.nombre: c for c in Cliente.objects.all()}
etiquetas_dict = {e.nombre: e for e in Etiqueta.objects.all()}
placas_existentes = set(Cotizador.objects.values_list('placa', flat=True))

for row in excel_data:
    cliente = clientes_dict.get(row['nombre'])
    etiqueta = etiquetas_dict.get(row['etiqueta'])
    ya_existe = row['placa'] in placas_existentes
```

### Paso 11.2 — Usar bulk_create para inserciones

```python
nuevos_cotizadores = []
for row in excel_data:
    if not ya_existe:
        nuevos_cotizadores.append(Cotizador(
            placa=row['placa'],
            idCliente=cliente.id,
            # ...
        ))

Cotizador.objects.bulk_create(nuevos_cotizadores, batch_size=500)
```

---

## 12. Usar bulk_create para logs

**Archivos:** `cotizador/api/views.py`, `tramites/api/views.py`

**Impacto:** Bajo-medio — reduce inserts individuales al actualizar registros.

```python
# ANTES — 1 INSERT por campo modificado
logs = []
for field, old_value in old_data.items():
    new_value = new_data.get(field)
    if old_value != new_value:
        LogCotizador.objects.create(  # 1 query por campo
            idCotizador=cotizador.id,
            campo=field,
            valorAnterior=old_value,
            valorNuevo=new_value,
        )

# DESPUES — 1 INSERT para todos los campos
logs = []
for field, old_value in old_data.items():
    new_value = new_data.get(field)
    if old_value != new_value:
        logs.append(LogCotizador(
            idCotizador=cotizador.id,
            campo=field,
            valorAnterior=old_value,
            valorNuevo=new_value,
        ))
if logs:
    LogCotizador.objects.bulk_create(logs)
```

---

## 13. Eliminar print() de produccion

**Impacto:** Bajo — elimina escrituras sincronas bloqueantes bajo Daphne/ASGI.

### Archivos afectados

| Archivo | Lineas aproximadas |
|---|---|
| `cotizador/api/views.py` | 210, 334, 579, 656, 748, 754, 896 |
| `gastosgenerales/api/views.py` | 49, 241 |
| `balancegeneral/api/views.py` | 546, 718, 943-946 |

### Opcion A — Eliminar directamente

Buscar y eliminar todos los `print(...)` de los archivos de vistas.

### Opcion B — Reemplazar por logging

```python
import logging
logger = logging.getLogger(__name__)

# Reemplazar
print(f"Error: {e}")
# por
logger.error(f"Error: {e}")
```

---

## 14. Monitoreo y validacion

### Paso 14.1 — Instalar django-debug-toolbar (solo desarrollo)

```bash
pip install django-debug-toolbar
```

```python
# settings.py (solo si DEBUG=True)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
```

Esto permite ver el numero exacto de queries SQL por request y detectar N+1 restantes.

### Paso 14.2 — Logging de queries lentas en MySQL

```sql
-- En la configuracion de MySQL
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- registrar queries que tarden mas de 1 segundo
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow-query.log';
```

### Paso 14.3 — Medir antes y despues

Antes de aplicar cambios, medir tiempos de respuesta de los endpoints principales:

```bash
# Ejemplo con curl
curl -w "\nTiempo total: %{time_total}s\n" -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/cotizador/
```

Registrar los tiempos y comparar despues de cada grupo de optimizaciones.

---

## Resumen de impacto esperado

| Optimizacion | Queries antes | Queries despues | Mejora |
|---|---|---|---|
| N+1 en cotizador (1000 registros) | ~3,001 | ~4 | 99.8% |
| N+1 en tramites (1000 registros) | ~2,001 | ~3 | 99.8% |
| select_related en vistas con FK | N+1 por vista | 1 | 99%+ |
| balancegeneral (10 tarjetas) | ~130 | ~8 | 93.8% |
| Paginacion (50 por pagina) | N registros completos | 50 registros | Proporcional al tamanio de tabla |
| Connection pooling | 1 conexion/request | Reutilizada | ~5-15ms por request |
| Cache en balancegeneral | Calculo completo | Lectura de cache | ~95%+ en requests cacheados |

---

## Orden recomendado de implementacion

1. **settings.py** — `CONN_MAX_AGE`, paginacion, cache (Secciones 1 y 8)
2. **N+1 en cotizador** — Mayor impacto por ser el endpoint mas usado (Seccion 2)
3. **select_related** en todas las vistas con FK (Seccion 4)
4. **balancegeneral** — Endpoint mas pesado del sistema (Seccion 5)
5. **N+1 en tramites** (Seccion 3)
6. **Indices de BD** (Seccion 6)
7. **prefetch_related en clientes** (Seccion 7)
8. **Importacion Excel** (Seccion 11)
9. **bulk_create para logs** (Seccion 12)
10. **Eliminar print()** (Seccion 13)
11. **IntegerField a ForeignKey** (Seccion 9)
12. **TextField a DecimalField** (Seccion 10)
