# DataTrust OS Roadmap

This roadmap describes the planned evolution of DataTrust OS from a local working MVP into a more complete governance-aware analytics reliability platform.

The project is already functional as a local MVP. The remaining roadmap focuses on deeper automation, stronger policy logic, more datasets, better testing, and deployment readiness.

---

## Current MVP status

DataTrust OS currently supports the full governance loop:

```text
Raw data
   ↓
dbt staging
   ↓
governance tests
   ↓
trust scoring
   ↓
incident lifecycle
   ↓
governance-aware marts
   ↓
lineage + blast radius
   ↓
policy evaluation
   ↓
CLI + Streamlit dashboard
```

Current system behavior:

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

The project already demonstrates the core idea:

> Business metrics should not be consumed without trust context.

---

## Completed capabilities

### Data ingestion

- Load NYC TLC Yellow Taxi data into PostgreSQL.
- Preserve source file metadata.
- Maintain a local raw data layer.

### dbt modeling

- Build a staging model for Yellow Taxi data.
- Build a governance-aware zone revenue mart.
- Load taxi zone lookup data as a dbt seed.
- Use a custom dbt schema naming macro.

### Data quality tests

- Validate required fields.
- Detect negative fare values.
- Detect impossible trip timestamps.
- Detect pickups outside the expected file month.
- Preserve known failing tests to demonstrate governance response behavior.

### Trust scoring

- Read dbt test results.
- Calculate pass rate and composite trust score.
- Store trust score runs historically.
- Expose latest trust score per asset.

### Incident management

- Promote failed tests into governance incidents.
- Assign incident severity.
- Track failure counts.
- Refresh `last_seen_at`.
- Support incident lifecycle fields such as `detected_at` and `resolved_at`.

### Governance-aware marts

- Attach trust score, trust label, open incident count, highest severity, and reliability status to business metrics.
- Make reliability visible at the point of analytical consumption.

### Lineage and blast-radius analysis

- Store asset lineage relationships.
- Use recursive SQL to find downstream impacted assets.
- Expose blast-radius output through CLI and dashboard.

### Policy engine

- Define metric reliability policies in YAML.
- Evaluate governed assets against policy rules.
- Apply precedence logic:
  - `BLOCKED`
  - `USE_WITH_CAUTION`
  - `ALLOWED`

### CLI

Current commands:

```bash
python -m src.cli run-pipeline
python -m src.cli trust-score
python -m src.cli incidents
python -m src.cli governance-summary
python -m src.cli zone-revenue
python -m src.cli blast-radius staging.stg_yellow_trips
python -m src.cli evaluate-policies
python -m src.cli incident-briefs
```

### Dashboard

The Streamlit command center currently includes:

- Executive risk banner
- KPI cards
- Incident severity distribution
- Trust score history
- Open incident table
- Latest trust score table
- Governance-aware revenue mart
- Visual lineage graph
- Blast-radius table
- Stakeholder-readable incident brief

### Documentation

Current documentation includes:

- `README.md`
- `docs/architecture.md`
- `docs/demo_walkthrough.md`
- dashboard screenshots

### Testing and CI

- Unit tests for policy evaluator logic.
- GitHub Actions workflow for Python tests.
- Passing CI badge in README.

---

## Roadmap overview

| Phase | Focus | Status |
|---|---|---|
| Phase 1 | Local governance MVP | Mostly complete |
| Phase 2 | Robust testing and cleanup | In progress |
| Phase 3 | More datasets and richer marts | Planned |
| Phase 4 | Automated lineage and richer policies | Planned |
| Phase 5 | AI-assisted governance summaries | Planned |
| Phase 6 | Deployment readiness | Planned |

---

## Phase 1: Local Governance MVP

**Status: Mostly complete**

Goal:

Build an end-to-end local system that can evaluate whether a business metric is safe to use.

Completed:

- Raw ingestion
- dbt staging
- dbt quality tests
- Trust scoring
- Governance incidents
- Incident lifecycle
- Governance-aware mart
- Lineage table
- Blast-radius CLI
- YAML policy engine
- Streamlit dashboard
- README and documentation

Remaining polish:

- Add more tests around incident logic.
- Add more tests around deterministic incident brief generation.
- Add dbt documentation generation notes.

---

## Phase 2: Robust testing and cleanup

**Status: In progress**

Goal:

Make the repository look more production-aware by adding tests, CI, and cleaner project structure.

