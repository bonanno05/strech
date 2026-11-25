import secrets
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FormularioCliente, FormularioProducto
from .models import Categoria, Cliente, DetallePedido, Pedido, Producto


# El carrito se guarda en la sesion del navegador, no en la base de datos.
# Recien se convierte en Pedido cuando el cliente lo envia.
# Es un diccionario donde la clave es el id del producto (como texto, porque
# la sesion solo admite texto) y el valor es la cantidad.
CLAVE_CARRITO = 'carrito'

# En la sesion tambien se guarda que cliente inicio sesion. Se guarda solo el
# id: los datos se vuelven a buscar en cada peticion, asi que si la cuenta se
# desactiva deja de funcionar enseguida.
CLAVE_CLIENTE = 'cliente_id'


def cliente_actual(request):
    """Devuelve el Cliente que inicio sesion, o None si no hay nadie."""
    cliente_id = request.session.get(CLAVE_CLIENTE)
    if cliente_id is None:
        return None

    cliente = Cliente.objects.filter(pk=cliente_id, activo=True).first()
    return cliente


def datos_del_cliente(request):
    """Deja el cliente disponible en todas las plantillas, sin pasarlo a mano.

    Se registra en settings.py, dentro de context_processors.
    """
    datos = {
        'cliente': cliente_actual(request),
    }
    return datos


def leer_carrito(request):
    carrito = request.session.get(CLAVE_CARRITO)
    if carrito is None:
        carrito = {}
    return carrito


def guardar_carrito(request, carrito):
    request.session[CLAVE_CARRITO] = carrito
    request.session.modified = True


def moneda_del_carrito(carrito):
    """Devuelve la moneda de los productos que ya estan en el carrito.

    Si el carrito esta vacio devuelve texto vacio.
    """
    for texto_id in carrito:
        producto = Producto.objects.filter(pk=int(texto_id)).first()
        if producto is not None:
            return producto.moneda
    return ''


def armar_resumen(carrito):
    """Convierte el carrito de la sesion en datos listos para mostrar."""
    lineas = []
    total = Decimal('0.00')
    moneda = ''

    for texto_id, cantidad in carrito.items():
        producto = Producto.objects.filter(pk=int(texto_id), activo=True).first()
        if producto is None:
            continue

        subtotal = producto.precio * cantidad
        total = total + subtotal
        moneda = producto.moneda

        linea = {
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal,
        }
        lineas.append(linea)

    resumen = {
        'lineas': lineas,
        'total': total,
        'moneda': moneda,
    }
    return resumen


def catalogo(request):
    # Solo se muestran los productos activos. Los dados de baja siguen en la
    # base de datos porque figuran en pedidos ya concretados.
    productos = Producto.objects.filter(activo=True)

    # select_related trae la categoria de cada producto en la misma consulta.
    # Sin esto, la plantilla haria una consulta extra por cada producto al
    # mostrar el nombre de su categoria.
    productos = productos.select_related('categoria')

    # El filtro de categoria llega en la direccion y siempre es texto.
    # Se convierte a numero para poder compararlo despues en la plantilla.
    categoria_activa = 0
    texto_categoria = request.GET.get('categoria', '')
    if texto_categoria.isdigit():
        categoria_activa = int(texto_categoria)
        productos = productos.filter(categoria_id=categoria_activa)

    busqueda = request.GET.get('q', '')
    busqueda = busqueda.strip()
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    productos = productos.order_by('nombre')
    categorias = Categoria.objects.order_by('nombre')

    datos = {
        'productos': productos,
        'categorias': categorias,
        'categoria_activa': categoria_activa,
        'busqueda': busqueda,
    }
    return render(request, 'catalogo.html', datos)


def producto_detalle(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)

    datos = {
        'producto': producto,
    }
    return render(request, 'producto_detalle.html', datos)


def carrito(request):
    carrito_guardado = leer_carrito(request)
    resumen = armar_resumen(carrito_guardado)

    datos = {
        'lineas': resumen['lineas'],
        'total': resumen['total'],
        'moneda': resumen['moneda'],
    }
    return render(request, 'carrito.html', datos)


