from types import SimpleNamespace

from src.policy.policy_evaluator import (
    choose_highest_priority_decision,
    policy_matches,
)


def test_blocked_decision_overrides_use_with_caution():
    decisions = [
        {
            "asset_name": "marts.mart_zone_revenue",
            "policy_name": "degraded_metric_requires_caution",
            "decision": "USE_WITH_CAUTION",
        },
        {
            "asset_name": "marts.mart_zone_revenue",
            "policy_name": "critical_upstream_incident_blocks_metric",
            "decision": "BLOCKED",
        },
    ]

    selected = choose_highest_priority_decision(decisions)

    assert selected["decision"] == "BLOCKED"
    assert selected["policy_name"] == "critical_upstream_incident_blocks_metric"


def test_no_matching_decisions_returns_none():
    selected = choose_highest_priority_decision([])

    assert selected is None


def test_policy_matches_exact_rule_values():
    asset = SimpleNamespace(
        trust_label="DEGRADED",
        highest_open_severity="CRITICAL",
    )

    policy = {
        "rules": {
            "trust_label": "DEGRADED",
            "highest_open_severity": "CRITICAL",
        }
    }

    assert policy_matches(asset, policy) is True


def test_policy_does_not_match_when_rule_value_differs():
    asset = SimpleNamespace(
        trust_label="DEGRADED",
        highest_open_severity="CRITICAL",
    )

    policy = {
        "rules": {
            "trust_label": "DEGRADED",
            "highest_open_severity": "MEDIUM",
        }
    }

    assert policy_matches(asset, policy) is False