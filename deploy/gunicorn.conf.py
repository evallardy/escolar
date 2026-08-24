"""Configuración de Gunicorn para producción.

Uso (dentro del venv del servidor):
    gunicorn -c deploy/gunicorn.conf.py escolar.wsgi:application
"""
import multiprocessing
import os

# Socket Unix (nginx habla con gunicorn por este socket, no por TCP).
# Se guarda dentro del propio proyecto (no en /run, que es tmpfs y se
# limpia al reiniciar el servidor) para simplificar permisos.
bind = "unix:/var/www/escolar/run/gunicorn.sock"

# Regla estándar: 2 * núcleos + 1. Ajustable con la variable de entorno GUNICORN_WORKERS.
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
timeout = 60
graceful_timeout = 30
keepalive = 5

accesslog = "/var/log/escolar/gunicorn-access.log"
errorlog = "/var/log/escolar/gunicorn-error.log"
loglevel = "info"

# Reinicia workers periódicamente para evitar fugas de memoria acumuladas.
max_requests = 1000
max_requests_jitter = 100
