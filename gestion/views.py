from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404, redirect, render

from .models import Categoria, Cliente, Producto


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
