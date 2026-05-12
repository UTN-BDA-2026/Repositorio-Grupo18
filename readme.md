# 🐄 SmartFarming API

Backend para un sistema de monitoreo ganadero inteligente, inspirado en [Halter](https://haltercollars.com/). Cada animal lleva un collar **ESP32** que transmite telemetría GPS + acelerómetro. El backend almacena, analiza y genera alertas en tiempo real usando una arquitectura **polígola** (PostgreSQL + MongoDB + pgvector).

---

## Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Modelos de datos](#modelos-de-datos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación local](#instalación-local)
- [Instalación con Docker](#instalación-con-docker)
- [Variables de entorno](#variables-de-entorno)
- [Endpoints disponibles](#endpoints-disponibles)
- [Flujo de telemetría](#flujo-de-telemetría)
- [Motor de análisis de comportamiento](#motor-de-análisis-de-comportamiento-pgvector)
- [Próximos pasos](#próximos-pasos)

---

## Arquitectura

```
┌──────────────────┐     POST /api/v1/ingest     ┌───────────────────────┐
│   ESP32 Collar   │ ──────────────────────────▶ │   FastAPI (Python)    │
│  GPS + IMU/Accel │                              │                       │
└──────────────────┘                              │  ┌─────────────────┐  │
                                                  │  │  TelemetryService│  │
                                                  │  └────────┬────────┘  │
                                                  │           │            │
                                          ┌───────┼───────────┤            │
                                          │       │           │            │
                                          ▼       ▼           ▼            │
                                      MongoDB  Postgres  BackgroundTask    │
                                     (raw GPS  (device   (behavior         │
                                      + accel)  metadata)  analysis)       │
                                                  │                        │
                                                  ▼                        │
                                             pgvector                      │
                                          (similarity                      │
                                           search)                         │
                                                  │                        │
                                                  ▼                        │
                                           HealthAlert ◀──────────────────┘
                                          (Postgres)
```

### ¿Por qué tres bases de datos?

| Base de datos | Uso | Justificación |
|---|---|---|
| **PostgreSQL** | Animales, operadores, lotes, dispositivos, sesiones, alertas | Integridad referencial total. Las relaciones entre entidades son fijas y conocidas. |
| **MongoDB** | Telemetría cruda (GPS + acelerómetro) | Un solo animal genera un documento cada pocos segundos. A 50 animales = ~150k docs/día. MongoDB maneja esto sin esquema rígido y con queries por rango de tiempo. |
| **pgvector** | Vectores de comportamiento de referencia | Extensión de Postgres que permite búsqueda por similitud coseno en O(log n). Detecta patrones como "pre-parto" o "cojera" comparando ventanas de acelerómetro. |

---

## Modelos de datos

### PostgreSQL (SQLAlchemy async)

```
operators
  id (UUID PK)
  name, email, hashed_password
  role: "admin" | "operator" | "vet"
  is_active, created_at

grazing_lots
  id (UUID PK)
  name, geofence (GeoJSON string), area_hectares
  operator_id → operators.id

livestock
  id (UUID PK)
  tag (ear-tag único), species, breed
  birth_date, sex, weight_kg
  operator_id → operators.id
  is_active, created_at

devices
  id (UUID PK)
  hardware_id (MAC del ESP32, único)
  firmware_version, battery_pct, last_seen
  animal_id → livestock.id  (1-to-1)
  is_active, created_at

grazing_sessions
  id (UUID PK)
  animal_id → livestock.id
  lot_id    → grazing_lots.id
  started_at, ended_at (NULL = sesión abierta)

health_alerts
  id (UUID PK)
  animal_id   → livestock.id
  alert_type: "behavior" | "geofence" | "battery" | "no_signal"
  pattern_label, similarity_score
  message, resolved, created_at

behavior_patterns
  id (UUID PK)
  label, description
  embedding VECTOR(128)   ← pgvector
  created_at
```

### MongoDB (Motor async)

**Colección `telemetry`** — un documento por lectura del collar:
```json
{
  "_id": "ObjectId",
  "device_hardware_id": "AA:BB:CC:DD:EE:FF",
  "timestamp": "2024-10-01T12:00:00Z",
  "lat": -34.6037,
  "lng": -58.3816,
  "altitude_m": 25.4,
  "gps_accuracy_m": 3.1,
  "accel": { "x": 0.12, "y": -0.05, "z": 9.81 },
  "battery_pct": 87.5
}
```

Índice: `{ device_hardware_id: 1, timestamp: -1 }`

---

## Estructura del proyecto

```
smartfarming/
├── app/
│   ├── main.py                   # Entrypoint FastAPI + lifespan
│   ├── api/
│   │   └── v1/
│   │       ├── router.py         # Registra todos los sub-routers
│   │       └── endpoints/
│   │           ├── ingest.py     # POST /ingest  ← lo llama el ESP32
│   │           ├── livestock.py  # CRUD animales
│   │           ├── devices.py    # CRUD collares
│   │           ├── alerts.py     # GET + resolve alertas
│   │           ├── sessions.py   # Sesiones de pastoreo
│   │           └── telemetry.py  # Query telemetría desde MongoDB
│   ├── core/
│   │   └── config.py             # Settings (Pydantic BaseSettings + .env)
│   ├── db/
│   │   ├── postgres.py           # Engine async + get_db dependency
│   │   └── mongo.py              # Motor client + helpers de colecciones
│   ├── models/
│   │   └── sql.py                # Todos los modelos SQLAlchemy
│   ├── schemas/
│   │   └── schemas.py            # Pydantic schemas (Create / Read)
│   ├── services/
│   │   └── telemetry.py          # Lógica de ingesta (MongoDB + Postgres)
│   └── workers/
│       └── behavior.py           # Análisis pgvector (BackgroundTask)
├── scripts/
│   ├── init_pgvector.sql         # Habilita extensión vector en Postgres
│   └── seed_patterns.py          # Carga patrones de referencia en pgvector
├── tests/
│   └── test_endpoints.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Instalación local

### Prerrequisitos

- Python 3.12+
- PostgreSQL 16 con extensión `pgvector` instalada
- MongoDB 7.0+
- Redis 7+ (opcional, para tareas en background más robustas)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/smartfarming-api.git
cd smartfarming-api

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales locales de Postgres y Mongo

# 5. Habilitar pgvector en tu Postgres local
psql -U postgres -d smartfarming -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 6. Cargar patrones de comportamiento de referencia
python scripts/seed_patterns.py

# 7. Levantar el servidor
uvicorn app.main:app --reload --port 8000
```

Las tablas de Postgres se crean automáticamente al iniciar la app (via `Base.metadata.create_all`).

Accedé a la documentación interactiva en: **http://localhost:8000/docs**

---

## Instalación con Docker

Docker Compose levanta todos los servicios con un solo comando: la API, Postgres con pgvector, MongoDB y Redis.

### Requisitos

- Docker 24+
- Docker Compose v2+

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/smartfarming-api.git
cd smartfarming-api

# 2. Crear archivo de variables de entorno
cp .env.example .env
# Podés dejar los valores por defecto para desarrollo

# 3. Construir y levantar todos los servicios
docker compose up --build

# La API estará disponible en http://localhost:8000
# Docs en http://localhost:8000/docs
```

### Comandos útiles

```bash
# Levantar en background
docker compose up -d

# Ver logs de la API en tiempo real
docker compose logs -f api

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (borra todos los datos)
docker compose down -v

# Levantar también Mongo Express (UI para MongoDB)
docker compose --profile tools up
# Mongo Express disponible en http://localhost:8081
```

### Cargar patrones de comportamiento con Docker

```bash
# Mientras los contenedores están corriendo:
docker compose exec api python scripts/seed_patterns.py
```

### Servicios y puertos

| Servicio | Puerto | Descripción |
|---|---|---|
| `api` | 8000 | FastAPI + Uvicorn |
| `postgres` | 5432 | PostgreSQL 16 + pgvector |
| `mongo` | 27017 | MongoDB 7 |
| `redis` | 6379 | Redis 7 |
| `mongo-express` | 8081 | UI MongoDB (perfil `tools`) |

---

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `DEBUG` | `false` | Activa logs SQL y recarga automática |
| `POSTGRES_HOST` | `localhost` | Host de PostgreSQL |
| `POSTGRES_PORT` | `5432` | Puerto de PostgreSQL |
| `POSTGRES_USER` | `postgres` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `changeme` | Contraseña de PostgreSQL |
| `POSTGRES_DB` | `smartfarming` | Nombre de la base de datos |
| `MONGO_HOST` | `localhost` | Host de MongoDB |
| `MONGO_PORT` | `27017` | Puerto de MongoDB |
| `MONGO_USER` | `mongo` | Usuario de MongoDB |
| `MONGO_PASSWORD` | `changeme` | Contraseña de MongoDB |
| `MONGO_DB` | `smartfarming_telemetry` | Base de datos de telemetría |
| `REDIS_HOST` | `localhost` | Host de Redis |
| `SECRET_KEY` | `change-me` | Clave secreta para JWT |
| `BEHAVIOR_VECTOR_DIM` | `128` | Dimensión de los vectores de comportamiento |
| `ALERT_SIMILARITY_THRESHOLD` | `0.85` | Umbral de similitud coseno para disparar alertas |

---

## Endpoints disponibles

Una vez levantada la app, la documentación completa está en `/docs` (Swagger UI) y `/redoc`.

### Resumen

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/ingest` | **Recibe telemetría del ESP32** |
| `GET` | `/api/v1/livestock` | Listar animales |
| `POST` | `/api/v1/livestock` | Registrar animal |
| `GET` | `/api/v1/livestock/{id}` | Detalle de un animal |
| `PATCH` | `/api/v1/livestock/{id}` | Actualizar animal |
| `DELETE` | `/api/v1/livestock/{id}` | Desactivar animal |
| `GET` | `/api/v1/devices` | Listar collares |
| `POST` | `/api/v1/devices` | Registrar collar |
| `GET` | `/api/v1/devices/{id}` | Detalle de un collar |
| `GET` | `/api/v1/telemetry/{hardware_id}` | Últimas lecturas de un collar (MongoDB) |
| `GET` | `/api/v1/alerts` | Listar alertas (filtro por `resolved`) |
| `PATCH` | `/api/v1/alerts/{id}/resolve` | Marcar alerta como resuelta |
| `GET` | `/api/v1/sessions` | Listar sesiones de pastoreo |
| `POST` | `/api/v1/sessions` | Abrir sesión |
| `PATCH` | `/api/v1/sessions/{id}/close` | Cerrar sesión |

### Ejemplo: ingestión desde ESP32

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_hardware_id": "AA:BB:CC:DD:EE:FF",
    "timestamp": "2024-10-01T12:00:00Z",
    "lat": -34.6037,
    "lng": -58.3816,
    "accel": { "x": 0.12, "y": -0.05, "z": 9.81 },
    "battery_pct": 87.5
  }'
```

---

## Flujo de telemetría

```
ESP32
  │
  │  POST /api/v1/ingest  (cada N segundos)
  ▼
TelemetryService.ingest()
  ├─ 1. INSERT en MongoDB (telemetry collection)
  ├─ 2. UPDATE Device.last_seen + battery_pct en Postgres
  └─ 3. Si count % 30 == 0 → BackgroundTask: analyze_behavior_window()

analyze_behavior_window()
  ├─ Fetch últimas 30 lecturas de MongoDB
  ├─ Extrae vector de features (media, std, RMS, FFT por eje X/Y/Z)
  ├─ pgvector: SELECT ... ORDER BY embedding <=> :vec LIMIT 1
  └─ Si similarity >= threshold AND pattern != "healthy_*"
       → INSERT HealthAlert en Postgres
```

---

## Motor de análisis de comportamiento (pgvector)

El `BehaviorWorker` implementa un pipeline de detección de anomalías basado en similitud vectorial:

### 1. Extracción de features

Cada ventana de 30 lecturas de acelerómetro se convierte en un vector de 128 dimensiones con:
- **Media, desviación estándar, mínimo, máximo, RMS** por eje (X, Y, Z) → 15 features
- **Top-3 picos de magnitud FFT** por eje → 9 features
- Zero-padding hasta la dimensión configurada

### 2. Búsqueda por similitud coseno

```sql
SELECT label, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM behavior_patterns
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 1;
```

### 3. Patrones de referencia disponibles

| Label | Descripción |
|---|---|
| `healthy_grazing` | Pastoreo normal |
| `healthy_resting` | Descanso normal |
| `healthy_walking` | Caminata normal |
| `pre_calving` | Agitación preparto |
| `illness_lethargy` | Letargo por enfermedad |
| `lameness` | Cojera (patrón asimétrico) |

Los patrones se cargan con `python scripts/seed_patterns.py`. En producción se reemplazarían con vectores derivados de datos reales etiquetados.

---

## Próximos pasos

- [ ] Autenticación JWT (login de operadores con `/auth/token`)
- [ ] Geofencing real: verificar si el GPS del animal está fuera del polígono del lote
- [ ] Alembic para migraciones de Postgres en producción
- [ ] WebSocket para notificaciones de alertas en tiempo real al frontend
- [ ] Rate limiting en `/ingest` para proteger contra ESP32 mal configurados
- [ ] Tests de integración con base de datos en memoria (pytest + testcontainers)

---

## Stack tecnológico

| Tecnología | Versión | Rol |
|---|---|---|
| Python | 3.12 | Lenguaje |
| FastAPI | 0.115 | Framework web async |
| SQLAlchemy | 2.0 | ORM async para Postgres |
| asyncpg | 0.29 | Driver async de Postgres |
| pgvector | 0.3 | Extensión + Python binding |
| Motor | 3.6 | Driver async de MongoDB |
| Pydantic v2 | 2.9 | Validación de esquemas |
| NumPy | 2.1 | Extracción de features |
| Docker | 24+ | Contenedores |
| PostgreSQL | 16 | Base de datos relacional |
| MongoDB | 7.0 | Base de datos de telemetría |
| Redis | 7.2 | Broker de tareas |
