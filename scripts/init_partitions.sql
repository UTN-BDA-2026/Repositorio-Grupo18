-- Renombrar tabla original
ALTER TABLE users RENAME TO users_old;

-- Crear tabla particionada por LIST sobre country
CREATE TABLE users (
    id            UUID DEFAULT gen_random_uuid(),
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(255)  NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role          VARCHAR(50)   NOT NULL DEFAULT 'user',
    country       VARCHAR(100)  NOT NULL,
    is_active     BOOLEAN       DEFAULT TRUE,
    created_at    TIMESTAMPTZ   DEFAULT now(),
    PRIMARY KEY (id, country)   -- country debe estar en el PK para particionado
) PARTITION BY LIST (country);

-- Crear particiones por país
CREATE TABLE users_argentina  PARTITION OF users FOR VALUES IN ('Argentina');
CREATE TABLE users_brasil      PARTITION OF users FOR VALUES IN ('Brasil');
CREATE TABLE users_uruguay     PARTITION OF users FOR VALUES IN ('Uruguay');
CREATE TABLE users_chile       PARTITION OF users FOR VALUES IN ('Chile');
CREATE TABLE users_paraguay    PARTITION OF users FOR VALUES IN ('Paraguay');
CREATE TABLE users_bolivia     PARTITION OF users FOR VALUES IN ('Bolivia');

-- Partición por defecto para cualquier otro país
CREATE TABLE users_otros       PARTITION OF users DEFAULT;

-- Migrar datos de la tabla vieja
INSERT INTO users SELECT * FROM users_old;

-- Eliminar tabla vieja
DROP TABLE users_old;
