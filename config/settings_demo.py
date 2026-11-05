"""
Configuracion para la demostracion, sin servidor MySQL.

Este archivo NO reemplaza a settings.py. Lo importa entero y despues cambia
solamente dos cosas: la clave secreta y la base de datos.

Sirve para levantar el sistema en una computadora donde no se puede instalar
MySQL. En lugar de un servidor, la base pasa a ser un unico archivo llamado
db.sqlite3 que Django crea solo la primera vez.

Se usa agregando --settings=config.settings_demo a cada comando. Por ejemplo:

    python manage.py migrate --settings=config.settings_demo
"""

from config.settings import *


# En settings.py la clave secreta se lee del archivo .env, que no se versiona.
# En una maquina nueva ese archivo no existe y Django no arrancaria.
# Por eso aca se define una clave fija, valida unicamente para mostrar el
# sistema funcionando. Nunca debe usarse en produccion.
SECRET_KEY = 'clave-de-demostracion-no-usar-en-produccion'


# La base de datos deja de ser un servidor aparte y pasa a ser un archivo.
# Es el mismo modelo de datos y las mismas migraciones: lo unico que cambia
# es el motor que las ejecuta.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
