import math
import pytest
from paidmedia import data, metrics, pacing, rules, fatigue, abtest, utm, report

ROWS = data.generate(42)
PLANNED = {k: v["planned"] for k, v in data.plan().items()}


def test_generation_is_seeded_and_shaped():
    assert data.generate(42) == ROWS
    assert data.generate(7) != ROWS
    tree = metrics.hierarchy(ROWS)
    assert len(tree) == 6 and all(len(s) == 2 for s in tree.values())
    assert all(len(a) == 2 for s in tree.values() for a in s.values())
    assert {r["date"] for r in ROWS}.__len__() == data.DAYS


def test_csv_roundtrip(tmp_path):
    p = tmp_path / "a.csv"
    data.write_csv(ROWS, p)
    assert data.read_csv(p) == ROWS


def test_metrics_and_break_even():
    m = metrics.rollup(ROWS, "campaign")["google_search_brand_us"]
    assert m["roas"] == pytest.approx(m["revenue"] / m["spend"])
    assert metrics.break_even_roas(0.5) == 2.0
    assert metrics.break_even_cpa(80, 0.5) == 40
    with pytest.raises(ValueError):
        metrics.break_even_roas(0)


def test_pacing_flags_planted_over_and_underspend():
    st = {p["campaign"]: p["status"] for p in pacing.pacing(ROWS, PLANNED, data.DAYS, data.DAYS)}
    assert st["google_search_generic_us"] == "overspend"
    assert st["google_pmax_catalog_us"] == "underspend"


def test_pacing_projection_math():
    rows = [{"campaign": "c", "spend": 100.0}] * 5
    p = pacing.pacing(rows, {"c": 1000}, 5, 10)[0]
    assert p["projected"] == 1000 and p["status"] == "on_pace"


def test_rules_thresholds():
    mk = lambda spend, conv, rev: [dict(campaign="c", impressions=1, clicks=1, spend=spend, conversions=conv, revenue=rev)]
    act = lambda rows: rules.decide(rows)[0]["action"]
    assert act(mk(100, 50, 1000)) == "hold"      # too little spend
    assert act(mk(1000, 50, 3000)) == "scale"    # roas 3.0 >= 2.6
    assert act(mk(1000, 50, 1500)) == "kill"     # roas 1.5 < 1.6
    assert act(mk(1000, 50, 2000)) == "hold"     # roas 2.0 in band
    assert act(mk(1000, 5, 9000)) == "hold"      # too few conversions


def test_rules_on_synthetic_data_kills_the_planted_loser():
    d = {x["campaign"]: x["action"] for x in rules.decide(ROWS)}
    assert d["meta_prospecting_broad_us"] == "kill"


def test_fatigue_finds_only_planted_ad():
    found = [f["ad"] for f in fatigue.detect(ROWS)]
    assert found == ["meta_prospecting_lookalike_us_as1_ad1"]


def test_abtest_known_values():
    r = abtest.z_test(100, 1000, 130, 1000)
    assert r["z"] == pytest.approx(2.1, abs=0.1)
    assert r["significant"] and r["p_value"] < 0.05
    assert not abtest.z_test(100, 1000, 105, 1000)["significant"]
    assert abtest.z_test(100, 1000, 100, 1000)["p_value"] == pytest.approx(1.0)
    lo, hi = abtest.z_test(100, 1000, 130, 1000)["ci_diff"]
    assert lo < 0.03 < hi
    with pytest.raises(ValueError):
        abtest.z_test(5, 0, 1, 10)


def test_sample_size_textbook():
    # 5% base, +20% relative lift, 80% power: roughly 8,100 per arm
    assert 7800 < abtest.sample_size(0.05, 0.20) < 8400
    assert abtest._z_inv(0.975) == pytest.approx(1.96, abs=0.001)


GOOD = "https://x.com/p?utm_source=meta&utm_medium=paid_social&utm_campaign=meta_prospecting_lookalike_us"


def test_utm_valid_and_invalid():
    assert utm.validate_url(GOOD) == []
    bad = utm.validate_url("https://x.com/p?utm_source=Meta&utm_medium=cpc")
    assert any("missing utm_campaign" in e for e in bad)
    assert any("lowercase" in e for e in bad)
    assert any("expects medium" in e or "not in allowed" in e for e in bad)
    assert any("not in allowed" in e for e in utm.validate_url(GOOD.replace("paid_social", "social")))


def test_naming_linter():
    assert utm.lint_campaign_name("meta_prospecting_lookalike_us") == []
    assert utm.lint_campaign_name("Meta Prospecting") == ["must be lowercase snake_case"]
    assert utm.lint_campaign_name("meta_prospecting") != []
    assert any("geo" in e for e in utm.lint_campaign_name("meta_prospecting_lookalike_mars"))
    assert all(utm.lint_campaign_name(c[0]) == [] for c in data.CAMPAIGNS)


def test_report_html():
    html = report.build(ROWS, PLANNED, "2025-03-24", "2025-03-30", 28, 28)
    assert html.startswith("<!doctype html>") and "Synthetic data" in html
    assert "meta_prospecting_lookalike_us_as1_ad1" in html and "overspend" in html
    assert "<script" not in html


def test_cli(tmp_path, capsys):
    from paidmedia.cli import main
    csv = str(tmp_path / "a.csv"); out = str(tmp_path / "r.html")
    assert main(["generate", "--out", csv]) == 0
    assert main(["report", "--csv", csv, "--out", out]) == 0
    assert (tmp_path / "r.html").exists()
    assert main(["lint", "meta_prospecting_lookalike_us"]) == 0
    assert main(["lint", "BadName"]) == 1
