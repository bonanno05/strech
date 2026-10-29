from django.db import models


MONEDAS = [
    ('ARS', 'Pesos argentinos'),
    ('USD', 'Dólares'),
]


class Cliente(models.Model):
    nombre = models.CharField(max_length=50, null=True, blank=True)
    apellido = models.CharField(max_length=50, null=True, blank=True)
    whatsapp = models.CharField(max_length=20, unique=True, null=True, blank=True)
    correo = models.EmailField(max_length=100, null=True, blank=True)
    contrasena = models.CharField(max_length=128, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'

    def __str__(self):
        nombre_completo = f'{self.nombre or ""} {self.apellido or ""}'.strip()
        return nombre_completo or f'Cliente {self.id} (datos eliminados)'


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
    )
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, choices=MONEDAS, default='ARS')
    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        CONFIRMADO = 'confirmado', 'Confirmado'
        DESCARTADO = 'descartado', 'Descartado'
        ANULADO = 'anulado', 'Anulado'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos',
    )
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    moneda = models.CharField(max_length=3, choices=MONEDAS, default='ARS')
    importe_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'
        ordering = ['-fecha']

    def __str__(self):
        return f'Pedido {self.id} - {self.cliente}'


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles',
    )
    nombre_producto = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'detalle de pedido'
        verbose_name_plural = 'detalles de pedido'
        constraints = [
            models.UniqueConstraint(
                fields=['pedido', 'producto'],
                name='uq_detalle_pedido_producto',
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='ck_detalle_cantidad_positiva',
            ),
        ]

    def __str__(self):
        return f'{self.cantidad} x {self.nombre_producto}'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class Reparacion(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='reparaciones',
    )
    codigo_seguimiento = models.CharField(max_length=12, unique=True)
    modelo_equipo = models.CharField(max_length=100)
    falla_declarada = models.TextField()
    fecha_ingreso = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'reparación'
        verbose_name_plural = 'reparaciones'
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return f'{self.codigo_seguimiento} - {self.modelo_equipo}'

    @property
    def ultimo_cambio(self):
        return self.cambios.order_by('-fecha', '-id').first()

    @property
    def estado_actual(self):
        ultimo = self.ultimo_cambio
        return ultimo.get_estado_display() if ultimo else 'Sin registrar'


class CambioEstado(models.Model):
    class Estado(models.TextChoices):
        RECIBIDO = 'recibido', 'Recibido'
        EN_REPARACION = 'en_reparacion', 'En reparación'
        REPARADO = 'reparado', 'Reparado'
        ENTREGADO = 'entregado', 'Entregado'

    reparacion = models.ForeignKey(
        Reparacion,
        on_delete=models.CASCADE,
        related_name='cambios',
    )
    estado = models.CharField(max_length=20, choices=Estado.choices)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'cambio de estado'
        verbose_name_plural = 'cambios de estado'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.reparacion.codigo_seguimiento}: {self.get_estado_display()}'


class PlantillaMensaje(models.Model):
    class Tipo(models.TextChoices):
        CLIENTE = 'cliente', 'Cliente'
        PRODUCTO = 'producto', 'Producto'
        PEDIDO = 'pedido', 'Pedido'
        REPARACION = 'reparacion', 'Reparación'

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    cuerpo = models.TextField()

    class Meta:
        verbose_name = 'plantilla de mensaje'
        verbose_name_plural = 'plantillas de mensaje'

    def __str__(self):
        return self.nombre