def agregar_al_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('producto_detalle', producto_id=producto_id)

    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    carrito_guardado = leer_carrito(request)

    # Un pedido admite una sola moneda, porque el sistema no convierte divisas.
    moneda_actual = moneda_del_carrito(carrito_guardado)
    if moneda_actual != '' and moneda_actual != producto.moneda:
        messages.error(
            request,
            'El carrito ya tiene productos en ' + moneda_actual + '. '
            'Para pedir productos en ' + producto.moneda + ' hay que hacer otro pedido.'
        )
        return redirect('producto_detalle', producto_id=producto.id)

    cantidad_pedida = 1
    texto_cantidad = request.POST.get('cantidad', '1')
    if texto_cantidad.isdigit():
        cantidad_pedida = int(texto_cantidad)

    if cantidad_pedida < 1:
        cantidad_pedida = 1

    clave = str(producto.id)
    cantidad_actual = carrito_guardado.get(clave, 0)
    cantidad_nueva = cantidad_actual + cantidad_pedida

    if cantidad_nueva > producto.stock:
        messages.error(
            request,
            'No hay stock suficiente. Quedan ' + str(producto.stock) + ' unidades.'
        )
        return redirect('producto_detalle', producto_id=producto.id)

    carrito_guardado[clave] = cantidad_nueva
    guardar_carrito(request, carrito_guardado)

    messages.success(request, producto.nombre + ' se agregó al carrito.')
    return redirect('carrito')


def actualizar_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('carrito')

    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    carrito_guardado = leer_carrito(request)

    cantidad_nueva = 0
    texto_cantidad = request.POST.get('cantidad', '0')
    if texto_cantidad.isdigit():
        cantidad_nueva = int(texto_cantidad)

    clave = str(producto.id)

    if cantidad_nueva < 1:
        carrito_guardado.pop(clave, None)
        guardar_carrito(request, carrito_guardado)
        messages.success(request, producto.nombre + ' se quitó del carrito.')
        return redirect('carrito')

    if cantidad_nueva > producto.stock:
        messages.error(
            request,
            'No hay stock suficiente. Quedan ' + str(producto.stock) + ' unidades.'
        )
        return redirect('carrito')

    carrito_guardado[clave] = cantidad_nueva
    guardar_carrito(request, carrito_guardado)

    messages.success(request, 'Se actualizó la cantidad.')
    return redirect('carrito')


def quitar_del_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('carrito')

    carrito_guardado = leer_carrito(request)
    clave = str(producto_id)
    carrito_guardado.pop(clave, None)
    guardar_carrito(request, carrito_guardado)

    messages.success(request, 'Se quitó el producto del carrito.')
    return redirect('carrito')


def registro(request):
    if cliente_actual(request) is not None:
        return redirect('catalogo')

    if request.method != 'POST':
        return render(request, 'cuenta/registro.html', {})

    nombre = request.POST.get('nombre', '').strip()
    apellido = request.POST.get('apellido', '').strip()
    whatsapp = request.POST.get('whatsapp', '').strip()
    correo = request.POST.get('correo', '').strip()
    contrasena = request.POST.get('contrasena', '')
    repetir_contrasena = request.POST.get('repetir_contrasena', '')

    errores = []

    if nombre == '':
        errores.append('Falta el nombre.')

    if apellido == '':
        errores.append('Falta el apellido.')

    if whatsapp == '':
        errores.append('Falta el número de WhatsApp.')
    else:
        ya_existe = Cliente.objects.filter(whatsapp=whatsapp).exists()
        if ya_existe:
            errores.append('Ya hay una cuenta registrada con ese número.')

    if correo == '':
        errores.append('Falta el correo electrónico.')

    if len(contrasena) < 8:
        errores.append('La contraseña necesita al menos 8 caracteres.')

    if contrasena != repetir_contrasena:
        errores.append('Las dos contraseñas no coinciden.')

    if errores:
        # Se devuelven los valores escritos para no obligar a cargarlos de nuevo.
        # La contrasena no se devuelve nunca.
        datos = {
            'errores': errores,
            'nombre': nombre,
            'apellido': apellido,
            'whatsapp': whatsapp,
            'correo': correo,
        }
        return render(request, 'cuenta/registro.html', datos)

    cliente = Cliente()
    cliente.nombre = nombre
    cliente.apellido = apellido
    cliente.whatsapp = whatsapp
    cliente.correo = correo
    # make_password convierte la contrasena en un hash. Lo que se guarda no
    # permite recuperar la contrasena original (RNF-13).
    cliente.contrasena = make_password(contrasena)
    cliente.save()

    request.session[CLAVE_CLIENTE] = cliente.id

    messages.success(request, 'Tu cuenta quedó creada.')
    return redirect('catalogo')


