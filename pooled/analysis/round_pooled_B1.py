"""Pooled B1 analysis: round6 + round7 (independent prompt sets) -> 120 prompts/cell.
Same suite as round6.py (both confound controls w/ bootstrap CIs, disagreement-conditioning,
calibration, audits, pre-registered decision-rule verdict). Tightens the CIs by doubling N."""
import json, os, math, random, sys
from collections import defaultdict
from statistics import NormalDist
random.seed(20260605)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
DEFAULT = [os.path.join(ROOT, "logs", "raw_round6_output.json"),
           os.path.join(ROOT, "logs", "raw_round7_output.json")]
RAWS = [os.path.join(ROOT, "logs", f"raw_{a}_output.json") for a in sys.argv[1:]] or DEFAULT
TIERS = ["opus", "sonnet", "haiku"]; Z = NormalDist()
PAIRS = [["opus", "sonnet"], ["opus", "haiku"], ["sonnet", "haiku"]]


def binom_p(k, n, p=0.5):
    from math import comb
    if n == 0: return float("nan")
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    o = pmf(k); return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= o + 1e-12))


def dprime(pc): pc = min(max(pc, 1e-6), 1 - 1e-6); return math.sqrt(2) * Z.inv_cdf(pc)


def boot_ci(prompts, by_prompt, stat_fn, B=3000):
    vals = []; pl = list(prompts)
    for _ in range(B):
        samp = [pl[int(random.random() * len(pl))] for _ in range(len(pl))]
        recs = []
        for pid in samp: recs.extend(by_prompt.get(pid, []))
        v = stat_fn(recs)
        if v is not None and not (isinstance(v, float) and math.isnan(v)): vals.append(v)
    vals.sort()
    if not vals: return (float("nan"), float("nan"))
    return (vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))])


def acc(recs):
    recs = [r for r in recs if r is not None]
    return (sum(1 for r in recs if r["correct"]) / len(recs)) if recs else float("nan")


