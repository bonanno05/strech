"""Direcciones del proyecto.

Este archivo solo reparte: cada prefijo se delega a la aplicacion que lo atiende.
Las direcciones propias del sistema viven en gestion/routes.py.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestion.routes')),
]
