# 🐄 SmartFarming API 

Backend para un sistema de monitoreo ganadero inteligente, inspirado en [Halter](https://www.halterhq.com/). Cada animal lleva un collar **ESP32** que transmite telemetría GPS + acelerómetro. El backend almacena, analiza y genera alertas en tiempo real usando una arquitectura **polígola** (PostgreSQL + MongoDB + pgvector).


## INTEGRANTES DEL GRUPO 18: 
* Bru Paulo
* Cano Juan
* Juarez Martin
* La Loggia Martín
* Méndez Jesús

---

## Tabla de contenidos

- [Modelos de datos](#modelos-de-datos)
- [Instalación local](#instalación-local)
- [Instalación con Docker](#instalación-con-docker)

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
users
  id (UUID PK),
  name, 
  email, 
  hashed_password,
  role: "admin" | "granjero" | "veterinario",
  country,
  is_active, 
  created_at

grounds
  id (UUID PK),
  name, geofence (GeoJSON string),
  area_hectares,
  users_id → users.id

animals
  id (UUID PK), 
  species,
  birth_date, 
  sex, 
  weight_kg,
  user_id → users.id
  is_active, created_at

devices (no implementado aún)
  id (UUID PK),
  hardware_id (MAC del ESP32, único),
  firmware_version,
  battery_pct,
  last_seen
  animal_id → livestock.id  (1-to-1),
  is_active, 
  created_at

grazing_sessions (no implementado aún)
  id (UUID PK),
  animal_id → livestock.id,
  lot_id    → grazing_lots.id,
  started_at, 
  ended_at (NULL = sesión abierta)

health_alerts (no implementado aún)
  id (UUID PK),
  animal_id   → livestock.id,
  alert_type: "behavior" | "geofence" | "battery" | "no_signal",
  pattern_label, 
  similarity_score,
  message, 
  resolved,
  created_at

behavior_patterns (no implementado aún)
  id (UUID PK),
  label, 
  description,
  embedding VECTOR(128)   ← pgvector,
  created_at
```

---

## Instalación local

### Prerrequisitos

- Python 3.12+
- PostgreSQL 16 con extensión `pgvector` instalada
- MongoDB 7.0+

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

# 5. Habilitar pgvector en tu Postgres local
psql -U postgres -d smartfarming -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 6. Cargar patrones de comportamiento de referencia
python scripts/seed_patterns.py

# 7. Levantar el servidor
uvicorn app.main:app --reload --port 8000
```

Las tablas de Postgres se crean automáticamente al iniciar la app.
---

## Instalación con Docker

Docker Compose levanta todos los servicios con un solo comando: la API, Postgres con pgvector.

### Requisitos

- Docker 24+
- Docker Compose v2+

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/smartfarming-api.git
cd smartfarming-api

# 2. Crear archivo de variables de entorno

# 3. Construir y levantar todos los servicios
docker compose up --build

# La API estará disponible en http://localhost:8000
```


