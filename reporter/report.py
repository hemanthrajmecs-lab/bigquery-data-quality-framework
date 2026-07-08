# Turns check results into report.html and report.json.
# The HTML is deliberately dependency-free, just a table with inline styles,
# so you can open it anywhere or shove it in an email.

import json
from datetime import datetime, timezone

STATUS_COLORS = {
    "PASS": "#1a7f37",
    "FAIL": "#cf222e",
    "WARN": "#9a6700",
    "SKIP": "#57606a",
    "ERROR": "#cf222e",
}


def summarize(results):
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


def write_json(results, path="report.json"):
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize(results),
        "results": results,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def write_html(results, path="report.html"):
    counts = summarize(results)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    badge = " · ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    overall_bad = counts.get("FAIL", 0) + counts.get("ERROR", 0)
    headline = "All good" if overall_bad == 0 else f"{overall_bad} problem(s) found"
    headline_color = "#1a7f37" if overall_bad == 0 else "#cf222e"

    rows = []
    for r in results:
        color = STATUS_COLORS.get(r["status"], "#57606a")
        rows.append(f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #d0d7de;">{r.get('table', '')}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #d0d7de;">{r['check']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #d0d7de;">{r.get('column') or ''}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #d0d7de;">
                <span style="color:#fff;background:{color};padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;">{r['status']}</span>
            </td>
            <td style="padding:8px 12px;border-bottom:1px solid #d0d7de;color:#57606a;">{r['detail']}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Data quality report</title></head>
<body style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:40px;color:#1f2328;">
    <h1 style="margin-bottom:4px;">Data quality report</h1>
    <p style="color:#57606a;margin-top:0;">Generated {generated}</p>
    <h2 style="color:{headline_color};">{headline}</h2>
    <p style="color:#57606a;">{badge}</p>
    <table style="border-collapse:collapse;width:100%;margin-top:16px;">
        <thead>
            <tr style="text-align:left;background:#f6f8fa;">
                <th style="padding:8px 12px;border-bottom:2px solid #d0d7de;">Table</th>
                <th style="padding:8px 12px;border-bottom:2px solid #d0d7de;">Check</th>
                <th style="padding:8px 12px;border-bottom:2px solid #d0d7de;">Column</th>
                <th style="padding:8px 12px;border-bottom:2px solid #d0d7de;">Status</th>
                <th style="padding:8px 12px;border-bottom:2px solid #d0d7de;">Detail</th>
            </tr>
        </thead>
        <tbody>{''.join(rows)}
        </tbody>
    </table>
</body>
</html>"""

    with open(path, "w") as f:
        f.write(html)
    return path
