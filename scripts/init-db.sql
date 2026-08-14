-- Extra schemas / tables for the LSAP application (Keycloak uses the same DB)
CREATE SCHEMA IF NOT EXISTS lsap;

CREATE TABLE IF NOT EXISTS lsap.jobs (
    id              UUID PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(255) NOT NULL,
    status          VARCHAR(50)  NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    target_name     VARCHAR(255) NOT NULL,
    target_config   JSONB       NOT NULL,
    tools_selected  TEXT[]      NOT NULL,
    options         JSONB       DEFAULT '{}',
    progress        JSONB       DEFAULT '{}',
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS lsap.results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES lsap.jobs(id) ON DELETE CASCADE,
    tool_name       VARCHAR(100) NOT NULL,
    status          VARCHAR(50)  NOT NULL,
    raw_path        TEXT,
    summary         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON lsap.jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON lsap.jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_results_job_id ON lsap.results(job_id);

-- Enable uuid-ossp if needed (Postgres 13+ has gen_random_uuid built-in)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