def main():
    ids, corpus = [], []
    for rp in RAWS:
        with open(rp, encoding="utf-8") as fh:
            res = json.load(fh)["result"]
        ids.extend(res["ids"]); corpus.extend(res["corpus"])
    prompts = sorted({r["prompt_id"] for r in ids})
    by_prompt = defaultdict(list)
    for r in ids: by_prompt[r["prompt_id"]].append(r)
    print(f"POOLED round6+round7: {len(corpus)} generations, {len(ids)} trials, {len(prompts)} prompts.\n")

    print("############ self-2AFC by judge (pooled, names-given) ############")
    for j in TIERS:
        s = [r for r in ids if r["judge"] == j and r["role"] == "self"]
        k = sum(1 for r in s if r["correct"]); n = len(s)
        ci = boot_ci(prompts, by_prompt, lambda R, j=j: acc([r for r in R if r["judge"] == j and r["role"] == "self"]))
        print(f"  {j:7s} {k}/{n}={k/n:.3f}  d'={dprime(k/n):+.2f}  p={binom_p(k,n):.4g}  CI[{ci[0]:.3f},{ci[1]:.3f}]")

    print("\n############ CONTROL 1 - JUDGE-FIXED self-advantage (CIs) ############")
    jf = {}
    for j in TIERS:
        s = [r for r in ids if r["judge"] == j and r["role"] == "self"]
        nt = [r for r in ids if r["judge"] == j and r["role"] == "neutral"]
        adv = acc(s) - acc(nt)
        def stat(R, j=j):
            a = acc([r for r in R if r["judge"] == j and r["role"] == "self"]); b = acc([r for r in R if r["judge"] == j and r["role"] == "neutral"])
            return (a - b) if not (math.isnan(a) or math.isnan(b)) else None
        ci = boot_ci(prompts, by_prompt, stat); jf[j] = (adv, ci)
        print(f"  {j:7s} self {acc(s):.3f} (n={len(s)})  neutral-out {acc(nt):.3f} (n={len(nt)})  adv={adv:+.3f}  CI[{ci[0]:+.3f},{ci[1]:+.3f}]")

    print("\n############ CONTROL 2 - PAIR-FIXED self-advantage (CIs) ############")
    for pr in PAIRS:
        s = [r for r in ids if r["pair"] == pr and r["role"] == "self"]
        nt = [r for r in ids if r["pair"] == pr and r["role"] == "neutral"]
        print(f"  {pr[0]} vs {pr[1]:7s}: members {acc(s):.3f}  outsider {acc(nt):.3f}  adv={acc(s)-acc(nt):+.3f}")
    sall = [r for r in ids if r["role"] == "self"]; nall = [r for r in ids if r["role"] == "neutral"]
    def stat_pf(R):
        a = acc([r for r in R if r["role"] == "self"]); b = acc([r for r in R if r["role"] == "neutral"])
        return (a - b) if not (math.isnan(a) or math.isnan(b)) else None
    pf_ci = boot_ci(prompts, by_prompt, stat_pf)
    print(f"  POOLED: self {acc(sall):.3f}  neutral {acc(nall):.3f}  adv={acc(sall)-acc(nall):+.3f}  CI[{pf_ci[0]:+.3f},{pf_ci[1]:+.3f}]")

    print("\n############ DISAGREEMENT-CONDITIONED (Ashuach) ############")
    items = defaultdict(dict)
    for r in ids:
        key = (r["prompt_id"], tuple(r["pair"]))
        if r["role"] == "neutral": items[key]["n"] = r
        else: items[key].setdefault("self", {})[r["judge"]] = r
    pts = []
    for (pid, pair), rec in items.items():
        if "n" not in rec or "self" not in rec: continue
        cn = bool(rec["n"]["correct"])
        for m in pair:
            if m in rec["self"]: pts.append({"tier": m, "s": bool(rec["self"][m]["correct"]), "n": cn})
    for name, P in [("ALL", pts)] + [(t, [p for p in pts if p["tier"] == t]) for t in TIERS]:
        dis = [p for p in P if p["s"] != p["n"]]; dk = sum(p["s"] for p in dis); dn = len(dis)
        ps = (dk / dn) if dn else float("nan")
        print(f"  {name:7s} agree {(len(P)-dn)/len(P):.0%} | DISAGREE n={dn}: P(self right)={ps:.3f} (adv {2*ps-1:+.3f}, p={binom_p(dk,dn):.4g})")

    print("\n############ B5 CALIBRATION (self trials, CIs on gap) ############")
    for j in TIERS:
        rows = [r for r in ids if r["judge"] == j and r["role"] == "self" and r.get("confidence") is not None]
        cor = [r["confidence"] for r in rows if r["correct"]]; inc = [r["confidence"] for r in rows if not r["correct"]]
        mc = sum(cor)/len(cor) if cor else float("nan"); mi = sum(inc)/len(inc) if inc else float("nan")
        brier = sum((r["confidence"]-(1 if r["correct"] else 0))**2 for r in rows)/len(rows)
        def sg(R, j=j):
            rr = [r for r in R if r["judge"] == j and r["role"] == "self" and r.get("confidence") is not None]
            c = [r["confidence"] for r in rr if r["correct"]]; i = [r["confidence"] for r in rr if not r["correct"]]
            return (sum(c)/len(c) - sum(i)/len(i)) if c and i else None
        ci = boot_ci(prompts, by_prompt, sg)
        print(f"  {j:7s} gap={mc-mi:+.3f} CI[{ci[0]:+.3f},{ci[1]:+.3f}]  Brier={brier:.3f}")

    print("\n############ DECISION RULE (PLAN A1), pooled ############")
    jf_nonpos = all(jf[j][1][0] <= 0 for j in TIERS); jf_pos = all(jf[j][1][0] > 0 for j in TIERS)
    if jf_pos and pf_ci[0] > 0:
        print("  -> CI excludes 0 POSITIVE both controls: SELF-RECOGNITION REAL -> pivot.")
    elif jf_nonpos and pf_ci[0] <= 0:
        print("  -> CI brackets 0/negative BOTH controls: NULL CONFIRMED AT POWER.")
    else:
        print("  -> Controls disagree: UNRESOLVED.")
    print("     judge-fixed CIs: " + ", ".join(f"{j}[{jf[j][1][0]:+.3f},{jf[j][1][1]:+.3f}]" for j in TIERS))
    print(f"     pair-fixed pooled CI: [{pf_ci[0]:+.3f},{pf_ci[1]:+.3f}]")


if __name__ == "__main__":
    main()
