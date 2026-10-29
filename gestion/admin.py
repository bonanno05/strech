from django.contrib import admin

from .models import (
    CambioEstado,
    Categoria,
    Cliente,
    DetallePedido,
    Pedido,
    PlantillaMensaje,
    Producto,
    Reparacion,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'whatsapp', 'correo', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'apellido', 'whatsapp', 'correo']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'moneda', 'stock', 'activo']
    list_filter = ['categoria', 'moneda', 'activo']
    search_fields = ['nombre', 'descripcion']


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'fecha', 'estado', 'importe_total', 'moneda']
    list_filter = ['estado', 'moneda']
    readonly_fields = ['fecha']
    inlines = [DetallePedidoInline]


class CambioEstadoInline(admin.TabularInline):
    model = CambioEstado
    extra = 1


@admin.register(Reparacion)
class ReparacionAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_seguimiento',
        'modelo_equipo',
        'cliente',
        'estado_actual',
        'fecha_ingreso',
    ]
    search_fields = ['codigo_seguimiento', 'modelo_equipo']
    readonly_fields = ['fecha_ingreso']
    inlines = [CambioEstadoInline]


@admin.register(PlantillaMensaje)
class PlantillaMensajeAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo']
    list_filter = ['tipo']
    search_fields = ['nombre', 'cuerpo']
