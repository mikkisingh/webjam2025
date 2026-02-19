-- ============================================================
-- MediCheck — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New query
-- ============================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ============================================================
-- ANALYSES TABLE
-- Stores AI analysis OUTPUT only — no raw bill text / raw PHI
-- Raw files and extracted text are deleted immediately after
-- analysis (HIPAA Option A: process and forget)
-- ============================================================
create table if not exists analyses (
  id                uuid default uuid_generate_v4() primary key,
  user_id           uuid references auth.users(id) on delete cascade not null,
  created_at        timestamptz default now(),

  -- User-defined label (e.g. "Jan 2026 hospital bill")
  bill_nickname     text,
  file_type         text,

  -- Top-level analysis metadata
  overall_severity  text check (overall_severity in ('low', 'medium', 'high')),
  potential_savings numeric default 0,
  issues_count      integer default 0,

  -- Full AI analysis results (structured JSON)
  structured_data   jsonb,   -- patient info, charges, totals
  analysis_results  jsonb,   -- issues, recommendations
  summary           text,    -- plain-English summary
  complaint_email   text,    -- dispute email template

  -- Dispute tracking (updated by user)
  dispute_status    text default 'none'
    check (dispute_status in ('none', 'submitted', 'in_progress', 'resolved', 'rejected'))
);

-- Row Level Security: users can only access their own analyses
alter table analyses enable row level security;

create policy "Users can view their own analyses"
  on analyses for select
  using (auth.uid() = user_id);

create policy "Users can insert their own analyses"
  on analyses for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own analyses"
  on analyses for update
  using (auth.uid() = user_id);

create policy "Users can delete their own analyses"
  on analyses for delete
  using (auth.uid() = user_id);

-- ============================================================
-- DISPUTES TABLE (Phase 2 — dispute outcome tracker)
-- User manually logs dispute progress; no bill content stored
-- ============================================================
create table if not exists disputes (
  id               uuid default uuid_generate_v4() primary key,
  user_id          uuid references auth.users(id) on delete cascade not null,
  analysis_id      uuid references analyses(id) on delete cascade,
  created_at       timestamptz default now(),

  submitted_date   date,
  amount_disputed  numeric,
  resolved_amount  numeric,
  status           text default 'submitted'
    check (status in ('submitted', 'in_progress', 'resolved', 'rejected')),
  notes            text
);

alter table disputes enable row level security;

create policy "Users can manage their own disputes"
  on disputes for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ============================================================
-- PUBLIC STATS FUNCTION
-- Returns aggregate counts visible to anyone (no PII)
-- ============================================================
create or replace function get_public_stats()
returns json language sql security definer stable as $$
  select json_build_object(
    'total_analyses',          (select count(*) from public.analyses),
    'total_potential_savings', (select coalesce(sum(potential_savings), 0) from public.analyses)
  )
$$;
grant execute on function get_public_stats() to anon;

-- ============================================================
-- ADMIN STATS FUNCTION
-- Returns full portal statistics — admin role required.
-- Role is checked inside the function via auth.jwt() so that
-- the security guarantee is enforced at the database level.
-- ============================================================
create or replace function get_admin_stats()
returns json language plpgsql security definer stable as $$
declare
  caller_role text;
begin
  caller_role := coalesce((auth.jwt() -> 'app_metadata' ->> 'role'), '');
  if caller_role != 'admin' then
    raise exception 'Access denied: admin role required';
  end if;

  return (
    select json_build_object(
      'total_analyses',          (select count(*) from public.analyses),
      'active_users',            (select count(distinct user_id) from public.analyses),
      'total_potential_savings', (select coalesce(sum(potential_savings), 0) from public.analyses),
      'total_confirmed_savings', (select coalesce(sum(potential_savings), 0) from public.analyses where dispute_status = 'resolved'),
      'last_7_days',             (select count(*) from public.analyses where created_at >= now() - interval '7 days'),
      'last_30_days',            (select count(*) from public.analyses where created_at >= now() - interval '30 days'),
      'severity_breakdown',      (
        select json_object_agg(overall_severity, cnt)
        from (
          select overall_severity, count(*) as cnt
          from public.analyses
          where overall_severity is not null
          group by overall_severity
        ) s
      ),
      'dispute_breakdown',       (
        select json_object_agg(dispute_status, cnt)
        from (
          select dispute_status, count(*) as cnt
          from public.analyses
          group by dispute_status
        ) d
      )
    )
  );
end;
$$;
grant execute on function get_admin_stats() to authenticated;

-- ============================================================
-- PROFILES TABLE — credit balance and usage tracking
-- Backend (service_role) writes credits; frontend can only read.
-- ============================================================
create table if not exists profiles (
  user_id         uuid references auth.users(id) on delete cascade primary key,
  scan_credits    integer default 0 not null,
  free_scan_used  boolean default false not null,
  total_scans     integer default 0 not null,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

alter table profiles enable row level security;

create policy "Users can view their own profile"
  on profiles for select
  using (auth.uid() = user_id);

-- No INSERT/UPDATE/DELETE policies for authenticated role.
-- Only the backend service_role key (which bypasses RLS) can modify credits.

-- ============================================================
-- PURCHASES TABLE — Stripe transaction history
-- ============================================================
create table if not exists purchases (
  id                    uuid default uuid_generate_v4() primary key,
  user_id               uuid references auth.users(id) on delete cascade not null,
  stripe_session_id     text unique not null,
  stripe_payment_intent text,
  price_id              text not null,
  credits_purchased     integer not null,
  amount_cents          integer not null,
  status                text default 'completed' not null,
  created_at            timestamptz default now()
);

alter table purchases enable row level security;

create policy "Users can view their own purchases"
  on purchases for select
  using (auth.uid() = user_id);

-- ============================================================
-- AUTO-CREATE PROFILE ON SIGNUP
-- ============================================================
create or replace function handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (user_id)
  values (new.id)
  on conflict (user_id) do nothing;
  return new;
end;
$$;

-- Drop trigger if exists to make this idempotent
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- ============================================================
-- BACKFILL PROFILES FOR EXISTING USERS
-- ============================================================
insert into profiles (user_id)
select id from auth.users
on conflict (user_id) do nothing;

-- ============================================================
-- GRANT FIRST ADMIN
-- Run once in SQL Editor, replacing the email below.
-- After this, other admins can be promoted via the app UI.
-- ============================================================
-- UPDATE auth.users
-- SET raw_app_meta_data = raw_app_meta_data || '{"role": "admin"}'
-- WHERE email = 'your@email.com';