def ingresar(request):
    if cliente_actual(request) is not None:
        return redirect('catalogo')

    if request.method != 'POST':
        return render(request, 'cuenta/ingresar.html', {})

    whatsapp = request.POST.get('whatsapp', '').strip()
    contrasena = request.POST.get('contrasena', '')

    cliente = Cliente.objects.filter(whatsapp=whatsapp, activo=True).first()

    # Se responde lo mismo si el numero no existe, si la cuenta no tiene
    # contrasena o si la contrasena esta mal. Asi nadie puede averiguar que
    # numeros tienen cuenta probando de a uno.
    contrasena_correcta = False
    if cliente is not None and cliente.contrasena:
        contrasena_correcta = check_password(contrasena, cliente.contrasena)

    if not contrasena_correcta:
        datos = {
            'error': 'El número o la contraseña no son correctos.',
            'whatsapp': whatsapp,
        }
        return render(request, 'cuenta/ingresar.html', datos)

    # Al iniciar sesion se renueva el identificador de sesion, para que un
    # identificador capturado antes no sirva despues. El contenido se conserva,
    # asi que el carrito armado sin cuenta no se pierde.
    request.session.cycle_key()
    request.session[CLAVE_CLIENTE] = cliente.id

    messages.success(request, 'Hola de nuevo, ' + cliente.nombre + '.')
    return redirect('catalogo')


def salir(request):
    if request.method != 'POST':
        return redirect('catalogo')

    request.session.pop(CLAVE_CLIENTE, None)
    messages.success(request, 'Cerraste la sesión.')
    return redirect('catalogo')


def enviar_pedido(request):
    """Convierte el carrito de la sesion en un Pedido con sus detalles.

    Es el momento en que el carrito deja de ser un borrador guardado en el
    navegador y pasa a ser un registro de la base de datos.
    """
    # Enviar un pedido cambia datos, asi que solo se acepta por POST.
    # Si alguien entra escribiendo la direccion, se lo manda al carrito.
    if request.method != 'POST':
        return redirect('carrito')

    # RF-10: hace falta haber iniciado sesion. El carrito no se pierde,
    # porque vive en la sesion y sigue estando despues de ingresar.
    cliente = cliente_actual(request)
    if cliente is None:
        messages.info(request, 'Ingresá a tu cuenta para enviar el pedido.')
        return redirect('ingresar')

    carrito = leer_carrito(request)
    if len(carrito) == 0:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('carrito')

    # Se revisa todo otra vez contra la base de datos. El carrito vive en el
    # navegador y pudo quedar viejo: un producto pudo agotarse o darse de baja
    # mientras el cliente lo tenia cargado.
    lineas = []
    errores = []
    total = Decimal('0.00')
    moneda = ''

    for texto_id, cantidad in carrito.items():
        producto = Producto.objects.filter(pk=int(texto_id), activo=True).first()

        if producto is None:
            errores.append('Un producto de tu carrito ya no está publicado.')
            continue

        if cantidad > producto.stock:
            aviso = 'No hay stock suficiente de %s. Quedan %d.' % (
                producto.nombre,
                producto.stock,
            )
            errores.append(aviso)
            continue

        if moneda == '':
            moneda = producto.moneda

        total = total + (producto.precio * cantidad)

        linea = {
            'producto': producto,
            'cantidad': cantidad,
        }
        lineas.append(linea)

    if len(errores) > 0:
        for error in errores:
            messages.error(request, error)
        return redirect('carrito')

    # Desde aca empieza lo que tiene que pasar entero o no pasar.
    # Si algo falla adentro del bloque, la base deshace todo lo anterior y no
    # queda ningun pedido a medias.
    with transaction.atomic():
        pedido = Pedido.objects.create(
            cliente=cliente,
            moneda=moneda,
            importe_total=total,
        )

        for linea in lineas:
            producto = linea['producto']
            # El nombre y el precio se copian, no se referencian: la linea
            # tiene que conservar las condiciones del momento de la venta,
            # aunque despues el producto cambie de nombre o de precio.
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                nombre_producto=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=linea['cantidad'],
            )

    # El pedido ya quedo guardado, asi que el carrito deja de hacer falta.
    # RF-12: nace pendiente y el stock NO se toca. Se descuenta recien cuando
    # el vendedor confirma la venta, que es el RF-14.
    guardar_carrito(request, {})

    return redirect('pedido_enviado', pedido_id=pedido.id)


