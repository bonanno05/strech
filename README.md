# Strech

Sistema de gestión para micronegocios de importación de productos tecnológicos.

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

## Módulos

| Módulo | Qué resuelve |
|---|---|
| **Catálogo y stock** | productos con precio, moneda y disponibilidad real |
| **Pedidos** | el cliente arma el pedido y el comercio lo confirma o lo descarta; el stock baja al confirmar |
| **Clientes** | cuentas propias, con historial de compras y reparaciones |
| **Servicio técnico** | seguimiento de reparaciones por código o desde la cuenta del cliente |
| **Mensajes** | generación de mensajes a partir de plantillas con campos variables |

---

## Estado

| | |
|---|---|
| Modelo de datos | implementado — 8 entidades, 6 relaciones |
| Panel de administración | funcionando |
| Interfaz del vendedor | en desarrollo |
| Interfaz del cliente | pendiente |
| Despliegue | pendiente |

---

## Tecnologías

| | Versión | Función |
|---|---|---|
| Python | 3.12 | lenguaje del lado del servidor |
| Django | 5.2 LTS | acceso a datos, autenticación, plantillas y formularios |
| MySQL | 8.0 | almacenamiento relacional |
| mysqlclient | 2.3.0 | conector entre Django y MySQL |
| python-dotenv | 1.2.4 | lectura de variables de entorno |
| Bootstrap | 5.3 | diseño adaptable |

> Se usa Django 5.2 LTS y no una versión posterior porque las versiones 6.x
> requieren MySQL 8.4 o superior, mientras que 8.0 es la versión más difundida
> en los servicios de alojamiento.

---

## Requisitos previos

- Python 3.12
- MySQL Server 8.0
- Git

---

## Instalación

**1. Clonar el repositorio**

```bash
git clone https://github.com/bonanno05/strech.git
cd strech
```

**2. Crear el entorno virtual e instalar las dependencias**

```bash
py -3.12 -m venv venv
```

```bash
# PowerShell
.\venv\Scripts\Activate.ps1

# Git Bash
source venv/Scripts/activate
```

```bash
pip install -r requirements.txt
```

**3. Crear la base de datos y su usuario**

Ejecutar `scriptCreateBD.sql` en MySQL, reemplazando antes el marcador de la
contraseña por la que se vaya a usar.

**4. Configurar las variables de entorno**

Copiar `.env.example` a `.env` y completar:

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | clave secreta de Django |
| `DB_NAME` | nombre de la base |
| `DB_USER` | usuario de la base |
| `DB_PASSWORD` | contraseña de ese usuario |
| `DB_HOST` | `127.0.0.1` |
| `DB_PORT` | `3306`, o el puerto configurado |

Este archivo no se versiona: contiene credenciales.

**5. Crear las tablas y el usuario administrador**

```bash
python manage.py migrate
python manage.py createsuperuser
```

**6. Levantar el servidor**

```bash
python manage.py runserver
```

El panel de administración queda en `http://127.0.0.1:8000/admin/`.

---

## Estructura

```
strech/
├── config/            configuración del proyecto
│   ├── settings.py    ajustes generales
│   ├── urls.py        mapa de direcciones
│   └── wsgi.py        arranque en el servidor
├── gestion/           aplicación principal
│   ├── models.py      las 8 entidades del modelo de datos
│   ├── admin.py       configuración del panel
│   ├── views.py       lógica de las pantallas
│   └── migrations/    historial del esquema de la base
├── manage.py          punto de entrada de los comandos
├── requirements.txt   dependencias con su versión
└── scriptCreateBD.sql creación de la base y su usuario
```

---

## Autor

Tobías Bonanno — [@bonanno05](https://github.com/bonanno05)
