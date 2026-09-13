# Semillero — Beta

Plataforma para el seguimiento del desarrollo de peloteros del béisbol menor venezolano.

## Cómo correrlo localmente

1. Crear y activar un entorno virtual:
   ```
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```
   (si no vas a usar Postgres todavía, puedes omitir psycopg2-binary y comentar esa línea)
3. Aplicar migraciones:
   ```
   python manage.py migrate
   ```
4. Cargar datos de ejemplo (ficticios, para probar el buscador):
   ```
   python manage.py cargar_datos_ejemplo
   ```
5. Crear tu propio usuario administrador:
   ```
   python manage.py createsuperuser
   ```
6. Levantar el servidor:
   ```
   python manage.py runserver
   ```

## Rutas

- `/` — Buscador de jugadores (público)
- `/admin/` — Panel de administración (login de equipo/liga)

Usuario de prueba ya incluido en la base de datos que se entrega con el proyecto:
- usuario: `admin`
- contraseña: `semillero2026`

Es superusuario — ve todo. Para probar cómo se comporta un admin de club real (que solo ve
los jugadores de su propio club), créalo desde `/admin/` como usuario normal y luego asígnale
un "Perfil de administrador" con rol "Administrador de club" y su club correspondiente.

**Cambia esta contraseña antes de usar el proyecto fuera de tu máquina.**

## Conectar a PostgreSQL (Supabase / Neon) en vez de SQLite

Define estas variables de entorno antes de correr el servidor:
```
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=5432
```
Si `DB_NAME` no está definida, el proyecto usa SQLite automáticamente (cero configuración),
que es como se entrega este beta.

## Estructura de datos

Liga → Campeonato (por Categoría y Temporada) → Equipo (de un Club) → Jugador → (Representante, Videos)

Cada decisión de este modelo (por qué Club y Equipo son entidades separadas, por qué
Representante existe como tabla propia con campo de consentimiento, etc.) está documentada
en la conversación de diseño — vale la pena pasarla a un documento formal para el capítulo
de metodología de la tesis.

## Próximos pasos naturales

1. Formulario de carga de video en el panel de administrador (hoy se sube desde /admin/ pero sin interfaz a medida)
2. Conectar almacenamiento de video en Cloudflare R2 en vez de guardar archivos localmente
3. Vista de perfil individual del jugador (hoy el buscador muestra tarjetas, falta la página de detalle)
4. Registro público de representantes con firma de consentimiento
