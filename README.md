# Strech

Sistema de gestión para micronegocios de importación de productos tecnológicos.

## El problema

Los comercios pequeños de este rubro venden por mensajería y redes sociales, y
administran el stock en planillas que no están vinculadas al catálogo que publican.
Una sola persona sostiene la atención comercial, el control de inventario y la
coordinación de reparaciones, lo que produce inconsistencias de stock y consume
el tiempo disponible para hacer crecer el negocio.

Strech centraliza esa operación: un catálogo con disponibilidad real, pedidos que
el cliente arma y el comercio confirma, un registro unificado de clientes y el
seguimiento de las reparaciones.

## Estado

En desarrollo. Proyecto final de la Tecnicatura Superior en Informática Aplicada,
INSPT - UTN.

## Tecnologías

- Python 3.12 / Django 6.1.2
- MySQL 8.0
- HTML, CSS y Bootstrap 5.3
- Despliegue en PythonAnywhere

## Funcionalidades

- **Catálogo y stock** — productos con precio, moneda y disponibilidad
- **Pedidos** — el cliente arma un pedido y el comercio lo confirma o lo descarta
- **Clientes** — registro unificado con historial de compras y reparaciones
- **Servicio técnico** — seguimiento de reparaciones mediante código de consulta
- **Mensajes** — generación de mensajes a partir de plantillas

## Cómo ejecutarlo

    git clone https://github.com/bonanno05/strech.git
    cd strech
    py -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    copy .env.example .env
    py manage.py migrate
    py manage.py runserver

Completar la variable `SECRET_KEY` en el archivo `.env` antes de ejecutar.

## Autor

Tobías Bonanno
