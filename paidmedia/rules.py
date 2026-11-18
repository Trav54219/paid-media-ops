"""Kill / scale / hold rules: a media buyer's daily checklist as code."""
from .metrics import rollup, break_even_roas

DEFAULTS = dict(gross_margin=0.5, min_spend=300.0, min_conversions=10,
                scale_mult=1.3, scale_step=0.20, kill_mult=0.8)


def decide(rows, **cfg):
    """One decision per campaign.

    break-even ROAS = 1/margin. Not enough data -> 'hold (insufficient data)'.
    ROAS >= break_even*scale_mult -> scale (+scale_step budget).
    ROAS <  break_even*kill_mult  -> kill/pause. Otherwise hold/optimise.
    """
    c = {**DEFAULTS, **cfg}
    be = break_even_roas(c["gross_margin"])
    out = []
    for camp, m in sorted(rollup(rows, "campaign").items()):
        if m["spend"] < c["min_spend"] or m["conversions"] < c["min_conversions"]:
            action, why = "hold", "insufficient data"
        elif m["roas"] >= be * c["scale_mult"]:
            action, why = "scale", f"ROAS {m['roas']:.2f} >= {be * c['scale_mult']:.2f}; raise budget {c['scale_step']:.0%}"
        elif m["roas"] < be * c["kill_mult"]:
            action, why = "kill", f"ROAS {m['roas']:.2f} < {be * c['kill_mult']:.2f}; pause or rework"
        else:
            action, why = "hold", f"ROAS {m['roas']:.2f} near break-even {be:.2f}; optimise creative/targeting"
        out.append({"campaign": camp, "roas": round(m["roas"], 2), "cpa": None if m["cpa"] is None else round(m["cpa"], 2),
                    "break_even_roas": round(be, 2), "action": action, "reason": why})
    return out
