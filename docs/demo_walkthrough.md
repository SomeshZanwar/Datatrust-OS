# DataTrust OS Demo Walkthrough

This walkthrough explains how to present DataTrust OS in a GitHub review, portfolio walkthrough, recruiter screen, or technical interview.

The goal is to show that this is not just a dbt project or a Streamlit dashboard. It is a governance-aware analytics reliability system that decides whether a business metric is safe to use.

---

## 1. One-sentence project explanation

Use this first:

> DataTrust OS is a governance-aware analytics reliability system that checks data quality, calculates trust scores, creates governance incidents, traces downstream blast radius, and blocks unsafe business metrics before analysts or stakeholders act on them.

A shorter version:

> It answers one question: should this business metric be trusted right now?

---

## 2. Problem statement

Most analytics projects stop at producing a metric.

Example:

```text
Revenue by pickup zone
Trips by day
Average fare
```

But business users usually do not know whether that metric is safe to use.

The upstream data may contain:

- negative fare amounts
- impossible timestamps
- records outside the expected reporting month
- failing dbt tests
- unresolved data quality incidents
- downstream marts affected by bad inputs

DataTrust OS adds a reliability and governance layer around analytics so business metrics are not consumed blindly.

---

## 3. Demo narrative

The demo should follow this story:

```text
Raw data enters the system.
dbt tests detect quality issues.
Those failures become governance incidents.
The trust scoring engine marks the asset as degraded.
Lineage shows which downstream business mart is affected.
The policy engine blocks unsafe metric usage.
The dashboard explains the status clearly.
```

The key phrase to repeat:

> The project does not only calculate metrics. It determines whether those metrics should be used.

---

## 4. Pre-demo checklist

Before presenting, make sure:

1. PostgreSQL is running.
2. The `.env` file exists.
3. The virtual environment is active.
4. dbt works with the local profile.
5. Streamlit dashboard loads.
6. The repo is clean.

Run:

```bash
git status
```

Expected:

```text
nothing to commit, working tree clean
```

Activate the virtual environment:

```bash
.venv\Scripts\activate
```

---

## 5. Start with the dashboard

Run:

```bash
streamlit run app.py
```

Open the local Streamlit URL.

Start on the **Command center** tab.

Explain:

> This is the governance command center. It shows that the current business metric is not safe to use because upstream data quality incidents are still open.

Point out:

- Governance Status: CRITICAL
- Metric Reliability: DEGRADED
- Governance Decision: DO NOT USE
- Open Incidents: 3
- Incident Severity Distribution
- Trust Score History

Use this explanation:

> The dashboard is not only showing metrics. It is showing whether the metric can be trusted.

---

## 6. Show the Command Center tab

On the **Command center** tab, explain each section:

### Executive risk banner

Say:

> This banner summarizes the current governance state. The revenue mart is blocked because a critical upstream incident is open.

### KPI cards

Explain:

- Metric Reliability shows the trust label.
- Governance Decision shows whether the metric can be used.
- Impacted Assets shows affected downstream assets.
- Open Incidents shows unresolved governance issues.

### Incident severity chart

Say:

> dbt test failures are being converted into operational incidents and classified by severity.

### Trust score history

Say:

> Trust scores are stored historically, so the system can show whether data reliability is improving or degrading over time.

---

## 7. Show the Revenue Reliability tab

Open the **Revenue reliability** tab.

Explain:

> This is the business mart. It contains normal analytical metrics like trip count and revenue, but also includes reliability context directly in the mart.

Point out columns such as:

```text
trust_label
open_incident_count
highest_open_severity
data_reliability_status
```

Say:

> The important design decision is that governance is embedded directly into the analytical output. Analysts do not need to check a separate system to know whether the metric is safe.

Current expected result:

```text
data_reliability_status = DO NOT USE
```

Explain:

> Because there is a critical upstream incident, revenue metrics are blocked from trusted consumption.

---

## 8. Show the Blast Radius tab

Open the **Blast radius** tab.

Explain:

> This view shows how upstream data quality issues propagate into downstream business assets.

Current lineage:

```text
raw.yellow_trips
        ↓
staging.stg_yellow_trips
        ↓
marts.mart_zone_revenue
```

Say:

> If staging.stg_yellow_trips is degraded, the system can identify that mart_zone_revenue is impacted.

This is an important governance capability because it answers:

```text
What business outputs are affected by this upstream issue?
```

---

## 9. Show the Incident Brief tab

