# DataTrust OS Architecture

DataTrust OS is designed as a governance-aware analytics reliability system. Its purpose is not only to produce business metrics, but to determine whether those metrics are safe to use.

The system connects five ideas into one pipeline:

1. Data quality evidence
2. Trust scoring
3. Governance incidents
4. Lineage blast-radius analysis
5. Policy-based metric consumption decisions

---

## 1. System overview

At a high level, DataTrust OS follows this flow:

```text
Raw data
   ↓
dbt staging model
   ↓
dbt governance tests
   ↓
Trust scoring engine
   ↓
Governance incident layer
   ↓
Governance-aware business mart
   ↓
Lineage and blast-radius analysis
   ↓
Policy engine
   ↓
CLI and Streamlit command center
```

The central design decision is that business metrics should not be separated from their reliability context.

Instead of producing only:

```text
zone
date
trip_count
revenue
```

the system produces:

```text
zone
date
trip_count
revenue
trust_score
trust_label
open_incident_count
highest_open_severity
data_reliability_status
```

This allows analysts and stakeholders to see both the metric and the governance status attached to it.

---

## 2. Database schemas

DataTrust OS uses PostgreSQL with separate schemas for each layer of the system.

```sql
CREATE SCHEMA raw;
CREATE SCHEMA staging;
CREATE SCHEMA marts;
CREATE SCHEMA governance;
CREATE SCHEMA lineage;
```

### raw

The `raw` schema stores source data loaded from external files.

Current tables:

```text
raw.yellow_trips
raw.taxi_zone_lookup
```

`raw.yellow_trips` contains NYC TLC Yellow Taxi trip records loaded from Parquet.

`raw.taxi_zone_lookup` is a dbt seed that maps taxi location IDs to boroughs and zone names.

---

### staging

The `staging` schema contains cleaned and standardized dbt models.

Current model:

```text
staging.stg_yellow_trips
```

This model standardizes source fields, casts data types, derives `trip_id`, and prepares the dataset for testing and downstream marts.

---

### marts

The `marts` schema contains business-facing analytical outputs and governance observability marts.

Current models:

```text
marts.mart_zone_revenue
marts.fct_governance_incidents
```

`mart_zone_revenue` is a business mart enriched with governance context.

`fct_governance_incidents` makes incident data easier to query for dashboards and summaries.

---

### governance

The `governance` schema stores operational governance metadata.

Current objects:

```text
governance.trust_score_runs
governance.latest_trust_scores
governance.governance_incidents
```

`trust_score_runs` stores historical trust scoring results.

`latest_trust_scores` exposes the latest trust score per asset.

`governance_incidents` stores open and resolved governance incidents.

---

### lineage

The `lineage` schema stores asset dependency relationships.

Current object:

```text
lineage.asset_lineage
```

This table supports downstream blast-radius analysis.

Example lineage:

```text
raw.yellow_trips
        ↓
staging.stg_yellow_trips
        ↓
marts.mart_zone_revenue
```

---

## 3. Ingestion layer

The ingestion layer downloads and loads raw NYC Yellow Taxi data into PostgreSQL.

Current loader:

```text
src/ingestion/load_yellow_taxi.py
```

The loader:

1. Downloads the Yellow Taxi Parquet file
2. Saves it locally under `data/raw`
3. Reads the file into Python
4. Adds ingestion metadata
5. Loads records into `raw.yellow_trips`

Important ingestion metadata includes:

```text
_ingested_at
_source_file
_source_file_hash
```

These metadata fields make the raw table more auditable and support future lineage and reproducibility work.

---

## 4. dbt transformation layer

The dbt project is located in:

```text
dbt_project/
```

Important dbt folders:

```text
dbt_project/models/staging
dbt_project/models/marts
dbt_project/tests
dbt_project/macros
dbt_project/seeds
```

### Schema naming macro

A custom dbt macro ensures that models land in their intended PostgreSQL schemas instead of prefixed schemas such as `public_marts`.

File:

```text
dbt_project/macros/generate_schema_name.sql
```

Purpose:

