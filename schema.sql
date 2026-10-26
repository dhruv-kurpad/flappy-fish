-- Fred the Fish / Project 3a — Supabase (Postgres)
--
-- Run in the Supabase dashboard: SQL Editor → New query → paste → Run.
-- flaskapp_pool.py reads SUPABASE_URL and SUPABASE_SECRET_KEY from the environment.

-- ---------------------------------------------------------------------------
-- Table: players
-- ---------------------------------------------------------------------------
create table if not exists public.players (
    id         bigint generated always as identity primary key,
    username   varchar(255) not null unique,
    password   varchar(255) not null,
    high_score integer      not null default 0
);

-- Leaderboard: ORDER BY high_score DESC
create index if not exists idx_players_high_score
    on public.players (high_score desc);
