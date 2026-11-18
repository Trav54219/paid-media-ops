"""UTM taxonomy validator and campaign naming-convention linter.

Conventions (edit TAXONOMY to match your team):
- all UTM values lowercase, [a-z0-9_] only (no spaces, no dashes, no uppercase)
- utm_source/utm_medium come from allowed lists
- campaign names: <platform>_<objective>_<audience>_<geo>, e.g. meta_prospecting_lookalike_us
"""
import re
from urllib.parse import urlparse, parse_qs

TAXONOMY = {
    "utm_source": {"meta", "google", "newsletter", "tiktok"},
    "utm_medium": {"paid_social", "cpc", "email", "display"},
}
REQUIRED = ("utm_source", "utm_medium", "utm_campaign")
VALUE_RE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
PLATFORMS = {"meta", "google", "tiktok"}
OBJECTIVES = {"prospecting", "retargeting", "search", "pmax", "brand"}
GEOS = {"us", "uk", "ca", "au", "eu"}
MEDIUM_FOR_SOURCE = {"meta": "paid_social", "tiktok": "paid_social", "google": "cpc"}


def validate_url(url):
    q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
    errs = []
    for k in REQUIRED:
        if k not in q or not q[k]:
            errs.append(f"missing {k}")
    for k, v in q.items():
        if k.startswith("utm_") and not VALUE_RE.match(v):
            errs.append(f"{k}={v!r} must be lowercase snake_case")
    for k, allowed in TAXONOMY.items():
        if k in q and q[k] not in allowed:
            errs.append(f"{k}={q[k]!r} not in allowed list")
    s, m = q.get("utm_source"), q.get("utm_medium")
    if s in MEDIUM_FOR_SOURCE and m and m != MEDIUM_FOR_SOURCE[s]:
        errs.append(f"source {s!r} expects medium {MEDIUM_FOR_SOURCE[s]!r}, got {m!r}")
    return errs


def lint_campaign_name(name):
    errs = []
    if not VALUE_RE.match(name):
        return ["must be lowercase snake_case"]
    parts = name.split("_")
    if len(parts) < 4:
        return ["expected <platform>_<objective>_<audience>_<geo>"]
    if parts[0] not in PLATFORMS:
        errs.append(f"platform {parts[0]!r} not in {sorted(PLATFORMS)}")
    if parts[1] not in OBJECTIVES:
        errs.append(f"objective {parts[1]!r} not in {sorted(OBJECTIVES)}")
    if parts[-1] not in GEOS:
        errs.append(f"geo {parts[-1]!r} not in {sorted(GEOS)}")
    return errs
