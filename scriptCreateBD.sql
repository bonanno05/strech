-- Creacion de la base de datos y del usuario de la aplicacion.
-- Se ejecuta una sola vez, al preparar el entorno en una maquina nueva.
--
-- La contrasena real NO se escribe aca: vive en el archivo .env, que esta
-- excluido del control de versiones. Este repositorio es publico.

CREATE DATABASE strech CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'strech'@'localhost' IDENTIFIED BY 'VER_DB_PASSWORD_EN_EL_ARCHIVO_.env';

GRANT ALL PRIVILEGES ON strech.* TO 'strech'@'localhost';

FLUSH PRIVILEGES;