"""CLI: python -m paidmedia <command>."""
import argparse
import json
import sys
from datetime import timedelta
from . import data, pacing, rules, fatigue, abtest, utm, report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="paidmedia", description="Paid media ops over SYNTHETIC data.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate"); g.add_argument("--out", default="data/ads.csv"); g.add_argument("--seed", type=int, default=42)
    for n in ("pacing", "rules", "fatigue"):
        p = sub.add_parser(n); p.add_argument("--csv", default="data/ads.csv")
    r = sub.add_parser("report"); r.add_argument("--csv", default="data/ads.csv"); r.add_argument("--out", default="report.html")
    a = sub.add_parser("abtest")
    a.add_argument("conv_a", type=int); a.add_argument("n_a", type=int); a.add_argument("conv_b", type=int); a.add_argument("n_b", type=int)
    u = sub.add_parser("lint"); u.add_argument("items", nargs="+", help="UTM URLs or campaign names")
    args = ap.parse_args(argv)

    if args.cmd == "generate":
        import os
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        data.write_csv(data.generate(args.seed), args.out)
        print(f"wrote {args.out}")
        return 0
    if args.cmd == "abtest":
        res = abtest.z_test(args.conv_a, args.n_a, args.conv_b, args.n_b)
        print(json.dumps(res, indent=2))
        return 0
    if args.cmd == "lint":
        bad = 0
        for item in args.items:
            errs = utm.validate_url(item) if item.startswith("http") else utm.lint_campaign_name(item)
            print(("FAIL " if errs else "ok   ") + item + ("".join(f"\n     - {e}" for e in errs)))
            bad += bool(errs)
        return 1 if bad else 0

    rows = data.read_csv(args.csv)
    planned = {k: v["planned"] for k, v in data.plan().items()}
    if args.cmd == "pacing":
        for p in pacing.pacing(rows, planned, data.DAYS, data.DAYS):
            print(p)
    elif args.cmd == "rules":
        for d in rules.decide(rows):
            print(d)
    elif args.cmd == "fatigue":
        for f in fatigue.detect(rows) or ["none detected"]:
            print(f)
    elif args.cmd == "report":
        end = data.START + timedelta(days=data.DAYS - 1)
        start = end - timedelta(days=6)
        html = report.build(rows, planned, start.isoformat(), end.isoformat(), data.DAYS, data.DAYS)
        with open(args.out, "w") as f:
            f.write(html)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
