"""Budget pacing: projected month-end spend vs plan, with alerts."""
from collections import defaultdict


def pacing(rows, planned, days_elapsed, days_in_period, under=0.85, over=1.10):
    """planned: {campaign: planned_period_spend}. Linear projection from spend to date.

    pace_ratio = projected / planned. Alert if < under or > over.
    """
    spent = defaultdict(float)
    for r in rows:
        spent[r["campaign"]] += r["spend"]
    out = []
    for camp, plan in planned.items():
        to_date = spent.get(camp, 0.0)
        projected = to_date / days_elapsed * days_in_period if days_elapsed else 0.0
        ratio = projected / plan if plan else 0.0
        status = "underspend" if ratio < under else "overspend" if ratio > over else "on_pace"
        out.append({"campaign": camp, "spend_to_date": round(to_date, 2), "planned": plan,
                    "projected": round(projected, 2), "pace_ratio": round(ratio, 3), "status": status})
    return out


def alerts(pace_rows):
    return [p for p in pace_rows if p["status"] != "on_pace"]
