"""Seeded synthetic ad-platform export generator (Meta-style and Google-style).

Nothing here talks to any API. Rows mimic a daily ad-level export:
date, platform, campaign, ad_set, ad, impressions, clicks, spend, conversions, revenue, frequency.
"""
import csv
import random
from datetime import date, timedelta

START = date(2025, 3, 3)  # a Monday
DAYS = 28

# name, platform, daily_budget, base_cpm, base_ctr, base_cvr, aov, ad_sets, planned_month_spend
CAMPAIGNS = [
    ("meta_prospecting_lookalike_us", "meta", 300, 14.0, 0.011, 0.028, 80, 2, 8400),
    ("meta_retargeting_cart_us", "meta", 120, 22.0, 0.018, 0.060, 80, 2, 3360),
    ("meta_prospecting_broad_us", "meta", 250, 12.0, 0.008, 0.012, 80, 2, 7000),
    ("google_search_brand_us", "google", 90, 30.0, 0.090, 0.110, 80, 2, 2520),
    ("google_search_generic_us", "google", 200, 38.0, 0.032, 0.025, 80, 2, 5600),
    ("google_pmax_catalog_us", "google", 180, 18.0, 0.014, 0.030, 80, 2, 5040),
]
ADS_PER_SET = 2
FIELDS = ["date", "platform", "campaign", "ad_set", "ad", "impressions", "clicks",
          "spend", "conversions", "revenue", "frequency"]


def generate(seed=42, days=DAYS):
    rng = random.Random(seed)
    rows = []
    for ci, (name, plat, budget, cpm, ctr, cvr, aov, n_sets, _plan) in enumerate(CAMPAIGNS):
        for si in range(n_sets):
            for ai in range(ADS_PER_SET):
                ad_set = f"{name}_as{si + 1}"
                ad = f"{ad_set}_ad{ai + 1}"
                share = (budget / (n_sets * ADS_PER_SET))
                # planted behaviours so detectors have real things to find
                fatigue = (name == "meta_prospecting_lookalike_us" and si == 0 and ai == 0)
                bad = (name == "meta_prospecting_broad_us")
                over = (name == "google_search_generic_us")
                under = (name == "google_pmax_catalog_us")
                freq = 1.1
                for d in range(days):
                    day = START + timedelta(days=d)
                    dow = 1.15 if day.weekday() >= 5 else 1.0
                    daily = share * dow * rng.uniform(0.9, 1.1)
                    if over and d >= 14:
                        daily *= 1.35
                    if under and d >= 10:
                        daily *= 0.55
                    cur_ctr = ctr * rng.uniform(0.9, 1.1)
                    if fatigue:
                        freq = 1.1 + d * 0.16
                        cur_ctr *= max(0.35, 1 - d * 0.025)
                    elif plat == "meta":
                        freq = min(3.0, freq + rng.uniform(0.0, 0.05))
                    else:
                        freq = 1.0 + rng.uniform(0, 0.3)
                    imps = int(daily / cpm * 1000)
                    clicks = max(0, int(rng.gauss(imps * cur_ctr, (imps * cur_ctr) ** 0.5 or 1)))
                    cur_cvr = cvr * rng.uniform(0.8, 1.2) * (0.6 if bad else 1.0) * (0.85 if ai else 1.0)
                    conv = max(0, int(rng.gauss(clicks * cur_cvr, (clicks * cur_cvr) ** 0.5 or 1)))
                    spend = round(imps * cpm / 1000, 2)
                    rev = round(conv * aov * rng.uniform(0.9, 1.1), 2)
                    rows.append({"date": day.isoformat(), "platform": plat, "campaign": name,
                                 "ad_set": ad_set, "ad": ad, "impressions": imps, "clicks": clicks,
                                 "spend": spend, "conversions": conv, "revenue": rev,
                                 "frequency": round(freq, 2)})
    return rows


def plan():
    """campaign -> dict(daily_budget, planned_month_spend, margin inputs)."""
    return {c[0]: {"daily_budget": c[2], "planned": c[8], "aov": c[6]} for c in CAMPAIGNS}


def write_csv(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    out = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            for k in ("impressions", "clicks", "conversions"):
                r[k] = int(r[k])
            for k in ("spend", "revenue", "frequency"):
                r[k] = float(r[k])
            out.append(r)
    return out
