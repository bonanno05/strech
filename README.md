# Strech

Sistema de gestión para micronegocios dedicados a la importación y venta de
productos tecnológicos.

Proyecto final de la Tecnicatura Superior en Informática Aplicada — INSPT, UTN.

---

## El problema

Los comercios pequeños de este rubro venden por mensajería y redes sociales, y
administran el stock en planillas que no están vinculadas al catálogo que publican.
Una sola persona sostiene la atención comercial, el control de inventario y la
coordinación de reparaciones, lo que produce inconsistencias de stock y consume
el tiempo disponible para hacer crecer el negocio.

Strech centraliza esa operación: un catálogo con disponibilidad real, pedidos que
el cliente arma desde su cuenta y el comercio confirma, un registro unificado de
clientes y el seguimiento de las reparaciones.

---

## Alcance

### Actores

**Vendedor.** Una única persona, dueña del comercio. Administra el catálogo y el
stock, confirma o descarta los pedidos, registra las reparaciones y actualiza su
estado, y genera los mensajes de contacto.

**Cliente.** Consulta el catálogo libremente, pero necesita una cuenta para enviar
un pedido. Desde su cuenta sigue el estado de sus pedidos y de sus reparaciones, y
puede modificar o anular un pedido que todavía no fue confirmado.

### Lo que el sistema hace

| Módulo | Alcance |
|---|---|
| **Catálogo y stock** | alta, baja lógica y modificación de productos, con precio, moneda, categoría y disponibilidad real |
| **Pedidos** | el cliente arma el pedido desde el catálogo; el vendedor lo confirma como venta o lo descarta |
| **Clientes** | cuentas propias con historial unificado de compras y reparaciones |
| **Servicio técnico** | registro de equipos ingresados e historial de estados, consultable por código o desde la cuenta |
| **Mensajes** | plantillas con campos variables que se completan con datos del sistema |

### Lo que queda fuera, y por qué

Cada ausencia responde a una restricción declarada en el análisis, no a una omisión.

| Fuera de alcance | Motivo |
|---|---|
| Pagos en línea | el comercio cobra por fuera del sistema; el pedido es una solicitud, no una compra |
| Proveedores e importación | el control de stock comienza cuando la mercadería ya está disponible |
| Gestión contable y comprobantes fiscales | excede el alcance del trabajo |
| Comunicación con el taller externo | la reparación se terceriza, pero el sistema solo registra su estado |
| Conversión entre divisas | los precios se publican en su moneda original, sin cotización |
| Listas de precios diferenciadas | se maneja una única lista base |

---

## Reglas de negocio

Son las condiciones que el sistema hace cumplir, independientemente de la pantalla
desde la que se opere.

### Sobre el stock

- El stock se descuenta **únicamente cuando el vendedor confirma la venta**, no
  cuando el cliente envía el pedido. Un pedido pendiente no reserva mercadería.
- Un producto que se deja de vender no se elimina: se marca como inactivo. Figura
  en ventas ya concretadas y esa información debe conservarse.

### Sobre los pedidos

- Todo pedido nace en estado **pendiente**.
- Mientras siga pendiente, el cliente puede modificar las cantidades o anularlo.
  Una vez confirmado o descartado por el vendedor, ya no puede intervenir.
- Se distingue entre **descartado** —el vendedor determinó que no se concretaría
  como venta— y **anulado** —el cliente desistió—, porque responden a situaciones
  distintas y conviene poder diferenciarlas.
- Un pedido admite **una sola moneda**. Como el sistema no convierte divisas, un
  pedido que combinara productos en pesos y en dólares no tendría un importe total
  con sentido.
- El detalle conserva el **nombre y el precio del producto al momento de generarse**.
  Si el precio cambia después, el pedido sigue mostrando las condiciones que
  efectivamente tuvo esa operación.

### Sobre las reparaciones

- Cada reparación recibe un **código de seguimiento no secuencial**. De ser
  correlativo, cualquiera podría consultar reparaciones ajenas probando códigos
  contiguos.
- El estado vigente **no se almacena**: se deduce del registro más reciente del
  historial. Guardarlo en dos lugares permitiría que se contradijeran.
- El equipo ingresado se registra como texto libre y no como referencia al catálogo,
  dado que no necesariamente fue adquirido en el comercio.

### Sobre los datos personales

- Se almacena únicamente lo necesario para operar y contactar al cliente.
- Las contraseñas se guardan cifradas.
- Ante una solicitud de eliminación, los campos personales se vacían y el registro
  se marca inactivo, **sin borrarse**. Los datos personales desaparecen y la venta
  permanece registrada sin comprador identificado.

---

## Modelo de datos

Ocho entidades vinculadas por seis relaciones, todas de uno a muchos.

