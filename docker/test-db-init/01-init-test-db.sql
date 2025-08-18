-- ObservaStack Test Database Initialization
-- Creates tables for storing test execution results and metrics

-- Test executions table
CREATE TABLE IF NOT EXISTS test_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_suite VARCHAR(255) NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    duration_ms INTEGER,
    environment VARCHAR(100) NOT NULL DEFAULT 'test',
    git_commit VARCHAR(40),
    git_branch VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Test results table
CREATE TABLE IF NOT EXISTS test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES test_executions(id) ON DELETE CASCADE,
    test_case VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration_ms INTEGER NOT NULL,
    error_message TEXT,
    stack_trace TEXT,
    assertions_passed INTEGER DEFAULT 0,
    assertions_failed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Test metrics table
CREATE TABLE IF NOT EXISTS test_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES test_executions(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(50),
    metric_type VARCHAR(50) NOT NULL DEFAULT 'gauge',
    labels JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Performance benchmarks table
CREATE TABLE IF NOT EXISTS performance_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    baseline_value DECIMAL(15,6) NOT NULL,
    threshold_value DECIMAL(15,6) NOT NULL,
    threshold_type VARCHAR(20) NOT NULL DEFAULT 'max', -- max, min, avg
    environment VARCHAR(100) NOT NULL DEFAULT 'test',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(test_name, metric_name, environment)
);

-- Test artifacts table for storing test outputs
CREATE TABLE IF NOT EXISTS test_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES test_executions(id) ON DELETE CASCADE,
    artifact_type VARCHAR(100) NOT NULL, -- screenshot, log, report, coverage
    artifact_name VARCHAR(255) NOT NULL,
    artifact_path TEXT NOT NULL,
    artifact_size INTEGER,
    mime_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_test_executions_suite_status ON test_executions(test_suite, status);
CREATE INDEX IF NOT EXISTS idx_test_executions_start_time ON test_executions(start_time);
CREATE INDEX IF NOT EXISTS idx_test_results_execution_id ON test_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results(status);
CREATE INDEX IF NOT EXISTS idx_test_metrics_execution_id ON test_metrics(execution_id);
CREATE INDEX IF NOT EXISTS idx_test_metrics_name_timestamp ON test_metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_benchmarks_test_metric ON performance_benchmarks(test_name, metric_name);
CREATE INDEX IF NOT EXISTS idx_test_artifacts_execution_id ON test_artifacts(execution_id);

-- Insert sample performance benchmarks
INSERT INTO performance_benchmarks (test_name, metric_name, baseline_value, threshold_value, threshold_type, environment) VALUES
('frontend_load_test', 'response_time_p95', 500.0, 1000.0, 'max', 'test'),
('frontend_load_test', 'error_rate', 0.01, 0.05, 'max', 'test'),
('api_load_test', 'response_time_p95', 200.0, 500.0, 'max', 'test'),
('api_load_test', 'throughput_rps', 100.0, 50.0, 'min', 'test'),
('search_performance', 'search_latency_ms', 100.0, 300.0, 'max', 'test'),
('search_performance', 'search_accuracy', 0.95, 0.90, 'min', 'test')
ON CONFLICT (test_name, metric_name, environment) DO NOTHING;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_test_executions_updated_at 
    BEFORE UPDATE ON test_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_performance_benchmarks_updated_at 
    BEFORE UPDATE ON performance_benchmarks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for test execution summaries
CREATE OR REPLACE VIEW test_execution_summary AS
SELECT 
    te.id,
    te.test_suite,
    te.test_name,
    te.start_time,
    te.end_time,
    te.status,
    te.duration_ms,
    te.environment,
    COUNT(tr.id) as total_test_cases,
    COUNT(CASE WHEN tr.status = 'passed' THEN 1 END) as passed_cases,
    COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) as failed_cases,
    COUNT(CASE WHEN tr.status = 'skipped' THEN 1 END) as skipped_cases,
    AVG(tr.duration_ms) as avg_test_duration,
    SUM(tr.assertions_passed) as total_assertions_passed,
    SUM(tr.assertions_failed) as total_assertions_failed
FROM test_executions te
LEFT JOIN test_results tr ON te.id = tr.execution_id
GROUP BY te.id, te.test_suite, te.test_name, te.start_time, te.end_time, 
         te.status, te.duration_ms, te.environment;

-- Grant permissions to test user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO test_user;