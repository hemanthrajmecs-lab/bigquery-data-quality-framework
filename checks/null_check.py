# Null check: fail any column where the null ratio goes over the threshold.
# One query per table no matter how many columns, COUNTIF does the heavy lifting.


def run(client, table, config):
    columns = config.get("columns", [])
    threshold = float(config.get("threshold", 0.0))

    if not columns:
        return [{
            "check": "null_check",
            "column": None,
            "status": "SKIP",
            "detail": "no columns configured",
        }]

    # build one COUNTIF per column instead of one query per column,
    # scanning a big table five times to check five columns gets expensive
    countifs = ",\n        ".join(
        f"COUNTIF(`{col}` IS NULL) AS `null_{col}`" for col in columns
    )
    sql = f"""
    SELECT
        COUNT(*) AS total_rows,
        {countifs}
    FROM `{table}`
    """

    row = list(client.query(sql).result())[0]
    total = row["total_rows"]

    results = []
    for col in columns:
        nulls = row[f"null_{col}"]
        ratio = (nulls / total) if total else 0.0
        ok = ratio <= threshold
        results.append({
            "check": "null_check",
            "column": col,
            "status": "PASS" if ok else "FAIL",
            "detail": f"{nulls}/{total} nulls ({ratio:.2%}), threshold {threshold:.2%}",
        })
    return results
