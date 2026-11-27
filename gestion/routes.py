from django.urls import path

from . import views

urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('producto/<int:producto_id>/', views.producto_detalle, name='producto_detalle'),

    path('seguimiento/', views.seguimiento, name='seguimiento'),

    path('carrito/', views.carrito, name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/quitar/<int:producto_id>/', views.quitar_del_carrito, name='quitar_del_carrito'),

    path('pedido/enviar/', views.enviar_pedido, name='enviar_pedido'),
    path('pedido/<int:pedido_id>/enviado/', views.pedido_enviado, name='pedido_enviado'),

    path('panel/', views.panel_inicio, name='panel_inicio'),
    path('panel/ingresar/', views.panel_ingresar, name='panel_ingresar'),
    path('panel/salir/', views.panel_salir, name='panel_salir'),
    path('panel/reparaciones/', views.panel_reparaciones,
         name='panel_reparaciones'),
    path('panel/reparaciones/nueva/', views.panel_reparacion_nueva,
         name='panel_reparacion_nueva'),
    path('panel/reparaciones/<int:reparacion_id>/',
         views.panel_reparacion_detalle, name='panel_reparacion_detalle'),
    path('panel/reparaciones/<int:reparacion_id>/estado/',
         views.panel_reparacion_estado, name='panel_reparacion_estado'),

    path('panel/clientes/', views.panel_clientes, name='panel_clientes'),
    path('panel/clientes/nuevo/', views.panel_cliente_nuevo,
         name='panel_cliente_nuevo'),
    path('panel/clientes/<int:cliente_id>/', views.panel_cliente_detalle,
         name='panel_cliente_detalle'),
    path('panel/clientes/<int:cliente_id>/editar/', views.panel_cliente_editar,
         name='panel_cliente_editar'),
    path('panel/clientes/<int:cliente_id>/contrasena/',
         views.panel_cliente_contrasena, name='panel_cliente_contrasena'),
    path('panel/clientes/<int:cliente_id>/eliminar-datos/',
         views.panel_cliente_eliminar_datos, name='panel_cliente_eliminar_datos'),

    path('panel/productos/', views.panel_productos, name='panel_productos'),
    path('panel/productos/nuevo/', views.panel_producto_nuevo,
         name='panel_producto_nuevo'),
    path('panel/productos/<int:producto_id>/editar/', views.panel_producto_editar,
         name='panel_producto_editar'),
    path('panel/productos/<int:producto_id>/stock/', views.panel_producto_stock,
         name='panel_producto_stock'),
    path('panel/productos/<int:producto_id>/publicacion/',
         views.panel_producto_publicacion, name='panel_producto_publicacion'),

    path('panel/pedidos/', views.panel_pedidos, name='panel_pedidos'),
    path('panel/pedidos/<int:pedido_id>/', views.panel_pedido_detalle,
         name='panel_pedido_detalle'),
    path('panel/pedidos/<int:pedido_id>/confirmar/', views.panel_confirmar_pedido,
         name='panel_confirmar_pedido'),
    path('panel/pedidos/<int:pedido_id>/descartar/', views.panel_descartar_pedido,
         name='panel_descartar_pedido'),

    path('cuenta/registro/', views.registro, name='registro'),
    path('cuenta/ingresar/', views.ingresar, name='ingresar'),
    path('cuenta/salir/', views.salir, name='salir'),
]
