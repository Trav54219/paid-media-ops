# paid-media-ops

A small Python toolkit for the daily and weekly work of a paid media / ad operations role (Meta Ads, Google Ads).

**All data is synthetic.** A seeded generator produces ad-platform-style exports. **Nothing connects to the Meta or Google APIs**, and no real account, client, or result is represented. The numbers below come from running this code on that generated data, so they show the tools work, not how any real campaign performs.

## What it does

| Module | Purpose |
|---|---|
| `data.py` | Seeded campaign / ad set / ad hierarchy with daily spend, clicks, conversions, revenue, frequency. A few behaviours are planted on purpose (an overspending campaign, an underspending one, a weak one, one fatigued ad) so detectors have something to find. |
| `metrics.py` | Rollups at any level; CTR, CPM, CPA, ROAS, CVR; break-even ROAS (1/margin) and break-even CPA. |
| `pacing.py` | Linear month-end projection vs plan; flags underspend (<0.85) and overspend (>1.10). |
| `rules.py` | Daily-checklist decisions per campaign: scale, kill, or hold, with a minimum spend/conversion floor before judging. |
| `fatigue.py` | Flags ads whose last-7-day frequency is high and CTR fell vs the first 7 days. |
| `abtest.py` | Two-proportion z-test, p-value, confidence interval, per-arm sample size. Stdlib only. |
| `utm.py` | UTM validator (required params, snake_case, allowed source/medium, source-medium pairing) and campaign naming linter (`<platform>_<objective>_<audience>_<geo>`). |
| `report.py` | Weekly performance report as one static HTML file. |

## Use

```
python -m paidmedia generate --out data/ads.csv
python -m paidmedia pacing | rules | fatigue
python -m paidmedia report --out report.html
python -m paidmedia abtest 100 1000 130 1000
python -m paidmedia lint meta_prospecting_lookalike_us "https://x.com/?utm_source=Meta"
pytest
```

## Rule defaults (edit in `rules.py`)

Gross margin 50% gives break-even ROAS 2.0. Scale at >= 1.3x break-even, kill below 0.8x, hold between. Minimum $300 spend and 10 conversions before any call. These are illustrative defaults; real thresholds depend on margin, LTV, and attribution window.

## Limits

Pacing is linear (no day-of-week weighting). Fatigue uses a simple first-vs-last window comparison. The z-test assumes independent users and a fixed sample size decided up front (no peeking correction).
