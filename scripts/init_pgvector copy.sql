-- This script runs automatically when the Postgres container starts for the first time.
-- It enables the pgvector extension so Vector columns work correctly.

CREATE EXTENSION IF NOT EXISTS vector;
