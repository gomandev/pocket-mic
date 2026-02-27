-- POCKETMIC CORE SCHEMA
-- Version: 1.0.0

-- 1. Jobs Table (Project Persistence)
do $$ begin
    if not exists (select 1 from pg_type where typname = 'job_status') then
        create type job_status as enum ('QUEUED', 'ANALYZING', 'DESIGNING', 'ARRANGING', 'COMPLETED', 'FAILED');
    end if;
end $$;

create table if not exists public.jobs (
    id uuid primary key default gen_random_uuid(),
    status job_status not null default 'QUEUED',
    progress integer default 0,
    audio_url text, -- Public URL to the raw vocal take
    result_plan jsonb, -- The Agent Pipeline's sonic blueprint
    error text,
    name text, -- Session Name (e.g. "Studio Session 01")
    version integer default 1, -- Project state version
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Storage Buckets & Policies (MANDATORY FOR UPLOADS)
-- Note: Create the 'audio-assets' bucket in the UI first, or use the SQL below.

-- Allow public access to the 'audio-assets' bucket
insert into storage.buckets (id, name, public) 
values ('audio-assets', 'audio-assets', true)
on conflict (id) do nothing;

-- Policy: Allow anyone to UPLOAD files to the 'audio-assets' bucket
create policy "Allow Public Uploads"
on storage.objects for insert
with check ( bucket_id = 'audio-assets' );

-- Policy: Allow anyone to VIEW files in the 'audio-assets' bucket (needed for publicUrl)
create policy "Allow Public Viewing"
on storage.objects for select
using ( bucket_id = 'audio-assets' );

-- 3. Security (Jobs Table)
alter table public.jobs enable row level security;
drop policy if exists "Public access" on public.jobs;
create policy "Public access" on public.jobs for all using (true) with check (true);
