CREATE OR REPLACE VIEW governance.latest_trust_scores AS
WITH ranked_scores AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY asset_name
            ORDER BY run_timestamp DESC, trust_score_run_id DESC
        ) AS score_rank
    FROM governance.trust_score_runs
)
SELECT
    asset_name,
    asset_type,
    run_timestamp,
    tests_passed,
    tests_failed,
    tests_total,
    test_pass_rate,
    freshness_score,
    ownership_score,
    composite_trust_score,
    trust_label,
    source_artifact
FROM ranked_scores
WHERE score_rank = 1;

CREATE TABLE IF NOT EXISTS governance.governance_incidents (
    incident_id SERIAL PRIMARY KEY,

    incident_key TEXT NOT NULL,
    asset_name TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    severity TEXT NOT NULL,

    test_name TEXT,
    failure_count INTEGER,
    violation_detail TEXT,

    status TEXT NOT NULL DEFAULT 'OPEN',
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    source_artifact TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_open_incident UNIQUE (incident_key, status)
);


CREATE TABLE IF NOT EXISTS lineage.asset_lineage (
    lineage_id SERIAL PRIMARY KEY,

    parent_asset TEXT NOT NULL,
    parent_asset_type TEXT NOT NULL,

    child_asset TEXT NOT NULL,
    child_asset_type TEXT NOT NULL,

    relationship_type TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);