Open the **Incident brief** tab.

Explain:

> This is a stakeholder-readable summary of the current governance issue.

Point out:

- affected asset
- trust score
- trust label
- policy decision
- open issues
- affected downstream assets
- recommended action

Say:

> The brief converts technical failures into decision-support language.

Current expected brief:

```text
Asset: stg_yellow_trips
Trust Score: 0.7250
Trust Label: DEGRADED
Policy Decision: DO NOT USE
Affected Downstream Asset: marts.mart_zone_revenue
```

---

## 10. CLI demo sequence

After the dashboard, show the CLI.

The CLI proves that the dashboard is backed by a real pipeline and not static mock data.

### Run the full pipeline

```bash
python -m src.cli run-pipeline
```

Explain:

> This runs dbt, captures test failures, updates trust scores, creates incidents, rebuilds marts, and evaluates policies.

Expected flow:

```text
dbt run
dbt test
trust scoring
incident reporting
mart rebuild
policy evaluation
latest trust score output
```

Important point:

> dbt tests are allowed to fail because the failures are evidence for the governance layer.

---

## 11. Show latest trust score

Run:

```bash
python -m src.cli trust-score
```

Expected:

```text
stg_yellow_trips | DEGRADED | 0.7250 | 9 passed / 3 failed / 12 total
```

Explain:

> The trust score is calculated from dbt test outcomes and stored historically.

---

## 12. Show open incidents

Run:

```bash
python -m src.cli incidents
```

Expected incidents:

```text
CRITICAL | IMPOSSIBLE_TIMESTAMPS
HIGH     | NEGATIVE_FARE_VALUES
MEDIUM   | PICKUP_OUTSIDE_FILE_MONTH
```

Explain:

> Failed governance tests become first-class incidents with severity, status, timestamps, and failure counts.

---

## 13. Show governance summary

Run:

```bash
python -m src.cli governance-summary
```

Explain:

> This gives a quick operational health summary of the governance layer.

Expected:

```text
Open incidents: 3
Affected assets: 1
Average open age: ...
```

---

## 14. Show governance-aware revenue mart

Run:

```bash
python -m src.cli zone-revenue
```

Explain:

> This is the business metric output, but it includes governance context.

Expected columns:

```text
Date
Zone
Borough
Trips
Revenue
Trust
Incidents
Severity
Status
```

Expected status:

```text
DO NOT USE
```

Say:

> The mart is not just reporting revenue. It is warning the analyst that the revenue metric should not be trusted yet.

---

## 15. Show blast-radius CLI

Run:

```bash
python -m src.cli blast-radius staging.stg_yellow_trips
```

Expected:

```text
marts.mart_zone_revenue | DEGRADED | 3 incidents | CRITICAL | DO NOT USE
```

Explain:

> This tells us which downstream business assets are impacted by a degraded upstream asset.

---

## 16. Show policy evaluation

Run:

```bash
python -m src.cli evaluate-policies
```

Expected:

```text
Asset: marts.mart_zone_revenue
Policy: critical_upstream_incident_blocks_metric
Decision: BLOCKED
Severity: CRITICAL
```

Explain:

> The YAML policy engine turns governance signals into explicit consumption decisions.

Important phrase:

> Because a critical upstream incident exists, the metric is blocked instead of merely marked as cautionary.

---

## 17. Show incident brief CLI

Run:

```bash
python -m src.cli incident-briefs
```

Expected:

```text
Governance Incident Brief

Asset: stg_yellow_trips
Trust Score: 0.7250 (DEGRADED)
Policy Status: DO NOT USE

Open Issues
- CRITICAL: IMPOSSIBLE_TIMESTAMPS
- HIGH: NEGATIVE_FARE_VALUES
- MEDIUM: PICKUP_OUTSIDE_FILE_MONTH

Affected Downstream Assets
- marts.mart_zone_revenue | DO NOT USE | 3 open incidents
```

Explain:

> This converts technical test failures into a stakeholder-readable governance explanation.

---

## 18. Architecture explanation for interviews

Use this explanation:

> I designed DataTrust OS as a layered analytics reliability system. Raw data is loaded into PostgreSQL, dbt creates a staging model, dbt tests generate data quality evidence, a Python trust scorer converts those results into a trust score, an incident reporter promotes failures into governance incidents, lineage identifies downstream impact, and a YAML policy engine decides whether business metrics should be trusted, used with caution, or blocked.

Then add:

> The dashboard and CLI are just two interfaces over the same governance metadata.

