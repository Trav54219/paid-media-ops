"""Aggregation and core metrics: ROAS, CPA, CTR, CPM; hierarchy rollups."""
from collections import defaultdict


def _div(a, b):
    return a / b if b else 0.0


def rollup(rows, key):
    """Sum rows grouped by key (a field name or function). Returns dict of metric dicts."""
    kf = key if callable(key) else (lambda r: r[key])
    acc = defaultdict(lambda: dict(impressions=0, clicks=0, spend=0.0, conversions=0, revenue=0.0))
    for r in rows:
        a = acc[kf(r)]
        for k in a:
            a[k] += r[k]
    return {k: with_ratios(v) for k, v in acc.items()}


def with_ratios(a):
    a = dict(a)
    a["ctr"] = _div(a["clicks"], a["impressions"])
    a["cpm"] = _div(a["spend"], a["impressions"]) * 1000
    a["cpa"] = _div(a["spend"], a["conversions"]) if a["conversions"] else None
    a["roas"] = _div(a["revenue"], a["spend"])
    a["cvr"] = _div(a["conversions"], a["clicks"])
    return a


def hierarchy(rows):
    """campaign -> ad_set -> ads tree of names."""
    tree = defaultdict(lambda: defaultdict(set))
    for r in rows:
        tree[r["campaign"]][r["ad_set"]].add(r["ad"])
    return {c: {s: sorted(a) for s, a in sets.items()} for c, sets in tree.items()}


def break_even_roas(gross_margin):
    """Revenue per $1 spend at which contribution margin is zero: 1 / margin."""
    if not 0 < gross_margin <= 1:
        raise ValueError("gross_margin must be in (0, 1]")
    return 1 / gross_margin


def break_even_cpa(aov, gross_margin):
    return aov * gross_margin
