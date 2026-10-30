-- V0.4.0 additive migration. Safe to run repeatedly on PostgreSQL.
ALTER TABLE events
    ADD COLUMN IF NOT EXISTS annotated_snapshot_url TEXT;
