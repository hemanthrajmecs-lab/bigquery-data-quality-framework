# Fires a Slack message when checks fail. Reads the webhook from
# SLACK_WEBHOOK_URL so nothing sensitive ever lands in the repo.
# No webhook set? Falls back to printing, which is all you want locally anyway.

import json
import os
import urllib.request


def alert(results):
    failures = [r for r in results if r["status"] in ("FAIL", "ERROR")]
    if not failures:
        print("alerter: everything passed, staying quiet")
        return

    lines = [f"*{len(failures)} data quality check(s) failed:*"]
    for r in failures:
        col = f" [{r['column']}]" if r.get("column") else ""
        lines.append(f"• `{r.get('table', '?')}` {r['check']}{col}: {r['detail']}")
    text = "\n".join(lines)

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print("alerter: SLACK_WEBHOOK_URL not set, printing instead\n")
        print(text)
        return

    req = urllib.request.Request(
        webhook,
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"alerter: sent to Slack, got {resp.status}")
    except Exception as e:
        # a broken webhook shouldn't take down the whole run
        print(f"alerter: Slack send failed ({e}), dumping to console\n")
        print(text)
