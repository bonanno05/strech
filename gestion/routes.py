from django.urls import path

from . import views

urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('producto/<int:producto_id>/', views.producto_detalle, name='producto_detalle'),

    path('carrito/', views.carrito, name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/quitar/<int:producto_id>/', views.quitar_del_carrito, name='quitar_del_carrito'),
]
