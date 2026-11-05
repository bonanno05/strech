# Modo demostracion (sin MySQL)

Esta rama permite levantar el sistema en una computadora donde no se puede
instalar un servidor MySQL. La base de datos pasa a ser un archivo que Django
crea solo, en lugar de un servidor aparte.

**No reemplaza a la rama `main`.** El proyecto real usa MySQL. Esto es
unicamente para poder mostrar el sistema funcionando en cualquier maquina.

## Que hace falta

Solamente Python 3.12 y Git. Nada mas.

## Pasos

Clonar el repositorio y pararse en esta rama:

    git clone https://github.com/bonanno05/strech.git
    cd strech
    git checkout demo-sin-mysql

Crear el entorno virtual e instalar las dependencias:

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements-demo.txt

Armar la base y cargar el catalogo de ejemplo:

    python manage.py migrate --settings=config.settings_demo
    python manage.py loaddata demo --settings=config.settings_demo

Levantar el servidor:

    python manage.py runserver --settings=config.settings_demo

Y abrir http://127.0.0.1:8000/

## Usuario administrador

El panel de administracion esta en /admin/. Para entrar hay que crear un
usuario, porque no viene ninguno cargado:

    python manage.py createsuperuser --settings=config.settings_demo

## Que diferencia tiene con la rama principal

Lo unico que cambia es el motor de la base de datos. El modelo de datos, las
migraciones, las entidades y todo el codigo son exactamente los mismos. Esa es
justamente una ventaja del mapeo objeto-relacional que usa Django: el codigo no
depende del motor.

Lo que si cambia: SQLite no valida algunos tipos de dato con el mismo rigor que
MySQL, por lo que este modo sirve para mostrar el funcionamiento, no para
reemplazar al entorno real.
