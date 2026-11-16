-- Metadata bootstraps new tables. Apply reviewed migrations for upgrades.
CREATE INDEX IF NOT EXISTS journey_batch_idx ON journeys (batch_id);
CREATE INDEX IF NOT EXISTS scenario_run_review_idx ON budget_scenarios (run_id,review_status);
