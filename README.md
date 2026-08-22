# Alerta AMBER Panamá — Prototipo

Prototipo de sistema de Alerta AMBER para Panamá: permite al personal administrativo
crear y gestionar alertas de menores desaparecidos, notificarlas por Web Push, y
mostrarlas al público en un sitio con diseño alineado a la identidad de
[Panamá Digital](https://panamadigital.gob.pa/).

## Stack técnico

- **Backend:** Django 5.2 (Python 3.12)
- **Base de datos:** MySQL 8.4
- **Servidor WSGI:** Gunicorn + WhiteNoise (archivos estáticos)
- **Notificaciones:** Web Push (VAPID) vía `pywebpush`
- **Contenedores:** Docker / Docker Compose

## Estructura del proyecto

```
AmberPrototype/
├── amber_alert_project/     # Configuración del proyecto Django (settings, urls raíz)
├── core/                    # App principal: alertas, login, panel admin y sitio público
│   ├── models.py            # Modelo AlertaAmber
│   ├── forms.py             # Formulario de creación de alertas
│   ├── views.py             # Vistas admin y públicas
│   ├── urls.py              # Rutas de la app
│   ├── migrations/
│   ├── services/            # Integraciones externas (Web Push)
│   └── templates/core/
│       ├── admin/           # Panel administrativo (dashboard, crear alerta, detalle)
│       ├── publico/         # Sitio público (inicio, lista de alertas)
│       └── login/           # Login del panel admin
├── notificaciones/          # App de suscripciones Web Push
├── static/                  # CSS compartido (base.css) y específico (admin/público/login)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

### Módulos separados: público vs. admin

- **Público** (`/inicio/`, `/lista_alertas/`, `/detalle_alerta/<id>/`): accesible sin
  login, extiende `core/templates/core/publico/baseUsuario.html`.
- **Admin** (`/dashboard/`, `/crear-alerta/`, `/panel/alertas/`,
  `/panel/alertas/<id>/`): requiere sesión de staff, extiende
  `core/templates/core/admin/base.html`. Tiene su propio nav, header persistente
  ("Panel Admin") y vista de detalle propia (no comparte plantilla con el público).

## Requisitos

- [Docker](https://www.docker.com/) y Docker Compose (recomendado para levantar todo,
  incluida la base de datos, sin instalar nada más).
- Alternativa sin Docker: Python 3.12+, MySQL 8.x corriendo localmente.

## Instalación y ejecución (con Docker)

1. Cloná el repositorio:
   ```bash
   git clone https://github.com/Reelez/AmberPrototype-.git
   cd AmberPrototype-
   ```

2. Creá un archivo `.env` en la raíz del proyecto con estas variables:
   ```env
   # Django
   SECRET_KEY=tu-secret-key
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost

   # Base de datos (usadas también por el contenedor de MySQL)
   DB_NAME=amber_db
   DB_USER=amber_user
   DB_PASSWORD=amber_dev_pass
   DB_ROOT_PASSWORD=amber_root_dev_pass

   # Notificaciones Web Push (VAPID) — generar par de claves con py-vapid
   VAPID_PUBLIC_KEY=
   VAPID_PRIVATE_KEY=
   VAPID_CLAIMS_EMAIL=dev@example.com

   # API de despacho (uso interno de notificaciones)
   DISPATCH_API_KEY=dev-dispatch-api-key
   ```
   > `SECRET_KEY`, `DB_*`, `VAPID_*` y `DISPATCH_API_KEY` son obligatorias — la app no
   > arranca sin ellas. Para desarrollo local podés usar valores de prueba; para
   > producción generá valores reales y no los subas al repo.

3. Levantá los contenedores:
   ```bash
   docker compose up -d --build
   ```
   Esto construye la imagen de la app, levanta MySQL, corre las migraciones y
   arranca Gunicorn.

4. Creá un superusuario (o usá las credenciales de prueba de abajo si ya cargaste una
   base de datos con uno):
   ```bash
   docker compose exec amber python manage.py createsuperuser
   ```

5. La app queda disponible en **http://localhost:8001**
   (el puerto se mapea `8001:8000` en `docker-compose.yml` para no chocar con otros
   proyectos locales que usen el 8000 — cambialo si lo necesitás).

## Credenciales de prueba

Para el panel administrativo (login en `/`):

| Usuario | Contraseña |
|---------|------------|
| `admin` | `admin1234` |

> Estas son credenciales de desarrollo. Cambialas (o creá un usuario nuevo) antes de
> exponer el proyecto fuera de tu máquina.

## Rutas principales

| Ruta | Acceso | Descripción |
|------|--------|-------------|
| `/` | Público | Login del panel admin |
| `/inicio/` | Público | Página de inicio del sitio |
| `/lista_alertas/` | Público | Listado de alertas activas |
| `/detalle_alerta/<id>/` | Público | Detalle de una alerta |
| `/dashboard/` | Admin | Panel principal con listado y estado de alertas |
| `/crear-alerta/` | Admin | Wizard paso a paso para crear una alerta |
| `/panel/alertas/` | Admin | Listado administrativo de alertas |
| `/panel/alertas/<id>/` | Admin | Detalle admin (activar/desactivar alerta) |

## Notas de desarrollo

- Los estilos comparten una base de diseño única en `static/base.css` (paleta,
  tipografía, header/nav/footer, botones y componentes reutilizados entre el sitio
  público y el panel admin); `estilos_admin.css`, `estilos_public.css` y
  `estilo_login.css` contienen únicamente estilos específicos de cada sección.
- La funcionalidad de alertas por SMS (Twilio) fue removida del proyecto.
