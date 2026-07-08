# Range check: count rows outside [min, max] for each configured column.
# min or max can be left out if you only care about one side.


def run(client, table, config):
    # config here is a list of rules, one per column
    rules = config if isinstance(config, list) else [config]
    results = []

    for rule in rules:
        col = rule.get("column")
        lo = rule.get("min")
        hi = rule.get("max")

        if col is None or (lo is None and hi is None):
            results.append({
                "check": "range_check",
                "column": col,
                "status": "SKIP",
                "detail": "need a column plus at least one of min/max",
            })
            continue

        conditions = []
        if lo is not None:
            conditions.append(f"`{col}` < {lo}")
        if hi is not None:
            conditions.append(f"`{col}` > {hi}")
        out_of_range = " OR ".join(conditions)

        sql = f"""
        SELECT
            COUNTIF({out_of_range}) AS bad_rows,
            COUNT(*) AS total_rows
        FROM `{table}`
        WHERE `{col}` IS NOT NULL
        """

        row = list(client.query(sql).result())[0]
        bad = int(row["bad_rows"])

        bounds = []
        if lo is not None:
            bounds.append(f"min {lo}")
        if hi is not None:
            bounds.append(f"max {hi}")

        results.append({
            "check": "range_check",
            "column": col,
            "status": "PASS" if bad == 0 else "FAIL",
            "detail": f"{bad}/{row['total_rows']} rows outside {', '.join(bounds)}",
        })
    return results
