import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


RUN_RESULTS_PATH = Path("dbt_project/target/run_results.json")
MANIFEST_PATH = Path("dbt_project/target/manifest.json")


SEVERITY_MAP = {
    "impossible_trip_timestamps": "CRITICAL",
    "negative_fare_amount": "HIGH",
    "pickup_outside_file_month": "MEDIUM",
}


INCIDENT_TYPE_MAP = {
    "impossible_trip_timestamps": "IMPOSSIBLE_TIMESTAMPS",
    "negative_fare_amount": "NEGATIVE_FARE_VALUES",
    "pickup_outside_file_month": "PICKUP_OUTSIDE_FILE_MONTH",
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


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run dbt test before reporting incidents.")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_test_name(test_node: dict) -> str:
    return test_node.get("name") or test_node.get("alias") or test_node.get("unique_id")


def get_asset_name(test_node: dict) -> str:
    depends_on = test_node.get("depends_on", {}).get("nodes", [])

    for node_id in depends_on:
        if node_id.startswith("model."):
            return node_id.split(".")[-1]

    return "unknown_asset"


def build_test_result_map():
    run_results = load_json(RUN_RESULTS_PATH)
    manifest = load_json(MANIFEST_PATH)

    all_known_incident_keys = set()
    failed_incidents = []

    for result in run_results.get("results", []):
        unique_id = result.get("unique_id")
        status = result.get("status")

        test_node = manifest.get("nodes", {}).get(unique_id, {})
        if test_node.get("resource_type") != "test":
            continue

        test_name = get_test_name(test_node)
        asset_name = get_asset_name(test_node)
        incident_key = f"{asset_name}:{test_name}"

        all_known_incident_keys.add(incident_key)

        if status not in {"fail", "error"}:
            continue

        severity = SEVERITY_MAP.get(test_name, "MEDIUM")
        incident_type = INCIDENT_TYPE_MAP.get(test_name, "DBT_TEST_FAILURE")
        failure_count = result.get("failures")

        violation_detail = (
            f"dbt test '{test_name}' failed for asset '{asset_name}' "
            f"with {failure_count} failing rows."
        )

        failed_incidents.append(
            {
                "incident_key": incident_key,
                "asset_name": asset_name,
                "incident_type": incident_type,
                "severity": severity,
                "test_name": test_name,
                "failure_count": failure_count,
                "violation_detail": violation_detail,
                "source_artifact": str(RUN_RESULTS_PATH),
            }
        )

    return all_known_incident_keys, failed_incidents


def save_incidents():
    all_known_incident_keys, failed_incidents = build_test_result_map()
    failed_keys = {incident["incident_key"] for incident in failed_incidents}

    engine = get_engine()

    with engine.begin() as conn:
        for incident in failed_incidents:
            conn.execute(
                text(
                    """
                    INSERT INTO governance.governance_incidents (
                        incident_key,
                        asset_name,
                        incident_type,
                        severity,
                        test_name,
                        failure_count,
                        violation_detail,
                        status,
                        source_artifact
                    )
                    VALUES (
                        :incident_key,
                        :asset_name,
                        :incident_type,
                        :severity,
                        :test_name,
                        :failure_count,
                        :violation_detail,
                        'OPEN',
                        :source_artifact
                    )
                    ON CONFLICT (incident_key, status)
                    DO UPDATE SET
                        last_seen_at = NOW(),
                        failure_count = EXCLUDED.failure_count,
                        violation_detail = EXCLUDED.violation_detail,
                        source_artifact = EXCLUDED.source_artifact;
                    """
                ),
                incident,
            )

        resolved_count = 0

        for incident_key in all_known_incident_keys:
            if incident_key in failed_keys:
                continue

            result = conn.execute(
                text(
                    """
                    UPDATE governance.governance_incidents
                    SET
                        status = 'RESOLVED',
                        resolved_at = NOW(),
                        last_seen_at = NOW()
                    WHERE incident_key = :incident_key
                      AND status = 'OPEN';
                    """
                ),
                {"incident_key": incident_key},
            )

            resolved_count += result.rowcount

    print(f"Governance incidents processed: {len(failed_incidents)}")
    print(f"Governance incidents resolved: {resolved_count}")

    for incident in failed_incidents:
        print(
            f"- {incident['severity']} | {incident['asset_name']} | "
            f"{incident['incident_type']} | failures={incident['failure_count']}"
        )


if __name__ == "__main__":
    save_incidents()