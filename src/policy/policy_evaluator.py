import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


POLICY_FILE = Path("policies/metric_reliability.yml")

DECISION_PRIORITY = {
    "BLOCKED": 1,
    "USE_WITH_CAUTION": 2,
    "ALLOWED": 3,
}


def get_engine():
    load_dotenv()

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")

    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )


def load_policies():
    with POLICY_FILE.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)["policies"]


def fetch_governed_assets():
    engine = get_engine()

    query = text(
        """
        SELECT DISTINCT
            'marts.mart_zone_revenue' AS asset_name,
            'dbt_model' AS asset_type,
            trust_label,
            open_incident_count,
            highest_open_severity,
            data_reliability_status
        FROM marts.mart_zone_revenue;
        """
    )

    with engine.connect() as conn:
        return conn.execute(query).fetchall()


def policy_matches(asset, policy):
    rules = policy.get("rules", {})

    for field, expected_value in rules.items():
        actual_value = getattr(asset, field)

        if actual_value != expected_value:
            return False

    return True


def choose_highest_priority_decision(decisions):
    if not decisions:
        return None

    return sorted(
        decisions,
        key=lambda decision: DECISION_PRIORITY.get(decision["decision"], 99),
    )[0]


def evaluate_policies():
    policies = load_policies()
    assets = fetch_governed_assets()

    final_decisions = []

    for asset in assets:
        matching_decisions = []

        for policy in policies:
            if asset.asset_type != policy["applies_to_asset_type"]:
                continue

            if not policy_matches(asset, policy):
                continue

            matching_decisions.append(
                {
                    "asset_name": asset.asset_name,
                    "policy_name": policy["policy_name"],
                    "decision": policy["decision"],
                    "severity": policy["severity"],
                    "description": policy["description"],
                    "trust_label": asset.trust_label,
                    "highest_open_severity": asset.highest_open_severity,
                    "data_reliability_status": asset.data_reliability_status,
                }
            )

        selected_decision = choose_highest_priority_decision(matching_decisions)

        if selected_decision:
            final_decisions.append(selected_decision)

    return final_decisions