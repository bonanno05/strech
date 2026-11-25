"""Formularios del panel.

Un ModelForm arma los campos solos a partir de un modelo y se encarga de
validar lo que llega del navegador: que el precio sea un numero, que el stock
no sea negativo, que el nombre no supere el largo maximo y que no falte nada
obligatorio. Es lo que en el apartado 4.2 del informe se menciona como
"validacion de formularios incluida" al justificar la eleccion de Django.
"""
from django import forms

from .models import Cliente, Producto


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


class FormularioCliente(forms.ModelForm):
    """Alta y edicion de un cliente desde el panel. RF-17.

    No incluye la contrasena: eso se maneja aparte, con el restablecimiento
    del RF-23, para que el vendedor nunca tenga que escribir la contrasena
    de otra persona.
    """

    class Meta:
        model = Cliente

        fields = [
            'nombre',
            'apellido',
            'whatsapp',
            'correo',
        ]

        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'whatsapp': 'Número de WhatsApp',
            'correo': 'Correo electrónico',
        }

        help_texts = {
            'whatsapp': 'Es el dato con el que el cliente inicia sesión. No se puede repetir.',
        }

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_whatsapp(self):
        """Valida el numero de WhatsApp.

        El modelo ya lo marca como unico, pero conviene dar un mensaje claro
        en lugar de dejar que falle la base de datos. Y desde el panel el
        numero es obligatorio, aunque el modelo lo admita vacio: vacio solo
        queda cuando se eliminan los datos personales de alguien.
        """
        numero = self.cleaned_data.get('whatsapp', '')

        if numero is None or numero.strip() == '':
            raise forms.ValidationError('Hace falta el número de WhatsApp.')

        numero = numero.strip()

        repetidos = Cliente.objects.filter(whatsapp=numero)
        if self.instance.pk is not None:
            # Si se esta editando, no se cuenta a si mismo como repetido.
            repetidos = repetidos.exclude(pk=self.instance.pk)

        if repetidos.exists():
            raise forms.ValidationError('Ya hay otra cuenta con ese número.')

        return numero
