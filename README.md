# bigquery-data-quality-framework

After dealing with bad data too many times at work (wrong nulls, silent duplicates, columns that changed type overnight) I built this configurable framework to automate quality checks on BigQuery tables. Define your rules in YAML, point it at a table, and get a report.

No platform to install, no UI to learn. It's a script that runs checks and tells you what's broken.

## The checks

* `null_check` - flags columns where the null ratio goes over your threshold
* `duplicate_check` - counts duplicate rows on whatever key columns you pick
* `range_check` - counts values outside a min/max window
* `schema_check` - compares the live schema against what you expect, catches type drift and missing columns, warns about surprise columns
* `freshness_check` - fails if the table hasn't been updated in X hours (uses table metadata, so this one costs nothing to run)

Each check returns PASS, FAIL, WARN or SKIP with a one-line explanation. Errors in one check don't kill the run.

## Configuring rules.yaml

One entry per table, and you only configure the checks you want. Anything you leave out simply doesn't run.

```yaml
tables:
  - name: myproject.mydataset.my_table
    checks:
      null_check:
        columns: [customer_id, transaction_date]
        threshold: 0.01          # fail if more than 1% nulls
      duplicate_check:
        key_columns: [transaction_id]
      range_check:
        - column: amount
          min: 0
          max: 1000000
      freshness_check:
        max_hours_since_update: 24
      schema_check:
        expected_columns:
          - name: transaction_id
            type: STRING
          - name: amount
            type: FLOAT64
```

Add more tables to the list and they all run in one go.

## Running it

```bash
git clone https://github.com/hemanthrajmecs-lab/bigquery-data-quality-framework.git
cd bigquery-data-quality-framework

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# auth, if you haven't already
gcloud auth application-default login

python runner.py
# or point it at a different config / output dir
python runner.py --config config/rules.yaml --out reports/
```

The exit code is 1 if anything failed, so you can drop it straight into cron or CI and get failures for free.

Docker works too:

```bash
docker build -t dq-checks .
docker run -v ~/.config/gcloud:/root/.config/gcloud dq-checks
```

## What the output looks like

Console:

```
PASS   myproject.mydataset.my_table  null_check [customer_id]      5/1000 nulls (0.50%), threshold 1.00%
FAIL   myproject.mydataset.my_table  null_check [transaction_date] 30/1000 nulls (3.00%), threshold 1.00%
FAIL   myproject.mydataset.my_table  duplicate_check [transaction_id]  3 duplicate rows on key (transaction_id)
PASS   myproject.mydataset.my_table  range_check [amount]          0/1000 rows outside min 0, max 1000000
FAIL   myproject.mydataset.my_table  freshness_check               last updated 30.0h ago, limit is 24h
FAIL   myproject.mydataset.my_table  schema_check [amount]         type drift: expected FLOAT64, table has NUMERIC
WARN   myproject.mydataset.my_table  schema_check [extra_col]      columns present in table but not in expected schema
```

It also writes `report.html` (a color-coded table you can open in a browser or attach to an email) and `report.json` (for anything downstream that wants to consume results programmatically).

## Alerts

If any check fails and `SLACK_WEBHOOK_URL` is set, you get a Slack message listing exactly what broke. No webhook configured? It prints to the console instead, which is what you want when running locally anyway. The webhook comes from an environment variable so nothing sensitive ever touches the repo.

```bash
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
python runner.py
```

## Cost note

`null_check`, `duplicate_check` and `range_check` scan the table, so on big tables mind your bytes. One thing I did to keep it cheap: the null check builds a single query with one COUNTIF per column instead of one query per column. `schema_check` and `freshness_check` only read table metadata and cost nothing.

## What I'd add next

* dbt test integration, so teams already on dbt can reuse these as generic tests
* A Cloud Scheduler + Cloud Run job setup for scheduled runs (the Dockerfile is already job-shaped for this)
* BigQuery audit log export, to track quality trends over time instead of point-in-time snapshots
