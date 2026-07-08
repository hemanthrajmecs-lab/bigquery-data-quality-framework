# Duplicate check: how many extra rows exist for the key columns.
# "Extra" meaning beyond the first occurrence, so 3 copies of a row = 2 dupes.


def run(client, table, config):
    keys = config.get("key_columns", [])
    if not keys:
        return [{
            "check": "duplicate_check",
            "column": None,
            "status": "SKIP",
            "detail": "no key_columns configured",
        }]

    key_list = ", ".join(f"`{k}`" for k in keys)
    sql = f"""
    SELECT COALESCE(SUM(n - 1), 0) AS dupes
    FROM (
        SELECT COUNT(*) AS n
        FROM `{table}`
        GROUP BY {key_list}
    )
    WHERE n > 1
    """

    row = list(client.query(sql).result())[0]
    dupes = int(row["dupes"])

    return [{
        "check": "duplicate_check",
        "column": ", ".join(keys),
        "status": "PASS" if dupes == 0 else "FAIL",
        "detail": f"{dupes} duplicate rows on key ({', '.join(keys)})"
                  if dupes else "no duplicates found",
    }]