Planned work:

### 1. Add incident reporter tests

Add tests for:

- new incident creation
- duplicate incident prevention
- `last_seen_at` update behavior
- resolved incident behavior

Potential file:

```text
tests/test_incident_reporter.py
```

### 2. Add incident brief tests

Add tests for:

- incident grouping
- downstream asset inclusion
- empty incident state
- policy status attachment

Potential file:

```text
tests/test_incident_briefs.py
```

### 3. Add blast-radius tests

Add tests for:

- recursive downstream traversal
- no downstream assets
- multiple downstream branches

Potential file:

```text
tests/test_blast_radius.py
```

### 4. Improve dependency separation

Potential future files:

```text
requirements.txt
requirements-dev.txt
```

This would separate runtime dependencies from development and test dependencies.

### 5. Add linting later

Potential tools:

- Ruff
- Black
- isort

Potential CI jobs:

```text
python-tests
python-lint
```

---

## Phase 3: Additional datasets and richer marts

**Status: Planned**

Goal:

Expand DataTrust OS beyond one dataset and one mart.

### 1. Add Green Taxi ingestion

Add:

```text
raw.green_trips
staging.stg_green_trips
```

Governance tests:

- negative fare amount
- impossible timestamps
- pickup outside expected file month
- null location IDs
- null fare values

### 2. Add FHV ingestion

Add:

```text
raw.fhv_trips
staging.stg_fhv_trips
```

Potential tests:

- missing dispatching base number
- invalid pickup location
- invalid dropoff location
- pickup outside expected file month

### 3. Add combined trip reliability mart

Potential mart:

```text
marts.mart_trip_volume_reliability
```

Possible metrics:

```text
pickup_date
service_type
trip_count
trusted_trip_count
degraded_trip_count
reliability_status
```

### 4. Add business-facing reliability comparison

Potential mart:

```text
marts.mart_asset_reliability_summary
```

Purpose:

Compare trust and incidents across assets.

Example:

| Asset | Trust Score | Label | Incidents | Status |
|---|---:|---|---:|---|
| stg_yellow_trips | 0.7250 | DEGRADED | 3 | DO NOT USE |
| stg_green_trips | 0.9200 | TRUSTED | 0 | TRUSTED |

---

## Phase 4: Automated lineage and richer policies

**Status: Planned**

Goal:

Reduce manual governance configuration and make the policy engine more expressive.

### 1. Automated dbt lineage extraction

Current lineage is manually inserted into:

```text
lineage.asset_lineage
```

Future improvement:

Parse dbt artifacts such as:

```text
manifest.json
run_results.json
```

Then automatically populate lineage relationships.

This would allow DataTrust OS to infer relationships such as:

```text
source → staging model → intermediate model → mart
```

### 2. Richer policy operators

Current policy matching supports exact equality.

Future policy operators:

```yaml
rules:
  trust_score:
    less_than: 0.65

  open_incident_count:
    greater_than: 0

  highest_open_severity:
    in: ["CRITICAL", "HIGH"]
```

Potential operators:

- `equals`
- `not_equals`
- `greater_than`
- `greater_than_or_equal`
- `less_than`
- `less_than_or_equal`
- `in`
- `not_in`

### 3. Asset-type-specific policies

Future policy examples:

```yaml
applies_to_asset_type: mart
applies_to_asset_type: source
applies_to_asset_type: dashboard
```

### 4. Policy explanation output

Policy engine should explain why a decision was made.

Example:

```text
Decision: BLOCKED
Reason: highest_open_severity = CRITICAL matched policy critical_upstream_incident_blocks_metric.
```

---

## Phase 5: AI-assisted governance summaries

**Status: Planned**

Goal:

Convert structured governance metadata into stakeholder-friendly summaries.

Current incident briefs are deterministic and rule-generated.

Future AI-assisted brief could summarize:

- what failed
- why it matters
- affected downstream assets
- recommended remediation
- suggested owner action

Example:

```text
The zone revenue mart should not be used because its upstream staging asset has a critical timestamp validity issue and a high-volume negative fare issue. These failures affect revenue reporting and may distort business performance analysis.
```

Potential implementation:

- Local deterministic template first
- Optional LLM provider later
- Ensure summaries are grounded only in stored governance metadata

Important design rule:

> AI summaries should explain governance evidence, not invent it.

---

## Phase 6: Deployment readiness

**Status: Planned**

Goal:

