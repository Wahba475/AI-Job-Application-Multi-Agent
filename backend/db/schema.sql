-- ApplyAI — auth + run history schema (Supabase / Postgres)
-- Run this once in the Supabase SQL editor.
--
-- users: custom JWT auth (our own table, bcrypt password hashes — NOT Supabase
--        Auth). The JWT we issue carries the user id; every run/history row is
--        scoped to it.
-- runs:  one row per pipeline run = one history entry. Files (CVs, spreadsheet)
--        live in Supabase Storage; we store only their URLs here.

create table if not exists users (
    id            uuid primary key default gen_random_uuid(),
    email         text        not null unique,
    password_hash text        not null,   -- bcrypt; plaintext is NEVER stored
    name          text,
    created_at    timestamptz not null default now()
);

create index if not exists users_email_idx on users (lower(email));


create table if not exists runs (
    id             uuid primary key default gen_random_uuid(),

    -- identity / abuse-control
    user_id        uuid        not null references users(id) on delete cascade,
    client_ip      text,                    -- server-derived, hard rate-limit backstop
    created_at     timestamptz not null default now(),

    -- what the user searched for
    job_title      text        not null,
    location       text        not null,
    experience     text        not null,

    -- run summary
    status         text        not null default 'done',  -- 'done' | 'error'
    total_jobs     int         not null default 0,        -- jobs found before filtering
    approved_count int         not null default 0,        -- CVs actually delivered

    -- deliverables in Supabase Storage
    spreadsheet_url text,                                 -- the jobs.xlsx URL

    -- per-job results; each element also holds that job's tailored-CV URL:
    -- [{
    --   "title","company","location","type","apply_link",
    --   "ats_score": 75, "gaps": "Docker, AWS",
    --   "cv_filename": "CV_Company_Title.docx",
    --   "cv_url": "https://<proj>.supabase.co/storage/v1/object/sign/..."
    -- }, ...]
    jobs           jsonb       not null default '[]'::jsonb
);

-- History lookups: newest runs for one user.
create index if not exists runs_user_created_idx on runs (user_id, created_at desc);

-- Rate-limit backstop: count recent runs per IP.
create index if not exists runs_ip_created_idx on runs (client_ip, created_at desc);
