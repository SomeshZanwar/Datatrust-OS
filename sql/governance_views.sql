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