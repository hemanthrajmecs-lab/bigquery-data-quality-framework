# Entry point. Loads rules.yaml, runs every configured check against every
# table, writes the report, and pings the alerter if anything failed.
#
#   python runner.py
#   python runner.py --config config/rules.yaml --out reports/

import argparse
import os
import sys

import yaml

from checks import REGISTRY
from reporter import report as reporter
from reporter.alerter import alert


def load_config(path):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    if not cfg or "tables" not in cfg:
        sys.exit(f"config {path} has no 'tables' section, nothing to do")
    return cfg


def get_client():
    # imported here so you can run --help or unit tests without
    # google-cloud-bigquery installed
    from google.cloud import bigquery
    return bigquery.Client()


def run_all(client, cfg):
    results = []
    for table_cfg in cfg["tables"]:
        table = table_cfg["name"]
        checks = table_cfg.get("checks", {})

        for check_name, check_cfg in checks.items():
            fn = REGISTRY.get(check_name)
            if fn is None:
                results.append({
                    "table": table,
                    "check": check_name,
                    "column": None,
                    "status": "ERROR",
                    "detail": f"unknown check '{check_name}', valid ones: {sorted(REGISTRY)}",
                })
                continue

            try:
                for r in fn(client, table, check_cfg):
                    r["table"] = table
                    results.append(r)
            except Exception as e:
                # one bad table shouldn't kill the whole run
                results.append({
                    "table": table,
                    "check": check_name,
                    "column": None,
                    "status": "ERROR",
                    "detail": str(e),
                })
    return results


def main():
    parser = argparse.ArgumentParser(description="Run data quality checks on BigQuery tables")
    parser.add_argument("--config", default="config/rules.yaml")
    parser.add_argument("--out", default=".", help="directory for report.html / report.json")
    args = parser.parse_args()

    cfg = load_config(args.config)
    client = get_client()

    results = run_all(client, cfg)

    os.makedirs(args.out, exist_ok=True)
    html_path = reporter.write_html(results, os.path.join(args.out, "report.html"))
    json_path = reporter.write_json(results, os.path.join(args.out, "report.json"))
    print(f"wrote {html_path} and {json_path}")

    alert(results)

    # non-zero exit if anything failed, so cron/CI notices
    failed = [r for r in results if r["status"] in ("FAIL", "ERROR")]
    for r in results:
        col = f" [{r['column']}]" if r.get("column") else ""
        print(f"{r['status']:5}  {r['table']}  {r['check']}{col}  {r['detail']}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
