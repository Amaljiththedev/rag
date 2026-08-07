-- Base schema. This was previously created by hand against the local Docker
-- database and never captured in code, so a fresh environment had nothing to
-- ALTER and every query failed. Run this first on any new database.
--
-- Safe to run against the existing local database: every statement is guarded.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id              SERIAL PRIMARY KEY,
    chunk_id        TEXT NOT NULL UNIQUE,
    source_file     TEXT NOT NULL,
    company         TEXT,
    section         TEXT,
    chunk_index     INTEGER,
    content         TEXT NOT NULL,
    -- 384 dimensions must match the all-MiniLM-L6-v2 embedding model.
    embedding       VECTOR(384)
);
