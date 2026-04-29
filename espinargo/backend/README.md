# EspinarGo Backend API

Backend de EspinarGo, una aplicación de transporte tipo InDrive para la ciudad de Espinar, Cusco, Perú. Permite a los pasajeros solicitar viajes y a los conductores aceptar ofertas de precio.

## Stack Tecnológico

| Tecnología | Versión | Para qué se usa |
|------------|---------|-----------------|
| Python | 3.12 | Lenguaje principal |
| FastAPI | 0.109+ | Framework web async |
| PostgreSQL | 16 | Base de datos relacional |
| Redis | 7 | Cache y rate limiting |
| SQLAlchemy | 2.0 | ORM async |
| Twilio | - | Envío de SMS OTP |
| Cloudinary | - | Almacenamiento de imágenes |
| Docker | - | Contenedores |
| Railway | - | Despliegue en producción |

## Estructura del Proyecto

```
backend/
├── app/
│   ├── api/v1/          # Endpoints REST
│   │   └── endpoints/   # Módulos: auth, users, trips, packages, ratings
│   ├── core/            # Configuración: database, config, security
│   ├── middleware/      # Dependencias de autenticación
│   ├── models/          # Modelos SQLAlchemy
│   ├── schemas/         # Validaciones Pydantic
│   ├── services/        # Lógica de negocio
│   └── main.py          # Punto de entrada
├── scripts/             # Scripts de inicialización
├── tests/               # Tests unitarios e integrados
├── Dockerfile           # Imagen Docker
└── docker-compose.yml   # Servicios locales
```

## Requisitos Previos

- Python 3.12
- Docker Desktop
- Git

## Configuración Inicial

### 1. Clonar y crear entorno virtual

```bash
git clone <repo-url>
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 4. Levantar servicios con Docker

```bash
docker-compose up -d postgres redis
```

### 5. Inicializar base de datos

```bash
python scripts/init_db.py
```

### 6. Crear usuario administrador

```bash
python scripts/create_admin.py
```

### 7. Iniciar servidor

```bash
uvicorn app.main:app --reload --port 8000
```

## Comandos Útiles

### Desarrollo
```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs de la API
docker-compose logs -f api

# Detener servicios
docker-compose down

# Ejecutar tests
pytest tests/unit/test_auth.py -v

# Formatear código
black app/
```

## Endpoints Principales

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /api/v1/auth/register | Crear cuenta nueva |
| POST | /api/v1/auth/verify-phone | Verificar teléfono |
| POST | /api/v1/auth/login | Iniciar sesión |
| POST | /api/v1/auth/refresh | Renovar token |
| POST | /api/v1/auth/logout | Cerrar sesión |
| GET | /api/v1/auth/me | Mi perfil |

### Viajes
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /api/v1/trips | Solicitar viaje |
| GET | /api/v1/trips/active | Ver viaje activo |
| POST | /api/v1/trips/offer | Hacer oferta |
| POST | /api/v1/trips/{id}/accept-offer | Aceptar oferta |
| POST | /api/v1/trips/{id}/start | Iniciar viaje |
| POST | /api/v1/trips/{id}/complete | Completar viaje |

### Encomiendas
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /api/v1/packages | Crear encomienda |
| GET | /api/v1/packages/track/{code} | Rastrear (público) |
| POST | /api/v1/packages/{id}/assign | Asignar a conductor |

## Flujo de Autenticación

```
1. Registro → POST /auth/register
2. OTP SMS → POST /auth/verify-phone (código: 123456 en dev)
3. Login → POST /auth/login → access_token (30 min) + refresh_token (30 días)
4. Requests → Authorization: Bearer <access_token>
5. Refresh → POST /auth/refresh → nuevo access_token
```

## Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| DATABASE_URL | URL de PostgreSQL async | postgresql+asyncpg://... |
| DATABASE_URL_SYNC | URL de PostgreSQL sync | postgresql+psycopg2://... |
| REDIS_URL | URL de Redis | redis://localhost:6379/0 |
| JWT_SECRET_KEY | Clave para firmar JWT | random-string |
| TWILIO_* | Credenciales de Twilio | - |
| CLOUDINARY_* | Credenciales de Cloudinary | - |
| SENTRY_DSN | DSN de Sentry (opcional) | https://... |

## Despliegue en Railway

1. Crear proyecto en Railway
2. Agregar servicio PostgreSQL
3. Agregar servicio Redis (opcional, usar Redis de Railway)
4. Conectar repositorio de GitHub
5. Configurar variables de entorno en Railway
6. Deploy automático al pushear a main

## Solución de Problemas

### Error de conexión a la DB
- Verificar que PostgreSQL esté corriendo: `docker ps`
- Revisar que DATABASE_URL sea correcta

### Error de Twilio en OTP
- En desarrollo el código siempre es "123456"
- Verificar credenciales de Twilio en .env

### Error de CORS
- Revisar ALLOWED_ORIGINS en config.py
- Agregar el origen de tu frontend

### Puerto ya en uso
- Cambiar puerto: `uvicorn app.main:app --port 8001`
- O matar proceso: `lsof -ti:8000 | xargs kill`

---

**EspinarGo** - Hecho con ❤️ para Espinar, Cusco, Perú