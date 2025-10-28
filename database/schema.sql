-- PM Service Database Schema for Supabase
-- Complete schema for chat instances, messages, email drafts, and action plans

-- Enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Table 1: chat_instances
-- Stores chat conversation metadata
CREATE TABLE chat_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('Lease & Contracts', 'Maintenance & Repairs', 'Tenant Communications')),
    workflow_phase TEXT DEFAULT 'assessment',
    user_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for faster category filtering and sorting
CREATE INDEX idx_chat_instances_category ON chat_instances(category);
CREATE INDEX idx_chat_instances_created_at ON chat_instances(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_instances_user_id ON chat_instances(user_id);

-- Table 2: chat_messages
-- Stores individual messages within chats
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chat_instances(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster message retrieval by chat
CREATE INDEX idx_chat_messages_chat_id ON chat_messages(chat_id, created_at);

-- Table 3: email_drafts
-- Stores generated email drafts
CREATE TABLE email_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chat_instances(id) ON DELETE CASCADE,
    subject TEXT,
    recipient TEXT,
    body TEXT NOT NULL,
    metadata JSONB, -- Store additional email metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for retrieving drafts by chat
CREATE INDEX idx_email_drafts_chat_id ON email_drafts(chat_id, created_at DESC);

-- Table 4: action_plans
-- Stores generated action plans
CREATE TABLE action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chat_instances(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    checklist JSONB NOT NULL, -- Store checklist items as JSON array
    key_considerations JSONB, -- Store key points as JSON array
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for retrieving plans by chat
CREATE INDEX idx_action_plans_chat_id ON action_plans(chat_id, created_at DESC);

-- Table 5: telemetry_events
-- Stores AI interaction telemetry data for analytics
CREATE TABLE telemetry_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chat_instances(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('Lease & Contracts', 'Maintenance & Repairs', 'Tenant Communications')),
    ai_mode TEXT NOT NULL CHECK (ai_mode IN ('💬 Chat', '✉️ Draft', '📋 Plan', '❓ Ask')),
    latency_ms DECIMAL(10,2) NOT NULL,
    tokens_used INTEGER NOT NULL,
    estimated_cost_usd DECIMAL(10,6) NOT NULL,
    model_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'error')),
    error_message TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient telemetry querying
CREATE INDEX idx_telemetry_events_chat_id ON telemetry_events(chat_id, timestamp DESC);
CREATE INDEX idx_telemetry_events_timestamp ON telemetry_events(timestamp DESC);
CREATE INDEX idx_telemetry_events_category ON telemetry_events(category);
CREATE INDEX idx_telemetry_events_ai_mode ON telemetry_events(ai_mode);
CREATE INDEX idx_telemetry_events_status ON telemetry_events(status);

-- Row Level Security (RLS) Policies
-- Enable RLS for multi-user support (strict policies)

-- Enable RLS on all tables
ALTER TABLE chat_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry_events ENABLE ROW LEVEL SECURITY;

-- Clean any existing policies
DROP POLICY IF EXISTS "ci_select_phase1" ON chat_instances;
DROP POLICY IF EXISTS "ci_modify_phase1" ON chat_instances;
DROP POLICY IF EXISTS "ci_delete_phase1" ON chat_instances;
DROP POLICY IF EXISTS "ci_insert" ON chat_instances;
DROP POLICY IF EXISTS "cm_access" ON chat_messages;
DROP POLICY IF EXISTS "ed_access" ON email_drafts;
DROP POLICY IF EXISTS "ap_access" ON action_plans;
DROP POLICY IF EXISTS "te_access" ON telemetry_events;

-- Strict, user-owned access policies
CREATE POLICY "ci_select" ON chat_instances FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "ci_modify" ON chat_instances FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY "ci_delete" ON chat_instances FOR DELETE USING (user_id = auth.uid());
CREATE POLICY "ci_insert" ON chat_instances FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "cm_access" ON chat_messages
FOR ALL USING (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = chat_messages.chat_id AND ci.user_id = auth.uid()
)) WITH CHECK (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = chat_messages.chat_id AND ci.user_id = auth.uid()
));

CREATE POLICY "ed_access" ON email_drafts
FOR ALL USING (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = email_drafts.chat_id AND ci.user_id = auth.uid()
)) WITH CHECK (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = email_drafts.chat_id AND ci.user_id = auth.uid()
));

CREATE POLICY "ap_access" ON action_plans
FOR ALL USING (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = action_plans.chat_id AND ci.user_id = auth.uid()
)) WITH CHECK (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = action_plans.chat_id AND ci.user_id = auth.uid()
));

CREATE POLICY "te_access" ON telemetry_events
FOR ALL USING (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = telemetry_events.chat_id AND ci.user_id = auth.uid()
)) WITH CHECK (EXISTS (
  SELECT 1 FROM chat_instances ci WHERE ci.id = telemetry_events.chat_id AND ci.user_id = auth.uid()
));

-- Functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at timestamp
CREATE TRIGGER update_chat_instances_updated_at 
    BEFORE UPDATE ON chat_instances 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing (optional)
-- Uncomment the following lines to add sample data

/*
-- Sample chat instance
INSERT INTO chat_instances (id, name, category, workflow_phase) VALUES 
('550e8400-e29b-41d4-a716-446655440000', 'Lease Review Discussion', 'Lease & Contracts', 'assessment');

-- Sample messages
INSERT INTO chat_messages (chat_id, role, content) VALUES 
('550e8400-e29b-41d4-a716-446655440000', 'user', 'I need help reviewing this lease agreement'),
('550e8400-e29b-41d4-a716-446655440000', 'assistant', 'I''d be happy to help you review the lease agreement. Could you please share the document or specific sections you''d like me to analyze?');

-- Sample email draft
INSERT INTO email_drafts (chat_id, subject, recipient, body, metadata) VALUES 
('550e8400-e29b-41d4-a716-446655440000', 'Lease Agreement Review Request', 'tenant@example.com', 'Dear [Tenant Name],\n\nI hope this message finds you well. I am writing to discuss the lease agreement review...', '{"priority": "normal", "type": "lease_review"}');

-- Sample action plan
INSERT INTO action_plans (chat_id, title, checklist, key_considerations) VALUES 
('550e8400-e29b-41d4-a716-446655440000', 'Lease Agreement Review Process', 
 '["Review lease terms and conditions", "Identify potential issues", "Prepare summary report", "Schedule follow-up meeting"]',
 '["Ensure compliance with local laws", "Check for any unusual clauses", "Verify rent escalation terms"]');
*/