Make the project easier to run outside the local development machine.

### 1. Docker support

Potential files:

```text
Dockerfile
docker-compose.yml
```

Services:

```text
postgres
streamlit
```

### 2. Seed/demo data bootstrap

Add a setup script:

```bash
python scripts/bootstrap_demo.py
```

The script could:

- create schemas
- load raw data
- run dbt seed
- run dbt models
- run tests
- generate trust scores
- generate incidents
- rebuild marts

### 3. Streamlit deployment notes

Document:

- required environment variables
- database connection requirements
- local vs hosted limitations

### 4. Makefile or task runner

Potential commands:

```bash
make setup
make test
make dbt-run
make pipeline
make dashboard
```

Or Windows-friendly alternatives:

```text
scripts/run_pipeline.bat
scripts/run_dashboard.bat
```

---

## Future feature ideas

### 1. Trust score decomposition

Show exactly why a trust score was calculated.

Example:

```text
Test pass rate contribution: 0.75
Freshness contribution: 1.00
Ownership contribution: 0.00
Composite trust score: 0.725
```

### 2. Incident aging and SLA tracking

Add SLA logic:

```text
CRITICAL incident must be resolved within 24 hours
HIGH incident must be resolved within 72 hours
MEDIUM incident must be resolved within 7 days
```

Dashboard could show:

```text
SLA breached
SLA due soon
Within SLA
```

### 3. Ownership model

Add ownership metadata:

```text
asset_owner
team_name
slack_channel
email
```

Then route incidents to owners.

### 4. Governance event log

Track governance events:

```text
TRUST_SCORE_CREATED
INCIDENT_OPENED
INCIDENT_UPDATED
INCIDENT_RESOLVED
POLICY_BLOCKED_ASSET
POLICY_ALLOWED_ASSET
```

Potential table:

```text
governance.governance_events
```

### 5. Dataset freshness checks

Add freshness score based on:

```text
max(ingested_at)
expected_update_frequency
last_successful_pipeline_run
```

### 6. Data contract checks

Future data contracts could define:

```text
required columns
allowed types
allowed ranges
expected freshness
owner
consumer impact
```

### 7. Dashboard consumer registry

Track which dashboards consume each mart:

```text
marts.mart_zone_revenue → executive revenue dashboard
marts.mart_zone_revenue → operations dashboard
```

Then blast radius becomes more business-readable.

### 8. Remediation recommendations

Generate recommended actions by incident type.

Example:

| Incident Type | Recommendation |
|---|---|
| NEGATIVE_FARE_VALUES | Validate payment/refund handling and fare ingestion logic |
| IMPOSSIBLE_TIMESTAMPS | Check timestamp parsing and source record validity |
| PICKUP_OUTSIDE_FILE_MONTH | Validate file partitioning and source file selection |

---

## Intentionally out of scope for now

The following are intentionally not part of the current MVP:

- Enterprise authentication
- Role-based access control
- Real-time streaming
- Multi-tenant governance
- Production-grade alerting
- Automatic ticket creation
- Full data catalog replacement
- Full observability platform replacement

DataTrust OS is currently focused on proving the governance flow from data quality evidence to metric consumption decisions.

---

## Success criteria for the next major milestone

The next milestone should be considered complete when DataTrust OS can:

1. Run tests for more than one source dataset.
2. Score multiple governed assets.
3. Show multiple assets in the dashboard.
4. Automatically infer at least some lineage from dbt artifacts.
5. Evaluate policies with richer operators.
6. Include tests for policy, incidents, and blast-radius logic.
7. Provide a one-command demo bootstrap.

---

## Suggested next development order

Recommended order:

```text
1. Add incident reporter unit tests
2. Add blast-radius unit tests
3. Add Green Taxi ingestion and staging
4. Add trust scoring for multiple assets
5. Add dashboard multi-asset support
6. Add automated dbt lineage extraction
7. Add richer policy rule operators
8. Add Docker/demo bootstrap
```

This order keeps the project practical and avoids overbuilding before the current architecture is stable.

---

## Current positioning

DataTrust OS should be positioned as:

```text
A governance-aware analytics reliability system for deciding whether business metrics are safe to use.
```

Not as:

```text
just a dbt project
just a dashboard
just a data quality checker
```

The differentiator is the full chain:

```text
dbt evidence → trust score → incident → lineage impact → policy decision → dashboard explanation
```

That is the core product story to preserve as the project evolves.
