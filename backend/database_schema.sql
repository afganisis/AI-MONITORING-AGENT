-- ZeroELD AI Agent - Database Schema for Supabase
-- Run this in Supabase SQL Editor to create all tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Errors table
CREATE TABLE IF NOT EXISTS errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zeroeld_log_id VARCHAR(255),
    zeroeld_event_id VARCHAR(255),
    driver_id VARCHAR(255) NOT NULL,
    driver_name VARCHAR(255),
    company_id VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    error_key VARCHAR(100) NOT NULL,
    error_name VARCHAR(255) NOT NULL,
    error_message TEXT,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    metadata JSONB,
    discovered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    fixed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for errors table
CREATE INDEX IF NOT EXISTS idx_errors_zeroeld_log_id ON errors(zeroeld_log_id);
CREATE INDEX IF NOT EXISTS idx_errors_zeroeld_event_id ON errors(zeroeld_event_id);
CREATE INDEX IF NOT EXISTS idx_errors_driver_id ON errors(driver_id);
CREATE INDEX IF NOT EXISTS idx_errors_company_id ON errors(company_id);
CREATE INDEX IF NOT EXISTS idx_errors_error_key ON errors(error_key);
CREATE INDEX IF NOT EXISTS idx_errors_status ON errors(status);
CREATE INDEX IF NOT EXISTS idx_errors_discovered_at ON errors(discovered_at DESC);

-- Fixes table
CREATE TABLE IF NOT EXISTS fixes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_id UUID NOT NULL REFERENCES errors(id) ON DELETE CASCADE,
    strategy_name VARCHAR(100) NOT NULL,
    fix_description TEXT,
    api_calls JSONB,
    status VARCHAR(20) NOT NULL,
    result_message TEXT,
    execution_time_ms INTEGER,
    retries INTEGER NOT NULL DEFAULT 0,
    requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for fixes table
CREATE INDEX IF NOT EXISTS idx_fixes_error_id ON fixes(error_id);
CREATE INDEX IF NOT EXISTS idx_fixes_status ON fixes(status);
CREATE INDEX IF NOT EXISTS idx_fixes_created_at ON fixes(created_at DESC);

-- Agent config table
CREATE TABLE IF NOT EXISTS agent_config (
    id SERIAL PRIMARY KEY,
    state VARCHAR(20) NOT NULL,
    polling_interval_seconds INTEGER NOT NULL DEFAULT 300,
    max_concurrent_fixes INTEGER NOT NULL DEFAULT 1,
    require_approval BOOLEAN NOT NULL DEFAULT TRUE,
    dry_run_mode BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Insert default agent config
INSERT INTO agent_config (state, polling_interval_seconds, max_concurrent_fixes, require_approval, dry_run_mode)
VALUES ('stopped', 300, 1, TRUE, TRUE)
ON CONFLICT DO NOTHING;

-- Fix rules table
CREATE TABLE IF NOT EXISTS fix_rules (
    id SERIAL PRIMARY KEY,
    error_key VARCHAR(100) NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    auto_fix BOOLEAN NOT NULL DEFAULT FALSE,
    priority INTEGER NOT NULL DEFAULT 50,
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_delay_seconds INTEGER NOT NULL DEFAULT 300,
    safety_checks JSONB,
    fix_strategy VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for fix_rules
CREATE INDEX IF NOT EXISTS idx_fix_rules_error_key ON fix_rules(error_key);

-- Insert default fix rules for all error types
INSERT INTO fix_rules (error_key, enabled, auto_fix, priority, max_retries) VALUES
('sequentialIdBreak', TRUE, FALSE, 90, 3),
('odometerError', TRUE, FALSE, 85, 3),
('engineHoursAfterShutdown', TRUE, FALSE, 80, 3),
('noDataInOdometerOrEngineHours', TRUE, FALSE, 95, 3),
('locationError', TRUE, FALSE, 80, 3),
('locationChangedError', TRUE, FALSE, 75, 3),
('locationDidNotChangeWarning', TRUE, TRUE, 50, 3),
('drivingOriginWarning', TRUE, FALSE, 60, 3),
('incorrectStatusPlacementError', TRUE, FALSE, 85, 3),
('twoIdenticalStatusesError', TRUE, TRUE, 70, 3),
('missingIntermediateError', TRUE, FALSE, 75, 3),
('incorrectIntermediatePlacementError', TRUE, FALSE, 70, 3),
('diagnosticEvent', TRUE, TRUE, 40, 3),
('noPowerUpError', TRUE, TRUE, 50, 3),
('noShutdownError', TRUE, TRUE, 50, 3),
('speedHigherThanLimit', TRUE, FALSE, 60, 3),
('speedMuchHigherThanLimit', TRUE, FALSE, 80, 3),
('unidentifiedDriverEvent', TRUE, FALSE, 65, 3),
('eventIsNotDownloaded', TRUE, FALSE, 55, 3),
('eventHasManualLocation', TRUE, FALSE, 45, 3),
('excessiveLogInWarning', TRUE, FALSE, 40, 3),
('excessiveLogOutWarning', TRUE, FALSE, 40, 3),
('engineHoursWarning', TRUE, FALSE, 50, 3)
ON CONFLICT (error_key) DO NOTHING;

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    user_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for audit_log
CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON audit_log(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);

-- Active connections table (for WebSocket tracking)
CREATE TABLE IF NOT EXISTS active_connections (
    id SERIAL PRIMARY KEY,
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    client_type VARCHAR(50),
    connected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_ping TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for active_connections
CREATE INDEX IF NOT EXISTS idx_active_connections_connection_id ON active_connections(connection_id);

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to tables
CREATE TRIGGER update_errors_updated_at BEFORE UPDATE ON errors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fixes_updated_at BEFORE UPDATE ON fixes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_config_updated_at BEFORE UPDATE ON agent_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fix_rules_updated_at BEFORE UPDATE ON fix_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) - optional for security
-- Uncomment if you want to use Supabase Auth

-- ALTER TABLE errors ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE fixes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_config ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE fix_rules ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Create policies (example - adjust based on your auth needs)
-- CREATE POLICY "Allow authenticated users to read errors" ON errors FOR SELECT USING (auth.role() = 'authenticated');
-- CREATE POLICY "Allow service role full access to errors" ON errors FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Grant permissions to authenticated users
-- GRANT ALL ON errors TO authenticated;
-- GRANT ALL ON fixes TO authenticated;
-- GRANT ALL ON agent_config TO authenticated;
-- GRANT ALL ON fix_rules TO authenticated;
-- GRANT ALL ON audit_log TO authenticated;
-- GRANT ALL ON active_connections TO authenticated;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database schema created successfully!';
    RAISE NOTICE 'Tables created: errors, fixes, agent_config, fix_rules, audit_log, active_connections';
    RAISE NOTICE 'Default data inserted: 1 agent_config, 23 fix_rules';
END $$;