```text
staging model → staging schema
mart model → marts schema
seed → raw schema
```

---

## 5. Staging model

Current staging model:

```text
dbt_project/models/staging/stg_yellow_trips.sql
```

The staging model creates:

```text
staging.stg_yellow_trips
```

It standardizes fields such as:

```text
trip_id
source_system
vendor_id
pickup_datetime
dropoff_datetime
pickup_date
pickup_location_id
dropoff_location_id
passenger_count
trip_distance
fare_amount
tip_amount
total_amount
payment_type
ratecode_id
source_file
source_file_hash
ingested_at
```

The staging layer is the main tested asset in the current project.

---

## 6. Governance tests

dbt tests are used as data quality evidence.

Current test categories include:

1. Basic field completeness
2. Accepted values
3. Negative fare detection
4. Impossible trip timestamp detection
5. Pickup date outside expected file month

Important custom tests:

```text
dbt_project/tests/negative_fare_amount.sql
dbt_project/tests/impossible_trip_timestamps.sql
dbt_project/tests/pickup_outside_file_month.sql
```

These tests intentionally fail on known data quality issues.

Current expected failures:

```text
negative_fare_amount: 25,049 rows
impossible_trip_timestamps: 3 rows
pickup_outside_file_month: 48 rows
```

This is intentional. The project demonstrates how the governance system responds when upstream data is not fully trustworthy.

---

## 7. Trust scoring engine

The trust scoring engine lives in:

```text
src/trust/scorer.py
```

It reads dbt run results from:

```text
dbt_project/target/run_results.json
```

The scorer calculates:

```text
tests_passed
tests_failed
tests_total
test_pass_rate
freshness_score
ownership_score
composite_trust_score
trust_label
```

The score is stored in:

```text
governance.trust_score_runs
```

Current example:

```text
tests_passed: 9
tests_failed: 3
tests_total: 12
test_pass_rate: 0.7500
composite_trust_score: 0.7250
trust_label: DEGRADED
```

The score is intentionally stored historically so the dashboard can show trends across runs.

---

## 8. Trust labels

The trust score maps to a trust label.

Current labels include:

```text
TRUSTED
DEGRADED
AT_RISK
```

In the current dataset, the Yellow Taxi staging model is marked:

```text
DEGRADED
```

because some governance tests fail.

The latest trust score is exposed through:

```text
governance.latest_trust_scores
```

This view selects the most recent trust score per asset.

---

## 9. Governance incident layer

The incident reporter lives in:

```text
src/policy/incident_reporter.py
```

It reads dbt test results and promotes failed tests into governance incidents.

Incidents are stored in:

```text
governance.governance_incidents
```

Each incident includes:

```text
incident_key
asset_name
incident_type
severity
test_name
failure_count
violation_detail
status
detected_at
last_seen_at
resolved_at
source_artifact
```

Current incident examples:

| Test | Incident Type | Severity |
|---|---|---|
| impossible_trip_timestamps | IMPOSSIBLE_TIMESTAMPS | CRITICAL |
| negative_fare_amount | NEGATIVE_FARE_VALUES | HIGH |
| pickup_outside_file_month | PICKUP_OUTSIDE_FILE_MONTH | MEDIUM |

---

## 10. Incident lifecycle

The incident reporter supports lifecycle behavior.

If a test is still failing:

```text
OPEN incident is updated
last_seen_at is refreshed
failure_count is updated
```

If a previously failing test no longer fails:

```text
OPEN incident is marked RESOLVED
resolved_at is populated
```

This prevents duplicate incidents and makes the governance layer operational instead of static.

Current status:

```text
3 OPEN incidents
0 RESOLVED incidents
```

---

## 11. Governance observability mart

The mart:

```text
marts.fct_governance_incidents
```

is created from:

```text
governance.governance_incidents
```

It adds analytical fields such as:

```text
incident_age_hours
is_resolved
severity_rank
```

This enables CLI summaries and dashboard reporting.

Example questions this mart supports:

- How many open incidents exist?
- Which severity levels are active?
- How long have incidents been open?
- Which assets are affected?

