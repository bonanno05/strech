from django.shortcuts import get_object_or_404, render

from .models import Categoria, Producto


def catalogo(request):
    productos = Producto.objects.filter(activo=True).select_related('categoria')

    categoria = request.GET.get('categoria', '')
    if categoria:
        productos = productos.filter(categoria_id=categoria)

    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    return render(request, 'catalogo.html', {
        'productos': productos.order_by('nombre'),
        'categorias': Categoria.objects.order_by('nombre'),
        'categoria_activa': categoria,
        'busqueda': busqueda,
    })


def producto_detalle(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    return render(request, 'producto_detalle.html', {'producto': producto})
