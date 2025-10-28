-- Full database wipe for app-owned objects (keeps auth schema/users).
-- Order: drop policies -> triggers/functions -> tables -> extensions (optional).

-- Disable RLS temporarily to ease dropping
ALTER TABLE IF EXISTS chat_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS email_drafts DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS action_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS telemetry_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chat_instances DISABLE ROW LEVEL SECURITY;

-- Drop policies if present
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'chat_instances') THEN
    DROP POLICY IF EXISTS "ci_select" ON chat_instances;
    DROP POLICY IF EXISTS "ci_modify" ON chat_instances;
    DROP POLICY IF EXISTS "ci_delete" ON chat_instances;
    DROP POLICY IF EXISTS "ci_insert" ON chat_instances;
    DROP POLICY IF EXISTS "ci_select_phase1" ON chat_instances;
    DROP POLICY IF EXISTS "ci_modify_phase1" ON chat_instances;
    DROP POLICY IF EXISTS "ci_delete_phase1" ON chat_instances;
  END IF;

  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'chat_messages') THEN
    DROP POLICY IF EXISTS "cm_access" ON chat_messages;
  END IF;

  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'email_drafts') THEN
    DROP POLICY IF EXISTS "ed_access" ON email_drafts;
  END IF;

  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'action_plans') THEN
    DROP POLICY IF EXISTS "ap_access" ON action_plans;
  END IF;

  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'telemetry_events') THEN
    DROP POLICY IF EXISTS "te_access" ON telemetry_events;
  END IF;
END
$$;

-- Drop triggers
DROP TRIGGER IF EXISTS update_chat_instances_updated_at ON chat_instances;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables (children first)
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS email_drafts CASCADE;
DROP TABLE IF EXISTS action_plans CASCADE;
DROP TABLE IF EXISTS telemetry_events CASCADE;
DROP TABLE IF EXISTS chat_instances CASCADE;

-- Optionally drop extension (keep if other apps depend on it)
-- DROP EXTENSION IF EXISTS pgcrypto;

-- Verify
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;