def pedido_enviado(request, pedido_id):
    """Muestra el pedido que se acaba de enviar."""
    cliente = cliente_actual(request)
    if cliente is None:
        return redirect('ingresar')

    # Se filtra tambien por cliente. Asi, cambiando el numero de la direccion,
    # nadie puede ver el pedido de otra persona.
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=cliente)
    detalles = pedido.detalles.all()

    contexto = {
        'pedido': pedido,
        'detalles': detalles,
    }
    return render(request, 'pedido_enviado.html', contexto)


# ---------------------------------------------------------------------------
# PANEL DEL VENDEDOR
#
# El vendedor no es una entidad del modelo de datos: usa el sistema de usuarios
# que ya trae Django, la tabla auth_user. Por eso el ingreso de aca no se
# parece al del cliente: no leemos la contrasena a mano, se la pasamos a
# Django, que ademas maneja la sesion y el cifrado.
#
# Son dos sesiones independientes y pueden convivir en el mismo navegador: una
# persona puede estar como cliente y como vendedor al mismo tiempo.
# ---------------------------------------------------------------------------


def panel_ingresar(request):
    """Ingreso del vendedor al panel de gestion."""
    # Si ya ingreso, no tiene sentido mostrarle el formulario otra vez.
    if request.user.is_authenticated:
        return redirect('panel_inicio')

    errores = []
    usuario_escrito = ''

    if request.method == 'POST':
        usuario_escrito = request.POST.get('usuario', '').strip()
        contrasena = request.POST.get('contrasena', '')

        # authenticate devuelve el usuario si los datos son correctos, o None.
        # Compara la contrasena contra la version cifrada, igual que hacemos
        # con el cliente, pero sin que tengamos que escribirlo nosotros.
        usuario = authenticate(request, username=usuario_escrito, password=contrasena)

        if usuario is None:
            # Se responde lo mismo exista o no el usuario, para no confirmarle
            # a nadie que cierto nombre de usuario es valido.
            errores.append('El usuario o la contraseña no son correctos.')
        elif not usuario.is_staff:
            errores.append('Esa cuenta no tiene acceso al panel.')
        else:
            # login() guarda en la sesion que este usuario ingreso.
            login(request, usuario)
            return redirect('panel_inicio')

    contexto = {
        'errores': errores,
        'usuario_escrito': usuario_escrito,
    }
    return render(request, 'panel/ingresar.html', contexto)


def panel_salir(request):
    """Cierra la sesion del vendedor, sin tocar la del cliente."""
    if request.method != 'POST':
        return redirect('panel_inicio')

    # logout() de Django borra la sesion ENTERA, y el carrito del cliente vive
    # en esa misma sesion. Se lo guarda aparte y se lo repone despues, asi
    # cerrar el panel no le vacia el carrito a quien este comprando en la
    # misma computadora.
    carrito_guardado = request.session.get(CLAVE_CARRITO)
    cliente_guardado = request.session.get(CLAVE_CLIENTE)

    logout(request)

    if carrito_guardado is not None:
        request.session[CLAVE_CARRITO] = carrito_guardado
    if cliente_guardado is not None:
        request.session[CLAVE_CLIENTE] = cliente_guardado

    return redirect('panel_ingresar')


@login_required
def panel_inicio(request):
    """Pantalla principal del panel, con el estado general del negocio."""
    # count() cuenta en la base de datos y devuelve un numero. No trae los
    # registros, asi que no importa cuantos haya: la consulta pesa lo mismo.
    pedidos_pendientes = Pedido.objects.filter(
        estado=Pedido.Estado.PENDIENTE).count()
    pedidos_confirmados = Pedido.objects.filter(
        estado=Pedido.Estado.CONFIRMADO).count()
    productos_publicados = Producto.objects.filter(activo=True).count()
    productos_agotados = Producto.objects.filter(activo=True, stock=0).count()
    clientes_registrados = Cliente.objects.filter(activo=True).count()

    # Los ultimos pedidos pendientes, para poder atenderlos sin ir a buscarlos.
    #
    # select_related('cliente') trae el cliente en la MISMA consulta. Sin eso,
    # Django haria una consulta extra por cada pedido al mostrar el nombre del
    # cliente en la plantilla: con 5 pedidos serian 6 consultas en vez de 1.
    # Con 100 pedidos serian 101. Eso es lo que pide el RNF-04.
    ultimos_pendientes = Pedido.objects.filter(
        estado=Pedido.Estado.PENDIENTE
    ).select_related('cliente')[:5]

    contexto = {
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_confirmados': pedidos_confirmados,
        'productos_publicados': productos_publicados,
        'productos_agotados': productos_agotados,
        'clientes_registrados': clientes_registrados,
        'ultimos_pendientes': ultimos_pendientes,
    }
    return render(request, 'panel/inicio.html', contexto)


