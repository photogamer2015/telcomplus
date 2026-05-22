# Telcomplus QR Demo

Demo Django para registrar equipos, generar QR por equipo y permitir que cualquier persona reporte una novedad desde el QR sin iniciar sesion.

## Arranque rapido

```bash
cd /Users/yandrig/Desktop/telcomplus_qr_demo
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py load_demo_data
python3 manage.py runserver 127.0.0.1:8000
```

## Despliegue en Render

Este proyecto incluye `render.yaml`, `build.sh` y `start.sh`.

1. Sube esta carpeta a un repositorio de GitHub.
2. En Render, crea un `New Blueprint Instance`.
3. Conecta el repositorio.
4. Render creara el Web Service y PostgreSQL automaticamente.
5. Cuando termine el deploy, entra a la URL `.onrender.com`.

Los QR se regeneran al iniciar Render con la URL publica del servicio.

## Usuarios demo

- `admin` / `admin123`
- `tecnico` / `tecnico123`
- `contrato` / `contrato123`

## Flujo principal

1. Ingresar al panel en `http://127.0.0.1:8000/login/`.
2. Crear o revisar equipos en `Equipos y QR`.
3. Descargar el QR de un equipo.
4. Escanear el QR: abre una pagina publica con los datos del equipo precargados.
5. El cliente completa nombre, telefono, empresa y problema.
6. El reporte entra al modulo interno de tickets.
