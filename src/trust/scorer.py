import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


RUN_RESULTS_PATH = Path("dbt_project/target/run_results.json")
MANIFEST_PATH = Path("dbt_project/target/manifest.json")
ASSET_NAME = "stg_yellow_trips"


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
        raise FileNotFoundError(f"Missing {path}. Run dbt test before scoring.")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_trust_label(score: float) -> str:
    if score >= 0.85:
        return "TRUSTED"
    if score >= 0.65:
        return "DEGRADED"
    return "AT_RISK"


def test_belongs_to_asset(test_node: dict, asset_name: str) -> bool:
    depends_on = test_node.get("depends_on", {}).get("nodes", [])

    for node_id in depends_on:
        if node_id.endswith(f".{asset_name}"):
            return True

    return False


def parse_test_results():
    run_results = load_json(RUN_RESULTS_PATH)
    manifest = load_json(MANIFEST_PATH)

    test_nodes_for_asset = set()

    for node_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") != "test":
            continue

        if test_belongs_to_asset(node, ASSET_NAME):
            test_nodes_for_asset.add(node_id)

    if not test_nodes_for_asset:
        raise ValueError(f"No dbt tests mapped to asset: {ASSET_NAME}")

    relevant_results = []

    for result in run_results.get("results", []):
        unique_id = result.get("unique_id")

        if unique_id in test_nodes_for_asset:
            relevant_results.append(result.get("status"))

    tests_total = len(relevant_results)
    tests_failed = sum(1 for status in relevant_results if status in {"fail", "error"})
    tests_passed = tests_total - tests_failed

    if tests_total == 0:
        raise ValueError(
            f"No run results found for tests mapped to asset: {ASSET_NAME}"
        )

    return tests_passed, tests_failed, tests_total


def calculate_score(tests_passed: int, tests_failed: int, tests_total: int):
    test_pass_rate = tests_passed / tests_total
    freshness_score = 1.0
    ownership_score = 0.0

    composite_score = (
        (test_pass_rate * 0.70)
        + (freshness_score * 0.20)
        + (ownership_score * 0.10)
    )

    return test_pass_rate, freshness_score, ownership_score, composite_score


def save_score():
    tests_passed, tests_failed, tests_total = parse_test_results()
    test_pass_rate, freshness_score, ownership_score, composite_score = calculate_score(
        tests_passed, tests_failed, tests_total
    )
    trust_label = get_trust_label(composite_score)

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO governance.trust_score_runs (
                    asset_name,
                    asset_type,
                    tests_passed,
                    tests_failed,
                    tests_total,
                    test_pass_rate,
                    freshness_score,
                    ownership_score,
                    composite_trust_score,
                    trust_label,
                    source_artifact
                )
                VALUES (
                    :asset_name,
                    'dbt_model',
                    :tests_passed,
                    :tests_failed,
                    :tests_total,
                    :test_pass_rate,
                    :freshness_score,
                    :ownership_score,
                    :composite_trust_score,
                    :trust_label,
                    :source_artifact
                );
                """
            ),
            {
                "asset_name": ASSET_NAME,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "tests_total": tests_total,
                "test_pass_rate": round(test_pass_rate, 4),
                "freshness_score": round(freshness_score, 4),
                "ownership_score": round(ownership_score, 4),
                "composite_trust_score": round(composite_score, 4),
                "trust_label": trust_label,
                "source_artifact": str(RUN_RESULTS_PATH),
            },
        )

    print("Trust score saved.")
    print(f"Asset: {ASSET_NAME}")
    print(f"Tests: {tests_passed} passed / {tests_failed} failed / {tests_total} total")
    print(f"Test pass rate: {test_pass_rate:.4f}")
    print(f"Composite trust score: {composite_score:.4f}")
    print(f"Trust label: {trust_label}")


if __name__ == "__main__":
    save_score()