@login_required
def panel_pedidos(request):
    """Lista los pedidos, con un filtro por estado. RF-15."""
    # El filtro llega por la direccion, por ejemplo /panel/pedidos/?estado=pendiente
    estado_pedido = request.GET.get('estado', 'pendiente')

    # Solo se aceptan estados que existan. Si llega cualquier otra cosa se
    # muestra todo, en lugar de romper o de filtrar por un valor inventado.
    estados_validos = []
    for valor, etiqueta in Pedido.Estado.choices:
        estados_validos.append(valor)

    # select_related trae el cliente en la misma consulta, para no hacer una
    # consulta por cada fila al mostrar su nombre (RNF-04).
    pedidos = Pedido.objects.select_related('cliente')

    if estado_pedido in estados_validos:
        pedidos = pedidos.filter(estado=estado_pedido)
    else:
        estado_pedido = 'todos'

    # Los numeros de cada solapa. Son cuentas en la base, no traen registros.
    conteos = {
        'pendiente': Pedido.objects.filter(
            estado=Pedido.Estado.PENDIENTE).count(),
        'confirmado': Pedido.objects.filter(
            estado=Pedido.Estado.CONFIRMADO).count(),
        'descartado': Pedido.objects.filter(
            estado=Pedido.Estado.DESCARTADO).count(),
        'anulado': Pedido.objects.filter(
            estado=Pedido.Estado.ANULADO).count(),
        'todos': Pedido.objects.count(),
    }

    contexto = {
        'pedidos': pedidos,
        'estado_pedido': estado_pedido,
        'conteos': conteos,
    }
    return render(request, 'panel/pedidos.html', contexto)


@login_required
def panel_pedido_detalle(request, pedido_id):
    """Muestra un pedido con sus lineas y las acciones disponibles."""
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente'), pk=pedido_id)

    # Se trae tambien el producto de cada linea, porque se muestra el stock
    # que hay ahora al lado de la cantidad pedida.
    detalles = pedido.detalles.select_related('producto').all()

    # Para avisarle al vendedor, antes de que confirme, si algo no alcanza.
    hay_faltantes = False
    for detalle in detalles:
        if detalle.cantidad > detalle.producto.stock:
            hay_faltantes = True

    contexto = {
        'pedido': pedido,
        'detalles': detalles,
        'hay_faltantes': hay_faltantes,
    }
    return render(request, 'panel/pedido_detalle.html', contexto)


@login_required
def panel_confirmar_pedido(request, pedido_id):
    """Confirma un pedido como venta y descuenta el stock. RF-13 y RF-14.

    Es la operacion mas delicada del sistema. Dos cosas tienen que pasar
    juntas o no pasar: descontar el stock de cada producto y marcar el pedido
    como confirmado. Y ademas hay que impedir que dos confirmaciones
    simultaneas del mismo producto lean el mismo stock y lo descuenten dos
    veces. Eso es el RNF-11 completo.
    """
    if request.method != 'POST':
        return redirect('panel_pedido_detalle', pedido_id=pedido_id)

    faltantes = []
    confirmado = False
    ya_resuelto = False

    with transaction.atomic():
        # select_for_update() bloquea la fila en la base de datos hasta que
        # termine la transaccion. Si otra confirmacion del mismo pedido llega
        # al mismo tiempo, se queda esperando aca en vez de avanzar en
        # paralelo.
        pedido = Pedido.objects.select_for_update().filter(pk=pedido_id).first()

        if pedido is None:
            raise Http404('No encontramos ese pedido.')

        if pedido.estado != Pedido.Estado.PENDIENTE:
            # Alguien lo resolvio mientras tanto, o se apreto el boton dos
            # veces. No se vuelve a descontar stock.
            ya_resuelto = True
        else:
            detalles = list(pedido.detalles.select_related('producto'))

            # Se bloquean tambien las filas de los productos. El orden por
            # clave primaria es a proposito: si dos confirmaciones bloquearan
            # los mismos productos en distinto orden podrian quedar trabadas
            # una esperando a la otra.
            identificadores = []
            for detalle in detalles:
                identificadores.append(detalle.producto_id)

            productos_bloqueados = Producto.objects.select_for_update().filter(
                pk__in=identificadores).order_by('pk')

            producto_por_id = {}
            for producto in productos_bloqueados:
                producto_por_id[producto.id] = producto

            # Primero se revisa que alcance para TODAS las lineas. Recien
            # despues se descuenta: asi no queda un pedido con la mitad del
            # stock descontado.
            for detalle in detalles:
                producto = producto_por_id[detalle.producto_id]
                if detalle.cantidad > producto.stock:
                    aviso = 'No alcanza el stock de %s: se piden %d y quedan %d.' % (
                        producto.nombre,
                        detalle.cantidad,
                        producto.stock,
                    )
                    faltantes.append(aviso)

            if len(faltantes) == 0:
                for detalle in detalles:
                    producto = producto_por_id[detalle.producto_id]
                    producto.stock = producto.stock - detalle.cantidad
                    producto.save()

                pedido.estado = Pedido.Estado.CONFIRMADO
                pedido.save()
                confirmado = True

    if ya_resuelto:
        messages.error(request, 'Ese pedido ya no estaba pendiente.')
    elif confirmado:
        messages.success(
            request, 'Pedido %d confirmado. El stock quedó descontado.' % pedido_id)
    else:
        for aviso in faltantes:
            messages.error(request, aviso)

    return redirect('panel_pedidos')


