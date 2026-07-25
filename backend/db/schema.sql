-- ApplyAI — auth + run-history schema (Supabase / Postgres)
-- Run this in the Supabase SQL editor. Safe to re-run (idempotent).
--
-- users:   custom JWT auth (our own table, bcrypt hashes — NOT Supabase Auth).
-- history: one row per pipeline run. Generated CVs + the spreadsheet live in
--          Supabase Storage; we store their bucket/paths here. Per-job results
--          (score, gaps, tailored flag, CV storage path) live in the `jobs`
--          JSONB column.
--
-- `jobs` JSONB — array, one element per matched job:
--   [{
--     "title":       "Backend Engineer",
--     "company":     "Acme",
--     "location":    "Cairo, Egypt",
--     "type":        "Full-time",
--     "posted_at":   "2026-07-20",
--     "apply_link":  "https://…",
--     "ats_score":   72,
--     "gaps":        "Docker, AWS, Kubernetes",
--     "tailored":    true,               -- false = original-CV fallback
--     "cv_filename": "CV_Acme_Backend_Engineer.docx",
--     "cv_bucket":   "deliverables",
--     "cv_path":     "{user_id}/{run_id}/CV_Acme_Backend_Engineer.docx"
--   }, ...]

-- ── users ────────────────────────────────────────────────────────────────────
create table if not exists users (
    id            uuid primary key default gen_random_uuid(),
    email         text        not null unique,
    password      text        not null,   -- bcrypt hash; plaintext NEVER stored
    name          text,
    created_at    timestamptz not null default now()
);
create index if not exists users_email_idx on users (lower(email));

-- ── history ──────────────────────────────────────────────────────────────────
create table if not exists history (
    id                 uuid primary key default gen_random_uuid(),
    user_id            uuid        not null references users(id) on delete cascade,
    run_id             text,                                   -- job/run id from the API
    job_title          text        not null,
    location           text,
    experience         text,
    spreadsheet_bucket text,
    spreadsheet_path   text,
    jobs               jsonb       not null default '[]'::jsonb,
    created_at         timestamptz not null default now()
);

-- Bring an existing (older) history table up to the current shape.
alter table history add column if not exists run_id text;
alter table history add column if not exists jobs   jsonb not null default '[]'::jsonb;

create index if not exists history_user_created_idx on history (user_id, created_at desc);
create index if not exists history_run_idx          on history (run_id);