---

## 12. Governance-aware business mart

The main business mart is:

```text
marts.mart_zone_revenue
```

It aggregates revenue by:

```text
pickup_date
pickup_location_id
zone_name
borough
```

Business metrics include:

```text
trip_count
total_revenue
avg_fare
avg_trip_distance
```

Governance context includes:

```text
trust_score
trust_label
open_incident_count
highest_open_severity
data_reliability_status
```

The key architectural decision is that the mart itself carries reliability context.

This makes trust visible at the point of analytical consumption.

---

## 13. Data reliability status macro

Reliability status is generated through a reusable dbt macro:

```text
dbt_project/macros/data_reliability_status.sql
```

Current logic:

```text
TRUSTED:
trust_score >= 0.85 AND open_incident_count = 0

USE WITH CAUTION:
trust_score >= 0.65 OR open_incident_count <= 2 with no CRITICAL incident

DO NOT USE:
trust_score < 0.65 OR any open CRITICAL incident
```

In the current state:

```text
marts.mart_zone_revenue → DO NOT USE
```

because a CRITICAL upstream incident is open.

---

## 14. Lineage model

Lineage is stored in:

```text
lineage.asset_lineage
```

The table captures:

```text
parent_asset
parent_asset_type
child_asset
child_asset_type
relationship_type
created_at
```

Current lineage:

```text
raw.yellow_trips → staging.stg_yellow_trips
staging.stg_yellow_trips → marts.mart_zone_revenue
```

This supports recursive downstream traversal.

---

## 15. Blast-radius analysis

Blast-radius logic lives in:

```text
src/lineage/blast_radius.py
```

It uses a recursive SQL query to find all downstream assets affected by a given upstream asset.

Example command:

```bash
python -m src.cli blast-radius staging.stg_yellow_trips
```

Example output:

```text
marts.mart_zone_revenue
Trust: DEGRADED
Open Incidents: 3
Highest Severity: CRITICAL
Reliability Status: DO NOT USE
```

The purpose is to answer:

> If this upstream asset is degraded, what downstream metrics or reports are affected?

---

## 16. YAML policy engine

Policies are defined in:

```text
policies/metric_reliability.yml
```

Policy evaluation logic lives in:

```text
src/policy/policy_evaluator.py
```

Example policy:

```yaml
policies:
  - policy_name: critical_upstream_incident_blocks_metric
    description: "A metric mart should not be used when a critical unresolved upstream incident exists."
    applies_to_asset_type: dbt_model
    decision: BLOCKED
    severity: CRITICAL
    rules:
      highest_open_severity: CRITICAL
```

The policy engine evaluates governed assets and emits decisions.

Current policy decision:

```text
marts.mart_zone_revenue → BLOCKED
```

---

## 17. Policy precedence

The policy engine supports decision precedence.

Current precedence:

```text
BLOCKED > USE_WITH_CAUTION > ALLOWED
```

This prevents noisy outputs.

For example, if an asset is both degraded and affected by a critical incident, the system outputs:

```text
BLOCKED
```

instead of outputting both:

```text
BLOCKED
USE_WITH_CAUTION
```

This makes the policy decision easier for analysts and stakeholders to act on.

---

## 18. Incident briefs

Incident brief logic lives in:

```text
src/policy/incident_briefs.py
```

Briefs summarize:

```text
affected asset
trust score
trust label
policy status
open incidents
downstream affected assets
recommended action
```

Example command:

```bash
python -m src.cli incident-briefs
```

Example output:

```text
Governance Incident Brief

Asset: stg_yellow_trips
Trust Score: 0.7250 (DEGRADED)
Policy Status: DO NOT USE

Open Issues
- CRITICAL: IMPOSSIBLE_TIMESTAMPS (3 failing rows)
- HIGH: NEGATIVE_FARE_VALUES (25049 failing rows)
- MEDIUM: PICKUP_OUTSIDE_FILE_MONTH (48 failing rows)

Affected Downstream Assets
- marts.mart_zone_revenue | DO NOT USE | 3 open incidents

Recommended Action
Investigate critical and high-severity upstream data quality failures before using dependent business metrics.
```