@login_required
def panel_descartar_pedido(request, pedido_id):
    """Descarta un pedido. RF-13.

    No toca el stock, porque al enviarse el pedido nunca se descontó.
    """
    if request.method != 'POST':
        return redirect('panel_pedido_detalle', pedido_id=pedido_id)

    ya_resuelto = False

    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().filter(pk=pedido_id).first()

        if pedido is None:
            raise Http404('No encontramos ese pedido.')

        if pedido.estado != Pedido.Estado.PENDIENTE:
            ya_resuelto = True
        else:
            pedido.estado = Pedido.Estado.DESCARTADO
            pedido.save()

    if ya_resuelto:
        messages.error(request, 'Ese pedido ya no estaba pendiente.')
    else:
        messages.success(request, 'Pedido %d descartado.' % pedido_id)

    return redirect('panel_pedidos')


@login_required
def panel_productos(request):
    """Lista los productos con busqueda y filtros. RF-05 y RF-07."""
    texto_buscado = request.GET.get('buscar', '').strip()
    categoria_elegida = request.GET.get('categoria', '')
    situacion = request.GET.get('situacion', 'publicados')

    # select_related trae la categoria en la misma consulta, para no hacer
    # una consulta por fila al mostrar su nombre (RNF-04).
    productos = Producto.objects.select_related('categoria')

    if texto_buscado != '':
        # icontains busca el texto adentro del nombre, sin distinguir
        # mayusculas de minusculas.
        productos = productos.filter(nombre__icontains=texto_buscado)

    if categoria_elegida.isdigit():
        productos = productos.filter(categoria_id=int(categoria_elegida))

    if situacion == 'publicados':
        productos = productos.filter(activo=True)
    elif situacion == 'agotados':
        productos = productos.filter(activo=True, stock=0)
    elif situacion == 'de_baja':
        productos = productos.filter(activo=False)

    productos = productos.order_by('categoria__nombre', 'nombre')

    conteos = {
        'publicados': Producto.objects.filter(activo=True).count(),
        'agotados': Producto.objects.filter(activo=True, stock=0).count(),
        'de_baja': Producto.objects.filter(activo=False).count(),
        'todos': Producto.objects.count(),
    }

    contexto = {
        'productos': productos,
        'categorias': Categoria.objects.all().order_by('nombre'),
        'texto_buscado': texto_buscado,
        'categoria_elegida': categoria_elegida,
        'situacion': situacion,
        'conteos': conteos,
    }
    return render(request, 'panel/productos.html', contexto)


