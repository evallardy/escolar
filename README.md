# Sistema de Administración y Seguimiento Escolar

Plataforma web (Django + Bootstrap + AJAX) para administrar una institución
educativa multi-nivel (Preparatoria, Licenciatura, Maestría, Doctorado) y
multi-plantel: colegiaturas parametrizables, calendario escolar, cardex de
alumnos, asistencia (biométrico + GPS), nómina docente con CFDI, incidencias,
trabajos/tareas y portales ejecutivos por rol (Padres, Alumnos, Docentes,
Administrativos, Directivos).

Ver el diseño completo de arquitectura en [docs/DISENO.md](docs/DISENO.md).

## Stack

- Django 6.1 + Python 3.12
- MySQL/MariaDB (producción) — SQLite solo como fallback de validación local
- Bootstrap 5 + JavaScript (fetch/AJAX) — vistas basadas en clases (CBV) con
  un patrón de template maestro + fragmentos parciales para actualizar solo
  la sección necesaria de la pantalla
- Django REST Framework (API para app móvil de GPS y terminal biométrica)

## Puesta en marcha (desarrollo local)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
# Edita .env: para desarrollo rápido puedes dejar DB_ENGINE=sqlite

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/` — te redirige al login y luego a tu panel
según el rol asignado al usuario (`rol_principal` en el modelo `Usuario`).

## Estructura del proyecto

```
apps/                   Apps de dominio (core, academico, alumnos, docentes,
                         inscripciones, asistencia, finanzas, nomina,
                         incidencias, trabajos, api, portal)
escolar/                Configuración del proyecto (settings, urls, wsgi/asgi)
templates/              Template maestro (base.html) y partials compartidos
static/                 JS (patrón AJAX) y CSS del proyecto
docs/DISENO.md           Documento de arquitectura y diseño de datos
deploy/                 Archivos para desplegar en producción (ver deploy/README.md)
```

## Despliegue a producción

Guía paso a paso en [deploy/README.md](deploy/README.md) para
`escolar.iagmexico.com` (venv + Gunicorn + Nginx + Supervisor + Certbot).
