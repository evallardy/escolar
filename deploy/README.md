# Despliegue en producción — escolar.iagmexico.com

Método: **tradicional** (venv + Gunicorn + Nginx + Supervisor), sin Docker,
con SSL vía **Certbot/Let's Encrypt**. Despliegue **manual** (no hay CI/CD
automático): tú corres `git pull` en el servidor y reinicias el servicio.

Todas las rutas de abajo asumen que el proyecto vive en `/var/www/escolar`
y que corre bajo un usuario dedicado `escolar` (sin privilegios root). Ajusta
las rutas/usuario si tu servidor usa otra convención.

## 1. Preparar el servidor (una sola vez)

```bash
sudo adduser --system --group --home /var/www/escolar escolar
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential \
    default-libmysqlclient-dev pkg-config nginx supervisor certbot \
    python3-certbot-nginx git mysql-server
```

Crea la base de datos y el usuario de MySQL para la app:

```sql
CREATE DATABASE escolar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'escolar_app'@'localhost' IDENTIFIED BY 'una-contraseña-segura';
GRANT ALL PRIVILEGES ON escolar.* TO 'escolar_app'@'localhost';
FLUSH PRIVILEGES;
```

## 2. Clonar el repositorio y crear el entorno virtual

```bash
sudo -u escolar git clone https://github.com/<tu-usuario>/<tu-repo>.git /var/www/escolar
cd /var/www/escolar
sudo -u escolar python3 -m venv .venv
sudo -u escolar .venv/bin/pip install --upgrade pip
sudo -u escolar .venv/bin/pip install -r requirements-production.txt
```

## 3. Configurar variables de entorno

```bash
sudo -u escolar cp deploy/.env.production.example .env
sudo -u escolar nano .env   # llenar SECRET_KEY, password de BD, etc.
```

Genera una `SECRET_KEY` segura con:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 4. Migraciones, estáticos y superusuario

```bash
sudo -u escolar mkdir -p run
sudo -u escolar .venv/bin/python manage.py migrate
sudo -u escolar .venv/bin/python manage.py collectstatic --noinput
sudo -u escolar .venv/bin/python manage.py createsuperuser
sudo mkdir -p /var/log/escolar && sudo chown escolar:www-data /var/log/escolar
```

## 5. Supervisor (mantiene Gunicorn corriendo)

```bash
sudo cp deploy/supervisor/escolar.conf /etc/supervisor/conf.d/escolar.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status escolar
```

## 6. Nginx

```bash
sudo cp deploy/nginx/escolar.iagmexico.com.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/escolar.iagmexico.com.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Antes de tener certificado SSL, comenta temporalmente el bloque `server`
del puerto 443 en ese archivo (o usa el asistente de certbot, paso 7, que
lo configura automáticamente).

## 7. Certificado SSL (Let's Encrypt / Certbot)

Requiere que el DNS de `escolar.iagmexico.com` ya apunte a la IP del
servidor.

```bash
sudo certbot --nginx -d escolar.iagmexico.com
```

Certbot instala el certificado, ajusta el `server` de nginx y programa la
renovación automática (verifica con `sudo certbot renew --dry-run`).

## 8. Verificar

Abre `https://escolar.iagmexico.com/` — deberías ver la pantalla de login.

## 9. Actualizar a una nueva versión (despliegue manual)

Cada vez que quieras subir cambios ya probados:

```bash
cd /var/www/escolar
sudo -u escolar git pull origin main
sudo -u escolar .venv/bin/pip install -r requirements-production.txt
sudo -u escolar .venv/bin/python manage.py migrate
sudo -u escolar .venv/bin/python manage.py collectstatic --noinput
sudo supervisorctl restart escolar
```

## Notas de seguridad

- El `.env` de producción **nunca** se sube al repositorio (ya está en
  `.gitignore`).
- `DJANGO_DEBUG=False` en producción siempre; con eso se activan
  automáticamente `SECURE_SSL_REDIRECT`, cookies seguras y HSTS (ver
  `escolar/settings.py`).
- Restringe el acceso SSH (llaves, no contraseña) y mantén el sistema
  operativo actualizado (`unattended-upgrades` recomendado).
- Haz respaldos periódicos de la base de datos MySQL y de la carpeta
  `media/` (documentos de alumnos, trabajos, fotos).
