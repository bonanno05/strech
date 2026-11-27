"""Formularios del panel.

Un ModelForm arma los campos solos a partir de un modelo y se encarga de
validar lo que llega del navegador: que el precio sea un numero, que el stock
no sea negativo, que el nombre no supere el largo maximo y que no falte nada
obligatorio. Es lo que en el apartado 4.2 del informe se menciona como
"validacion de formularios incluida" al justificar la eleccion de Django.
"""
from django import forms

from .models import Cliente, Producto, Reparacion


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


class FormularioReparacion(forms.ModelForm):
    """Alta de una reparacion. RF-24.

    El requisito pide poder asociar el equipo a un cliente que ya exista o a
    uno nuevo registrado en la misma operacion. Por eso el formulario tiene
    las dos posibilidades: una lista con los clientes registrados y, debajo,
    los campos para cargar uno nuevo. Hay que usar una sola de las dos.
    """

    cliente_existente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        required=False,
        label='Cliente ya registrado',
        empty_label='— Elegir de la lista —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    nuevo_nombre = forms.CharField(
        required=False, max_length=50, label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    nuevo_apellido = forms.CharField(
        required=False, max_length=50, label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    nuevo_whatsapp = forms.CharField(
        required=False, max_length=20, label='Número de WhatsApp',
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Reparacion
        fields = ['modelo_equipo', 'falla_declarada']
        labels = {
            'modelo_equipo': 'Modelo del equipo',
            'falla_declarada': 'Falla declarada por el cliente',
        }
        help_texts = {
            'falla_declarada': 'Lo que cuenta el cliente, con sus palabras.',
        }
        widgets = {
            'modelo_equipo': forms.TextInput(attrs={'class': 'form-control'}),
            'falla_declarada': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # La lista de clientes se arma cuando se usa el formulario, no cuando
        # se define la clase. Si se armara al definirla, quedaria congelada
        # con los clientes que habia al arrancar el servidor.
        super().__init__(*args, **kwargs)
        self.fields['cliente_existente'].queryset = Cliente.objects.filter(
            activo=True).order_by('apellido', 'nombre')

    def clean(self):
        """Valida que se use una sola de las dos formas de indicar el cliente."""
        datos = super().clean()

        existente = datos.get('cliente_existente')
        whatsapp = datos.get('nuevo_whatsapp', '')
        if whatsapp is None:
            whatsapp = ''
        whatsapp = whatsapp.strip()

        if existente is None and whatsapp == '':
            raise forms.ValidationError(
                'Elegí un cliente de la lista o cargá uno nuevo con su número '
                'de WhatsApp.')

        if existente is not None and whatsapp != '':
            raise forms.ValidationError(
                'Elegí una sola opción: un cliente de la lista o uno nuevo, '
                'no las dos.')

        if whatsapp != '' and Cliente.objects.filter(whatsapp=whatsapp).exists():
            raise forms.ValidationError(
                'Ya hay un cliente registrado con ese número. Elegilo de la lista.')

        datos['nuevo_whatsapp'] = whatsapp
        return datos
