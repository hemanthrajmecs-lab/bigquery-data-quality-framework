# Schema check: compare the live table schema against what rules.yaml expects.
# Catches the classic "someone changed a column type overnight" problem.
# No query needed, table metadata is enough.


def run(client, table, config):
    expected = config.get("expected_columns", [])
    if not expected:
        return [{
            "check": "schema_check",
            "column": None,
            "status": "SKIP",
            "detail": "no expected_columns configured",
        }]

    live = {f.name: f.field_type for f in client.get_table(table).schema}

    results = []
    for col in expected:
        name = col["name"]
        want = col["type"].upper()

        if name not in live:
            results.append({
                "check": "schema_check",
                "column": name,
                "status": "FAIL",
                "detail": f"column missing from table (expected {want})",
            })
        elif live[name].upper() != want:
            results.append({
                "check": "schema_check",
                "column": name,
                "status": "FAIL",
                "detail": f"type drift: expected {want}, table has {live[name].upper()}",
            })
        else:
            results.append({
                "check": "schema_check",
                "column": name,
                "status": "PASS",
                "detail": f"{want}, as expected",
            })

    # also flag columns that showed up out of nowhere, usually harmless
    # but worth knowing about
    expected_names = {c["name"] for c in expected}
    surprise = sorted(set(live) - expected_names)
    if surprise:
        results.append({
            "check": "schema_check",
            "column": ", ".join(surprise),
            "status": "WARN",
            "detail": "columns present in table but not in expected schema",
        })
    return results
