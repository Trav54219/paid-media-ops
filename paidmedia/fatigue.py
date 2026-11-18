"""Creative fatigue: high frequency AND CTR decay over the window."""
from collections import defaultdict


def _ctr(rows):
    i = sum(r["impressions"] for r in rows)
    return sum(r["clicks"] for r in rows) / i if i else 0.0


def detect(rows, window=7, freq_threshold=2.5, ctr_drop=0.25, min_impressions=5000):
    """Compare first `window` days to last `window` days per ad.

    Fatigued if last-window frequency >= freq_threshold and CTR fell >= ctr_drop.
    """
    by_ad = defaultdict(list)
    for r in rows:
        by_ad[r["ad"]].append(r)
    out = []
    for ad, rs in sorted(by_ad.items()):
        rs.sort(key=lambda r: r["date"])
        if len(rs) < window * 2 or sum(r["impressions"] for r in rs) < min_impressions:
            continue
        first, last = rs[:window], rs[-window:]
        c0, c1 = _ctr(first), _ctr(last)
        drop = (c0 - c1) / c0 if c0 else 0.0
        freq = sum(r["frequency"] for r in last) / window
        if freq >= freq_threshold and drop >= ctr_drop:
            out.append({"ad": ad, "frequency": round(freq, 2), "ctr_start": round(c0, 5),
                        "ctr_end": round(c1, 5), "ctr_drop": round(drop, 3)})
    return out