@login_required
def panel_producto_nuevo(request):
    """Alta de un producto. RF-01."""
    if request.method == 'POST':
        # Al formulario se le pasan los datos que llegaron del navegador.
        formulario = FormularioProducto(request.POST)

        # is_valid() corre todas las validaciones del modelo. Si algo falla,
        # el formulario se vuelve a mostrar con los errores y con lo que el
        # vendedor ya habia escrito.
        if formulario.is_valid():
            producto = formulario.save()
            messages.success(request, 'Se agregó %s al catálogo.' % producto.nombre)
            return redirect('panel_productos')
    else:
        # Sin datos: el formulario aparece vacio.
        formulario = FormularioProducto()

    contexto = {
        'formulario': formulario,
        'es_nuevo': True,
    }
    return render(request, 'panel/producto_formulario.html', contexto)


@login_required
def panel_producto_editar(request, producto_id):
    """Modificacion de un producto. RF-02."""
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        # instance le dice al formulario que esta editando este producto,
        # no creando uno nuevo.
        formulario = FormularioProducto(request.POST, instance=producto)

        if formulario.is_valid():
            formulario.save()
            messages.success(request, 'Se guardaron los cambios de %s.' % producto.nombre)
            return redirect('panel_productos')
    else:
        formulario = FormularioProducto(instance=producto)

    contexto = {
        'formulario': formulario,
        'producto': producto,
        'es_nuevo': False,
    }
    return render(request, 'panel/producto_formulario.html', contexto)


@login_required
def panel_producto_stock(request, producto_id):
    """Cambia solamente la cantidad disponible, desde el listado. RF-04.

    Es la operacion mas frecuente del vendedor, asi que tiene su propio
    formulario en cada fila y no obliga a abrir la pantalla de edicion.
    """
    if request.method != 'POST':
        return redirect('panel_productos')

    producto = get_object_or_404(Producto, pk=producto_id)
    texto_stock = request.POST.get('stock', '').strip()

    if not texto_stock.isdigit():
        messages.error(request, 'La cantidad tiene que ser un número entero y no negativa.')
        return redirect('panel_productos')

    producto.stock = int(texto_stock)
    producto.save()
    messages.success(
        request, 'El stock de %s quedó en %d.' % (producto.nombre, producto.stock))
    return redirect('panel_productos')


@login_required
def panel_producto_publicacion(request, producto_id):
    """Publica o da de baja un producto. RF-02.

    El producto NO se borra nunca. Darlo de baja lo saca del catalogo publico
    pero lo conserva, porque puede estar referenciado en pedidos anteriores y
    porque el historial tiene que seguir siendo consultable.
    """
    if request.method != 'POST':
        return redirect('panel_productos')

    producto = get_object_or_404(Producto, pk=producto_id)

    if producto.activo:
        producto.activo = False
        aviso = 'Se dio de baja %s. Ya no aparece en el catálogo.' % producto.nombre
    else:
        producto.activo = True
        aviso = 'Se publicó %s de nuevo en el catálogo.' % producto.nombre

    producto.save()
    messages.success(request, aviso)
    return redirect('panel_productos')


@login_required
def panel_clientes(request):
    """Lista los clientes con busqueda. RF-17."""
    texto_buscado = request.GET.get('buscar', '').strip()
    situacion = request.GET.get('situacion', 'activos')

    clientes = Cliente.objects.all()

    if texto_buscado != '':
        # Q permite combinar condiciones con "o". Se busca el texto en el
        # nombre, en el apellido o en el numero de WhatsApp.
        clientes = clientes.filter(
            Q(nombre__icontains=texto_buscado)
            | Q(apellido__icontains=texto_buscado)
            | Q(whatsapp__icontains=texto_buscado)
        )

    if situacion == 'activos':
        clientes = clientes.filter(activo=True)
    elif situacion == 'inactivos':
        clientes = clientes.filter(activo=False)

    clientes = clientes.order_by('apellido', 'nombre', 'id')

    conteos = {
        'activos': Cliente.objects.filter(activo=True).count(),
        'inactivos': Cliente.objects.filter(activo=False).count(),
        'todos': Cliente.objects.count(),
    }

    contexto = {
        'clientes': clientes,
        'texto_buscado': texto_buscado,
        'situacion': situacion,
        'conteos': conteos,
    }
    return render(request, 'panel/clientes.html', contexto)