The current brief is deterministic and rule-generated. A future enhancement could add LLM-assisted natural language summaries.

---

## 19. CLI orchestration

The CLI is implemented in:

```text
src/cli.py
```

Main commands:

```bash
python -m src.cli trust-score
python -m src.cli incidents
python -m src.cli governance-summary
python -m src.cli zone-revenue
python -m src.cli blast-radius staging.stg_yellow_trips
python -m src.cli evaluate-policies
python -m src.cli incident-briefs
python -m src.cli run-pipeline
```

The most important command is:

```bash
python -m src.cli run-pipeline
```

It orchestrates:

```text
dbt run staging model
dbt test staging model
trust scoring
incident reporting
dbt run governance marts
policy evaluation
latest trust score rendering
```

The pipeline intentionally allows dbt tests to fail without stopping execution because failed tests are the evidence needed by the governance layer.

---

## 20. Streamlit command center

The dashboard is implemented in:

```text
app.py
```

It includes:

1. Executive risk banner
2. KPI cards
3. Incident severity distribution
4. Trust score history
5. Open incident table
6. Latest trust score table
7. Governance-aware revenue table
8. Visual lineage graph
9. Blast-radius table
10. Incident brief

The dashboard is designed to answer the governance questions quickly:

```text
Is the metric safe?
What is broken?
What downstream asset is impacted?
What is the policy decision?
What should happen next?
```

---

## 21. Current end-to-end behavior

The current system state is:

```text
Asset: staging.stg_yellow_trips
Trust score: 0.7250
Trust label: DEGRADED
Open incidents: 3
Highest severity: CRITICAL
Downstream impacted asset: marts.mart_zone_revenue
Policy decision: BLOCKED
Mart reliability status: DO NOT USE
```

This means the system correctly blocks the downstream revenue mart because critical upstream data quality failures remain unresolved.

---

## 22. Design principles

DataTrust OS follows these design principles:

### 1. Metrics should carry trust context

A metric should not be consumed without knowing whether its input data is reliable.

### 2. Test failures should become operational signals

dbt test failures are not only developer feedback. They can become incidents, policy triggers, and dashboard signals.

### 3. Governance should be close to analytics

Governance should not live only in documentation. It should be embedded in marts, CLI workflows, and dashboards.

### 4. Lineage should support decisions

Lineage is valuable when it can answer what is affected by an upstream issue.

### 5. Policies should make decisions explicit

Instead of relying on informal judgment, DataTrust OS defines when a metric is trusted, cautionary, or blocked.

---

## 23. Known limitations

Current limitations:

- Only Yellow Taxi data is currently loaded.
- Lineage is manually inserted rather than fully inferred from dbt metadata.
- Policy rules are simple equality-based rules.
- Incident recommendations are deterministic rather than LLM-generated.
- Dashboard is local and not deployment-ready yet.
- There are no automated unit tests for Python policy logic yet.
- Secrets and local PostgreSQL configuration are expected to be handled manually.

---

## 24. Future improvements

Planned improvements:

1. Add Green Taxi and FHV datasets
2. Add richer trust scoring dimensions
3. Add automated lineage extraction from dbt artifacts
4. Add policy rule operators such as less-than, greater-than, and contains
5. Add resolved incident demos
6. Add incident history and MTTR metrics
7. Add AI-assisted incident explanations
8. Add dashboard deployment instructions
9. Add Python unit tests
10. Add GitHub Actions for linting and test validation
11. Add a demo walkthrough document

---

## 25. Summary

DataTrust OS is not only an analytics project. It is a reliability and governance layer around analytics.

The project demonstrates how raw data quality evidence can flow through:

```text
tests → trust scores → incidents → lineage → policies → dashboard decisions
```

The result is a system that can answer:

> Should this business metric be trusted right now?

In the current state, the answer for the revenue mart is:

```text
No. The metric is blocked because a critical upstream data quality incident is unresolved.
```
