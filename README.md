# Alerta AMBER Panamá — Prototipo

Prototipo para la difusión de Alertas AMBER en Panamá mediante tecnología **Web Push**.
El personal autorizado crea y gestiona alertas de menores desaparecidos desde un panel
administrativo; al registrarse una alerta, el sistema envía una notificación push a todos
los navegadores suscritos y la publica en un portal público con diseño alineado a la
identidad de [Panamá Digital](https://panamadigital.gob.pa/).

Proyecto de trabajo de graduación — Universidad Tecnológica de Panamá.

## Stack técnico

- **Backend:** Django 5.2 (Python 3.12), patrón MVT
- **Base de datos:** MySQL 8.4 (`mysql-connector-python`)
- **Servidor WSGI:** Gunicorn + WhiteNoise (archivos estáticos)
- **Notificaciones:** Web Push con VAPID (ECDSA P-256) vía `pywebpush`; Service Worker y Push API (W3C)
- **Interoperabilidad:** API JSON de solo lectura y exportación en formato CAP v1.2
- **Entorno local:** Docker / Docker Compose

## Funcionalidades

| Requisito | Implementación |
|-----------|----------------|
| RF1 Autenticación | Login exclusivo para usuarios `is_staff`; vistas del panel protegidas |
| RF2 Gestión de alertas | Crear (asistente de 6 pasos), consultar, editar y marcar como encontrada |
| RF3 Portal público | Inicio, listado de alertas activas y detalle, sin login |
| RF4 Suscripción Web Push | Botón "Activar alertas"; guarda endpoint y claves `p256dh`/`auth` |
| RF5 Difusión masiva | Envío en segundo plano a todas las suscripciones (TTL 24 h, urgencia alta) |
| RF6 Contacto | Botones de llamada `tel:104` (Policía Nacional) y `tel:5201000` (DIJ) |
| RF7 Depuración | Suscripciones con respuesta HTTP 404/410 se eliminan automáticamente |

Navegadores validados: **Google Chrome**, **Microsoft Edge** y **Mozilla Firefox**.

## Estructura del proyecto

```
AmberPrototype/
├── amber_alert_project/     # Configuración Django (settings, urls raíz)
├── core/                    # Alertas: login, panel admin, portal público, API/CAP
│   ├── models.py            # Modelo AlertaAmber
│   ├── forms.py             # Formulario con validación y sanitización
│   ├── views.py             # Vistas admin y públicas
│   ├── api.py               # API JSON y exportación CAP v1.2
│   ├── services/            # Despacho de Web Push en segundo plano
│   ├── tests.py             # Pruebas PF1–PF4 y PF8
│   └── templates/core/      # admin/, publico/, login/
├── notificaciones/          # Suscripciones Web Push y envío (pywebpush)
│   └── tests.py             # Pruebas PF5–PF7
├── static/                  # CSS y service-worker.js
├── scripts/                 # Utilidades (generar claves VAPID, limpiar alertas)
├── docs/capitulo_v/         # Borrador del Capítulo V, figuras y resultados de pruebas
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Instalación en otro equipo (con Docker)

**Requisitos:** [Git](https://git-scm.com/) y [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Reelez/AmberPrototype-.git
   cd AmberPrototype-
   ```

2. **Crear el archivo `.env`** en la raíz del proyecto con este contenido
   (el `.env` no se sube al repositorio):
   ```env
   # Django
   SECRET_KEY=cambiar-por-una-cadena-larga-y-aleatoria
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   # Solo si se usa un túnel o dominio HTTPS (separados por coma)
   CSRF_TRUSTED_ORIGINS=

   # Base de datos (también crea el usuario del contenedor MySQL)
   DB_NAME=amber_db
   DB_USER=amber_user
   DB_PASSWORD=amber_dev_pass
   DB_ROOT_PASSWORD=amber_root_dev_pass

   # Web Push (VAPID) — ver paso 3
   VAPID_PUBLIC_KEY=
   VAPID_PRIVATE_KEY=
   VAPID_CLAIMS_EMAIL=dev@example.com
   ```

3. **Generar las claves VAPID** y pegarlas en el `.env`:
   ```bash
   docker compose build amber
   docker compose run --rm --no-deps amber python scripts/generar_claves_vapid.py
   ```
   El comando imprime `VAPID_PUBLIC_KEY=...` y `VAPID_PRIVATE_KEY=...`.
   Sin claves válidas el navegador no puede suscribirse.
   Si se cambian las claves, todas las suscripciones existentes dejan de funcionar.

4. **Levantar el proyecto**
   ```bash
   docker compose up -d --build
   ```
   Construye la imagen, levanta MySQL, aplica las migraciones y arranca Gunicorn.

5. **Crear el usuario administrador**
   ```bash
   docker compose exec amber python manage.py createsuperuser
   ```

6. Abrir **http://localhost:8001** (login del panel) y **http://localhost:8001/inicio/**
   (portal público).

## Probar las notificaciones

1. Abrir `http://localhost:8001/inicio/` en Chrome, Edge o Firefox y pulsar **"Activar alertas"**.
2. En otra pestaña, iniciar sesión en `http://localhost:8001/` y crear una alerta.
3. La notificación llega a cada navegador suscrito; al pulsarla se abre el detalle de la alerta.

`localhost` es un contexto seguro para el navegador, por lo que no requiere HTTPS.
Si no aparece la notificación, revisar que Windows tenga habilitadas las notificaciones
del navegador y que el modo "No molestar" esté desactivado.

### Desde un celular u otro dispositivo de la red

Los Service Workers solo funcionan en `localhost` o bajo **HTTPS**, por lo que acceder por
IP (`http://192.168.x.x:8001`) no permite suscribirse. Para probar desde un celular se puede
usar un túnel HTTPS, por ejemplo con [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/):

```bash
cloudflared tunnel --url http://localhost:8001
```

Con la URL que genera (por ejemplo `https://xyz.trycloudflare.com`), agregar en el `.env`:

```env
ALLOWED_HOSTS=127.0.0.1,localhost,xyz.trycloudflare.com
CSRF_TRUSTED_ORIGINS=https://xyz.trycloudflare.com
```

y reiniciar la app con `docker compose up -d amber`. En iPhone, Web Push solo funciona si el
sitio se agrega a la pantalla de inicio.

## Ver la base de datos

MySQL queda expuesto solo para el equipo local en el puerto **3307**. Con DBeaver u otro cliente:

| Campo | Valor |
|-------|-------|
| Host | `localhost` |
| Puerto | `3307` |
| Base de datos | valor de `DB_NAME` |
| Usuario / contraseña | valores de `DB_USER` / `DB_PASSWORD` |

En DBeaver, en *Driver properties*, configurar `allowPublicKeyRetrieval=true` y `useSSL=false`.

## Pruebas automatizadas

```bash
docker compose exec amber python manage.py test -v 2
```

Ejecuta 37 pruebas agrupadas en los casos PF1–PF8. Si la base es nueva y falla con un error
de permisos al crear `test_amber_db`, otorgar el permiso una sola vez:

```bash
docker compose exec db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "GRANT ALL ON \`test\_%\`.* TO \"$MYSQL_USER\"@\"%\";"'
```

## Rutas principales

| Ruta | Acceso | Descripción |
|------|--------|-------------|
| `/` | Público | Login del panel admin |
| `/inicio/` | Público | Inicio del portal y botón "Activar alertas" |
| `/lista_alertas/` | Público | Listado de alertas activas |
| `/detalle_alerta/<id>/` | Público | Detalle de una alerta con botones de llamada |
| `/dashboard/` | Admin | Panel principal |
| `/crear-alerta/` | Admin | Asistente para crear una alerta |
| `/panel/alertas/<id>/` | Admin | Detalle admin (editar, marcar como encontrada) |
| `/panel/alertas/<id>/editar/` | Admin | Edición de una alerta (no reenvía notificaciones) |
| `/api/alertas/` | Público | Alertas activas en JSON |
| `/api/alertas/<id>/` | Público | Una alerta en JSON |
| `/api/alertas/<id>/cap.xml` | Público | Alerta en formato CAP v1.2 |

## Seguridad

- El archivo `.env` (claves VAPID, contraseñas, `SECRET_KEY`) nunca debe subirse al repositorio.
- La clave privada VAPID solo vive en el servidor; sin ella no es posible enviar notificaciones
  a las suscripciones aunque la base de datos se vea comprometida.
- Las suscripciones no almacenan datos personales identificables.
- Con `DEBUG=False` se activan cookies seguras; en producción el sitio debe servirse por HTTPS.
- Las credenciales de prueba son solo para desarrollo; usar contraseñas robustas fuera de la máquina local.