@login_required
def panel_cliente_detalle(request, cliente_id):
    """Ficha del cliente con su historial. RF-18."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    # prefetch_related trae todos los detalles de todos los pedidos en una
    # sola consulta extra, en lugar de una por pedido (RNF-04).
    pedidos = cliente.pedidos.prefetch_related('detalles').order_by('-fecha')
    reparaciones = cliente.reparaciones.all().order_by('-fecha_ingreso')

    contexto = {
        'cliente': cliente,
        'pedidos': pedidos,
        'reparaciones': reparaciones,
    }
    return render(request, 'panel/cliente_detalle.html', contexto)


@login_required
def panel_cliente_nuevo(request):
    """Alta de un cliente desde el panel. RF-17.

    Queda sin contrasena, asi que todavia no puede iniciar sesion. El
    vendedor le genera una con el restablecimiento del RF-23.
    """
    if request.method == 'POST':
        formulario = FormularioCliente(request.POST)
        if formulario.is_valid():
            cliente = formulario.save()
            messages.success(request, 'Se registró a %s.' % cliente)
            return redirect('panel_cliente_detalle', cliente_id=cliente.id)
    else:
        formulario = FormularioCliente()

    contexto = {
        'formulario': formulario,
        'es_nuevo': True,
    }
    return render(request, 'panel/cliente_formulario.html', contexto)


@login_required
def panel_cliente_editar(request, cliente_id):
    """Modificacion de los datos de un cliente. RF-17."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    if request.method == 'POST':
        formulario = FormularioCliente(request.POST, instance=cliente)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, 'Se guardaron los cambios.')
            return redirect('panel_cliente_detalle', cliente_id=cliente.id)
    else:
        formulario = FormularioCliente(instance=cliente)

    contexto = {
        'formulario': formulario,
        'cliente': cliente,
        'es_nuevo': False,
    }
    return render(request, 'panel/cliente_formulario.html', contexto)


@login_required
def panel_cliente_contrasena(request, cliente_id):
    """Restablece la contrasena de un cliente. RF-23.

    El vendedor no elige la contrasena: el sistema genera una al azar y se la
    muestra una sola vez, para que se la pase al cliente. Asi el vendedor no
    tiene que inventar ni escribir la contrasena de otra persona, y lo que
    queda guardado es el cifrado, no el texto.
    """
    if request.method != 'POST':
        return redirect('panel_cliente_detalle', cliente_id=cliente_id)

    cliente = get_object_or_404(Cliente, pk=cliente_id)

    if not cliente.activo:
        messages.error(request, 'Esa cuenta está dada de baja.')
        return redirect('panel_cliente_detalle', cliente_id=cliente.id)

    # token_urlsafe genera texto al azar con una fuente criptografica, no con
    # el generador comun. Es el mismo criterio del RNF-10 para los codigos de
    # seguimiento: que no se pueda adivinar.
    nueva = secrets.token_urlsafe(8)

    cliente.contrasena = make_password(nueva)
    cliente.save()

    messages.success(
        request,
        'Contraseña nueva de %s: %s  —  anotala y pasásela, no se vuelve a mostrar.'
        % (cliente, nueva))
    return redirect('panel_cliente_detalle', cliente_id=cliente.id)


@login_required
def panel_cliente_eliminar_datos(request, cliente_id):
    """Elimina los datos personales de un cliente. RNF-13.

    No borra el registro. Vacia los campos personales y marca la cuenta como
    inactiva, en una sola operacion. El registro se conserva porque los
    pedidos lo referencian: si se borrara, quedarian ventas sin cliente y se
    perderia el historial del negocio.

    Es irreversible: los datos vaciados no se pueden recuperar.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    if request.method != 'POST':
        return redirect('panel_cliente_detalle', cliente_id=cliente.id)

    # Se pide escribir una palabra exacta. Es una operacion que no tiene
    # vuelta atras, asi que no alcanza con un solo clic.
    confirmacion = request.POST.get('confirmacion', '').strip()
    if confirmacion != 'ELIMINAR':
        messages.error(
            request,
            'Para eliminar los datos hay que escribir ELIMINAR en el cuadro.')
        return redirect('panel_cliente_detalle', cliente_id=cliente.id)

    nombre_anterior = str(cliente)

    # Los cinco campos y la bandera tienen que cambiar juntos. Si quedara a
    # medias, el cliente podria terminar sin nombre pero con la cuenta
    # habilitada, o al reves.
    with transaction.atomic():
        cliente.nombre = None
        cliente.apellido = None
        cliente.whatsapp = None
        cliente.correo = None
        cliente.contrasena = None
        cliente.activo = False
        cliente.save()

    messages.success(
        request,
        'Se eliminaron los datos personales de %s. Sus pedidos se conservan '
        'sin referencia a la persona.' % nombre_anterior)
    return redirect('panel_clientes')