```
Categoria ──1:N── Producto ──1:N── DetallePedido ──N:1── Pedido ──N:1── Cliente
                                                                           │
                                                                          1:N
                                                                           │
                                       CambioEstado ──N:1── Reparacion ────┘

PlantillaMensaje      (sin relaciones)
auth_user             (provista por Django: corresponde al vendedor)
```

| Entidad | Qué representa |
|---|---|
| **Categoria** | agrupación del catálogo. Es una entidad y no una lista fija porque el surtido cambia con cada importación |
| **Producto** | artículo del catálogo, con precio, moneda, stock y estado de actividad |
| **Cliente** | persona con cuenta propia. Inicia sesión con su número de WhatsApp |
| **Pedido** | solicitud de compra, con su estado, su moneda y su importe total |
| **DetallePedido** | línea del pedido. Resuelve la única relación de muchos a muchos del sistema y conserva la foto del producto al momento de la venta |
| **Reparacion** | equipo ingresado al servicio técnico, con su código de seguimiento |
| **CambioEstado** | cada cambio de estado de una reparación, con su fecha |
| **PlantillaMensaje** | texto reutilizable con campos variables. Su tipo indica con qué clase de registro se completa |

El **vendedor no es una entidad propia**: utiliza el esquema de usuarios que provee
Django, que ya resuelve el cifrado de credenciales y los permisos de acceso.

### Criterios de diseño

**Qué se almacena y qué se calcula.** Se almacena aquello que puede variar con el
tiempo y se deriva aquello cuyo cálculo arroja siempre el mismo resultado. Por eso
el importe total del pedido se guarda —recalcularlo con precios posteriores daría
un valor distinto al de la venta— mientras que el estado de una reparación y el
subtotal de una línea se calculan en el momento.

**Qué pasa al borrar.** La eliminación en cascada se reserva para los registros que
carecen de significado sin aquel del que dependen: las líneas de un pedido y el
historial de una reparación. En los demás casos la base rechaza el borrado, de modo
que no puedan perderse ventas ni quedar registros huérfanos.

**Los estados como enumeraciones.** Los estados de pedido y de reparación se definen
en el código y no como tablas, dado que son fijos y ningún requisito contempla que
el vendedor incorpore nuevos.

---

## Tecnologías

| | Versión | Función |
|---|---|---|
| Python | 3.12 | lenguaje del lado del servidor |
| Django | 5.2 LTS | acceso a datos, autenticación, plantillas, sesiones y formularios |
| MySQL | 8.0 | almacenamiento relacional |
| mysqlclient | 2.3.0 | conector entre Django y MySQL |
| python-dotenv | 1.2.4 | lectura de credenciales desde variables de entorno |
| Bootstrap | 5.3 | diseño adaptable a distintos tamaños de pantalla |

Se utiliza **Django 5.2 LTS** y no una versión posterior porque las versiones 6.x
exigen MySQL 8.4 o superior, mientras que 8.0 es la más difundida en los servicios
de alojamiento previstos para el despliegue.

El sistema se estructura como una **aplicación web de un bloque**: un único servidor
recibe las peticiones, consulta la base y devuelve las páginas ya construidas. Se
contempla una instalación por comercio, coherente con el volumen de operación
relevado.

---

## Estructura

```
strech/
├── config/            configuración del proyecto
│   ├── settings.py    ajustes generales y conexión a la base
│   ├── urls.py        mapa de direcciones
│   └── wsgi.py        arranque en el servidor de producción
├── gestion/           aplicación principal
│   ├── models.py      las ocho entidades del modelo de datos
│   ├── admin.py       configuración del panel de administración
│   ├── views.py       lógica de las pantallas
│   └── migrations/    historial del esquema de la base
├── manage.py          punto de entrada de los comandos
├── requirements.txt   dependencias con su versión exacta
└── scriptCreateBD.sql creación de la base y de su usuario
```

El esquema de la base **tiene un único origen**: se define en `models.py` y las
tablas se crean mediante el sistema de migraciones de Django. No se modifican a
mano, de modo que el código y la base no puedan divergir.

Las credenciales no se escriben en el código: se leen de un archivo `.env` excluido
del control de versiones. Eso permite además instalar el sistema en otro comercio
modificando solo la configuración.

---

## Estado

| | |
|---|---|
| Análisis y documentación | requisitos, casos de uso y modelo de datos cerrados |
| Modelo de datos | implementado — 8 entidades, 6 relaciones |
| Panel de administración | funcionando |
| Interfaz del vendedor | en desarrollo |
| Interfaz del cliente | pendiente |
| Despliegue | pendiente |

---

## Puesta en marcha

Requiere **Python 3.12** y **MySQL Server 8.0**.

Tras clonar el repositorio: crear el entorno virtual e instalar `requirements.txt`,
ejecutar `scriptCreateBD.sql` para crear la base y su usuario, copiar `.env.example`
a `.env` completando sus seis variables, y aplicar las migraciones con
`manage.py migrate`.

---

## Autor

Tobías Bonanno — [@bonanno05](https://github.com/bonanno05)
