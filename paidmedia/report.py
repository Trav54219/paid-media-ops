"""Weekly performance report as a single static HTML file (no JS, no network)."""
import html
from .metrics import rollup
from .pacing import pacing
from .rules import decide
from .fatigue import detect


def _money(x):
    return "-" if x is None else f"${x:,.2f}"


def _table(headers, rows):
    h = "".join(f"<th>{html.escape(c)}</th>" for c in headers)
    b = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def build(rows, planned, week_start, week_end, days_elapsed, days_in_period, **rule_cfg):
    wk = [r for r in rows if week_start <= r["date"] <= week_end]
    tot = rollup(wk, lambda r: "all")["all"]
    camp = rollup(wk, "campaign")
    perf = [(c, _money(m["spend"]), m["conversions"], _money(m["cpa"]), f"{m['roas']:.2f}",
             f"{m['ctr']:.2%}") for c, m in sorted(camp.items())]
    to_date = [r for r in rows if r["date"] <= week_end]
    pace = [(p["campaign"], _money(p["spend_to_date"]), _money(p["projected"]), _money(p["planned"]),
             f"{p['pace_ratio']:.2f}", p["status"]) for p in pacing(to_date, planned, days_elapsed, days_in_period)]
    acts = [(d["campaign"], d["roas"], d["break_even_roas"], d["action"], d["reason"])
            for d in decide(wk, **rule_cfg)]
    fat = [(f["ad"], f["frequency"], f"{f['ctr_start']:.2%}", f"{f['ctr_end']:.2%}", f"{f['ctr_drop']:.0%}")
           for f in detect(to_date)]
    fat_html = _table(["Ad", "Freq (last 7d)", "CTR start", "CTR end", "Drop"], fat) if fat else "<p>None detected.</p>"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Weekly performance {week_start} to {week_end}</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;color:#1a1a1a}}
table{{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem}}th,td{{border-bottom:1px solid #ddd;padding:.4rem .6rem;text-align:left}}
th{{background:#f4f4f4}}.kpi span{{display:inline-block;margin-right:2rem}}.note{{color:#666;font-size:13px}}</style></head><body>
<h1>Weekly performance report</h1>
<p class="note">{week_start} to {week_end}. Synthetic data; not connected to Meta or Google.</p>
<p class="kpi"><span><b>Spend</b> {_money(tot['spend'])}</span><span><b>Conversions</b> {tot['conversions']}</span>
<span><b>CPA</b> {_money(tot['cpa'])}</span><span><b>ROAS</b> {tot['roas']:.2f}</span></p>
<h2>By campaign (this week)</h2>{_table(["Campaign", "Spend", "Conv", "CPA", "ROAS", "CTR"], perf)}
<h2>Budget pacing (period to date)</h2>{_table(["Campaign", "Spent", "Projected", "Planned", "Ratio", "Status"], pace)}
<h2>Kill / scale decisions</h2>{_table(["Campaign", "ROAS", "Break-even", "Action", "Reason"], acts)}
<h2>Creative fatigue</h2>{fat_html}
</body></html>"""
