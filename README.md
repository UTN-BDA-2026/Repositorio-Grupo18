# 🐄 SmartFarming API 

Backend para un sistema de monitoreo ganadero inteligente, inspirado en [Halter](https://www.halterhq.com/). Cada animal lleva un collar **ESP32** que transmite telemetría GPS + acelerómetro. El backend almacena, analiza y genera alertas en tiempo real usando una arquitectura **polígola** (PostgreSQL + MongoDB + pgvector).


## INTEGRANTES DEL GRUPO 18: 
* Bru Paulo
* Cano Juan
* Juarez Martín
* La Loggia Martín
* Méndez Jesús

---

## Tabla de contenidos

- [Modelos de datos](#modelos-de-datos)
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

devices 
  id (UUID PK),
  hardware_id (MAC del ESP32, único),
  firmware_version,
  battery_pct,
  last_seen
  animal_id → livestock.id  (1-to-1),
  is_active, 
  created_at

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
## Instalación con Docker

Docker Compose levanta todos los servicios con un solo comando: la API, Postgres con pgvector.

### Requisitos

- Docker
- Docker Compose

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/UTN-BDA-2026/Repositorio-Grupo18.git
cd Repositorio-Grupo18

# 2. Crear archivo de variables de entorno

# 3. Construir y levantar todos los servicios
docker compose up --build

# La API estará disponible en http://localhost:8000

# 4. Cargar patrones de comportamiento de referencia
python scripts/seed_patterns.py

# 5. Cargar 1 millón de datos en las tablas de forma repartida
python scripts/simulation_data.py

# 5. Crear particiones
docker compose exec postgres psql -U postgres -d smartfarming \
  -f /scripts/init_partitions.sql

```

