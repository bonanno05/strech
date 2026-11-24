"""Formularios del panel.

Un ModelForm arma los campos solos a partir de un modelo y se encarga de
validar lo que llega del navegador: que el precio sea un numero, que el stock
no sea negativo, que el nombre no supere el largo maximo y que no falte nada
obligatorio. Es lo que en el apartado 4.2 del informe se menciona como
"validacion de formularios incluida" al justificar la eleccion de Django.
"""
from django import forms

from .models import Producto


class FormularioProducto(forms.ModelForm):
    """Alta y edicion de un producto del catalogo. RF-01 y RF-02."""

    class Meta:
        model = Producto

        # Que campos del modelo aparecen en el formulario, y en que orden.
        fields = [
            'nombre',
            'descripcion',
            'categoria',
            'precio',
            'moneda',
            'stock',
            'activo',
        ]

        # Como se llama cada campo en la pantalla.
        labels = {
            'nombre': 'Nombre del producto',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'precio': 'Precio',
            'moneda': 'Moneda del precio',
            'stock': 'Cantidad disponible',
            'activo': 'Publicado en el catálogo',
        }

        # Una aclaracion debajo del campo, para que no haga falta explicarle
        # nada al vendedor (RNF-02).
        help_texts = {
            'moneda': 'El catálogo muestra el precio junto con esta moneda.',
            'stock': 'Cantidad que hay ahora. Baja sola al confirmar una venta.',
            'activo': 'Si lo desmarcás, deja de aparecer en el catálogo público.',
        }

        # Los widgets definen el campo HTML. Se usan para ponerles las clases
        # de Bootstrap, que es lo que les da el aspecto.
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'stock': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
