# Freshness check: has the table been touched recently?
# Uses the table's last modified timestamp from metadata, so it's free,
# no query cost at all.

from datetime import datetime, timezone


def run(client, table, config):
    max_hours = float(config.get("max_hours_since_update", 24))

    modified = client.get_table(table).modified  # tz-aware datetime from BQ
    age_hours = (datetime.now(timezone.utc) - modified).total_seconds() / 3600

    return [{
        "check": "freshness_check",
        "column": None,
        "status": "PASS" if age_hours <= max_hours else "FAIL",
        "detail": f"last updated {age_hours:.1f}h ago, limit is {max_hours:.0f}h",
    }]