---

## 19. What makes this project different

Use these points in interviews:

### 1. Governance is embedded into marts

Most projects produce metrics. This project produces metrics with trust context attached.

### 2. dbt tests become operational signals

Test failures are not only pass/fail outputs. They become incidents, trust scores, policy decisions, and dashboard alerts.

### 3. Lineage is used for impact analysis

The system does not only say that data is bad. It shows which downstream business assets are affected.

### 4. Policies make metric consumption explicit

Instead of relying on informal judgment, the system decides:

```text
TRUSTED
USE WITH CAUTION
DO NOT USE
BLOCKED
```

### 5. Dashboard is decision-oriented

The dashboard answers:

```text
Is the metric safe?
What is broken?
What is affected?
What should happen next?
```

---

## 20. How to explain the failing data

Do not apologize for failing tests.

Say:

> The failing tests are intentional because the purpose of the project is to demonstrate how governance systems respond when real data has quality issues.

Then explain:

> If everything passed, there would be no incident lifecycle, blast radius, or policy blocking behavior to demonstrate.

This turns the failures into a strength of the project.

---

## 21. Recommended live demo order

Use this sequence:

```text
1. Show README
2. Open dashboard
3. Explain executive risk banner
4. Show revenue reliability tab
5. Show blast radius tab
6. Show incident brief tab
7. Run python -m src.cli run-pipeline
8. Run evaluate-policies
9. Run incident-briefs
10. Explain architecture.md
```

This order works well because it starts with visual impact and then proves there is working backend logic.

---

## 22. Short interview pitch

Use this when asked: "Tell me about this project."

> DataTrust OS is a governance-aware analytics reliability system. I built it to answer whether a business metric is safe to use. It loads NYC Taxi data into PostgreSQL, uses dbt for modeling and quality tests, converts failed tests into trust scores and governance incidents, traces downstream blast radius through lineage, and applies YAML policies to decide whether a metric should be trusted, used with caution, or blocked. I also built a Streamlit command center to show the current governance status, incident severity, trust trends, affected marts, and stakeholder-readable incident briefs.

---

## 23. Longer technical pitch

Use this when speaking to technical interviewers:

> The pipeline starts with raw Yellow Taxi data in PostgreSQL. dbt builds a staging model and runs both standard and custom data quality tests. I parse dbt's run_results.json to compute a trust score and persist it in a governance schema. Failed tests are promoted into governance incidents with severity levels and lifecycle fields like detected_at, last_seen_at, and resolved_at. A governance-aware mart joins business metrics with the latest trust score and open incident context. I store asset dependencies in a lineage table and use recursive SQL for blast-radius analysis. Finally, a YAML policy engine evaluates the metric and blocks it if a critical upstream incident exists. The CLI and Streamlit dashboard expose the same governance metadata in different ways.

---

## 24. Recruiter-friendly explanation

Use this when the listener is non-technical:

> I built a system that helps teams avoid using unreliable data. Instead of just showing revenue numbers, it checks whether the data behind those numbers has quality problems. If there are serious issues, it marks the metric as unsafe to use, shows what is broken, and explains which reports or business outputs are affected.

---

## 25. GitHub reviewer path

A reviewer should inspect files in this order:

```text
README.md
docs/architecture.md
app.py
src/cli.py
src/trust/scorer.py
src/policy/incident_reporter.py
src/policy/policy_evaluator.py
src/policy/incident_briefs.py
src/lineage/blast_radius.py
dbt_project/models/staging/stg_yellow_trips.sql
dbt_project/models/marts/mart_zone_revenue.sql
dbt_project/macros/data_reliability_status.sql
policies/metric_reliability.yml
```

This order shows the project from explanation to implementation.

---

## 26. Current project status to mention

Current completed capabilities:

- Raw ingestion
- dbt staging model
- dbt governance tests
- Trust scoring
- Incident lifecycle
- Governance-aware business mart
- Lineage and blast radius
- YAML policy engine
- Incident briefs
- Streamlit dashboard
- Trust history visualization
- Project README
- Architecture documentation

Current next steps:

- Add more datasets
- Add richer policy operators
- Add unit tests
- Add automated lineage extraction
- Improve deployment readiness
- Add resolved incident demos
- Add AI-assisted incident summaries

---

## 27. Closing demo line

End the demo with this:

> The main idea is that analytics should not stop at producing numbers. It should also tell people whether those numbers are reliable enough to act on.
