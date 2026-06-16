"""B2 (PLAN A2) — implicit-attribution arm. Pools all logs/raw_b2-*_output.json.
Reports per framing (F0 explicit / F1 sounds-like-you / F2 which-do-you-keep): self-2AFC by judge,
both confound controls (judge-fixed, pair-fixed) with self-advantage + bootstrap CIs,
disagreement-conditioning, the framing x self-advantage x tier table, the manipulation check, and
the pre-registered decision-rule verdict."""
import json, os, math, random, glob, re
from collections import defaultdict
from statistics import NormalDist
random.seed(20260605)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
TIERS = ["opus", "sonnet", "haiku"]; FRAMINGS = ["F0", "F1", "F2"]; Z = NormalDist()
PAIRS = [["opus", "sonnet"], ["opus", "haiku"], ["sonnet", "haiku"]]


def binom_p(k, n, p=0.5):
    from math import comb
    if n == 0: return float("nan")
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    o = pmf(k); return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= o + 1e-12))


def dprime(pc): pc = min(max(pc, 1e-6), 1 - 1e-6); return math.sqrt(2) * Z.inv_cdf(pc)


def acc(recs):
    recs = [r for r in recs if r is not None]
    return (sum(1 for r in recs if r["correct"]) / len(recs)) if recs else float("nan")


def boot_ci(prompts, by_prompt, stat_fn, B=2000):
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


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "logs", "raw_b2-*_output.json")))
    ids = []
    for f in files:
        tag = os.path.basename(f).replace("raw_", "").replace("_output.json", "")
        with open(f, encoding="utf-8") as fh:
            for r in json.load(fh)["result"]["ids"]:
                r["prompt_id"] = tag + ":" + r["prompt_id"]  # namespace so same-prompt batches don't collide
                ids.append(r)
    prompts = sorted({r["prompt_id"] for r in ids})
    by_prompt = defaultdict(list)
    for r in ids: by_prompt[r["prompt_id"]].append(r)
    print(f"B2 pooled over {len(files)} batch(es): {len(ids)} trials, {len(prompts)} prompts.")
    print(f"  files: {[os.path.basename(f) for f in files]}\n")

    for F in FRAMINGS:
        fi = [r for r in ids if r["framing"] == F]
        if not fi: continue
        label = {"F0": "EXPLICIT (which did you write)", "F1": "IMPLICIT-voice (sounds like you)",
                 "F2": "IMPLICIT-choice (which do you keep)"}[F]
        print(f"############ {F} — {label}  (n={len(fi)}) ############")
        for j in TIERS:
            s = [r for r in fi if r["judge"] == j and r["role"] == "self"]
            k = sum(1 for r in s if r["correct"]); n = len(s)
            print(f"  self-2AFC {j:7s} {k}/{n}={k/n:.3f}  d'={dprime(k/n):+.2f}  p={binom_p(k,n):.4g}")
        # judge-fixed
        print("  judge-fixed self-advantage (self pairs - out pair), CI:")
        jf = {}
        for j in TIERS:
            s = [r for r in fi if r["judge"] == j and r["role"] == "self"]
            nt = [r for r in fi if r["judge"] == j and r["role"] == "neutral"]
            adv = acc(s) - acc(nt)
            def stat(R, j=j, F=F):
                a = acc([r for r in R if r["framing"] == F and r["judge"] == j and r["role"] == "self"])
                b = acc([r for r in R if r["framing"] == F and r["judge"] == j and r["role"] == "neutral"])
                return (a - b) if not (math.isnan(a) or math.isnan(b)) else None
            ci = boot_ci(prompts, by_prompt, stat); jf[j] = (adv, ci)
            print(f"    {j:7s} self {acc(s):.3f} (n={len(s)}) - neutral {acc(nt):.3f} (n={len(nt)}) = {adv:+.3f}  CI[{ci[0]:+.3f},{ci[1]:+.3f}]")
        # pair-fixed pooled
        sall = [r for r in fi if r["role"] == "self"]; nall = [r for r in fi if r["role"] == "neutral"]
        def stat_pf(R, F=F):
            a = acc([r for r in R if r["framing"] == F and r["role"] == "self"]); b = acc([r for r in R if r["framing"] == F and r["role"] == "neutral"])
            return (a - b) if not (math.isnan(a) or math.isnan(b)) else None
        pf_ci = boot_ci(prompts, by_prompt, stat_pf)
        print(f"  pair-fixed pooled: self {acc(sall):.3f} - neutral {acc(nall):.3f} = {acc(sall)-acc(nall):+.3f}  CI[{pf_ci[0]:+.3f},{pf_ci[1]:+.3f}]")
        # disagreement
        items = defaultdict(dict)
        for r in fi:
            key = (r["prompt_id"], tuple(r["pair"]))
            if r["role"] == "neutral": items[key]["n"] = r
            else: items[key].setdefault("self", {})[r["judge"]] = r
        dk = dn = 0
        for (pid, pair), rec in items.items():
            if "n" not in rec or "self" not in rec: continue
            cn = bool(rec["n"]["correct"])
            for m in pair:
                if m in rec["self"]:
                    s = bool(rec["self"][m]["correct"])
                    if s != cn: dn += 1; dk += 1 if s else 0
        print(f"  disagreement-conditioned: P(self right | contested) = {dk}/{dn}={dk/dn if dn else float('nan'):.3f} (p={binom_p(dk,dn):.4g})\n")

    # ---- framing x tier self-advantage table (pair-fixed) ----
    print("############ FRAMING x TIER self-advantage (judge-fixed) — the key contrast ############")
    print(f"  {'tier':8s} " + "  ".join(f"{F:>16s}" for F in FRAMINGS))
    for j in TIERS:
        cells = []
        for F in FRAMINGS:
            s = [r for r in ids if r["framing"] == F and r["judge"] == j and r["role"] == "self"]
            nt = [r for r in ids if r["framing"] == F and r["judge"] == j and r["role"] == "neutral"]
            cells.append(f"{acc(s)-acc(nt):+.3f}")
        print(f"  {j:8s} " + "  ".join(f"{c:>16s}" for c in cells))

    # ---- manipulation check ----
    print("\n############ MANIPULATION CHECK (reasoning traces) ############")
    fp = re.compile(r"\b(my|mine|myself|i['’]?m|i am|i \w|me\b)\b", re.I)  # first-person ownership
    tn = re.compile(r"\b(opus|sonnet|haiku)\b", re.I)                      # third-person tier naming
    own = re.compile(r"\b(my (draft|writing|voice|style|reply|response)|sounds like me|wrote this|i wrote|i'?d write)\b", re.I)
    for F in FRAMINGS:
        fi = [r for r in ids if r["framing"] == F and r.get("reason")]
        if not fi: continue
        n = len(fi)
        f_first = sum(1 for r in fi if fp.search(r["reason"])) / n
        f_tier = sum(1 for r in fi if tn.search(r["reason"])) / n
        f_own = sum(1 for r in fi if own.search(r["reason"])) / n
        print(f"  {F}: first-person {f_first:.0%} | explicit-ownership phrase {f_own:.0%} | names a tier {f_tier:.0%}  (n={n})")
    print("  expect: F1/F2 high first-person/ownership, low tier-naming; F0 names tiers. If F1/F2 look like F0 -> manipulation leaked.")

    # ---- decision rule ----
    print("\n############ DECISION RULE (PLAN A2) ############")
    def any_pos(F):  # any tier judge-fixed CI excludes 0 positive AND pair-fixed too
        ok = False
        for j in TIERS:
            s = [r for r in ids if r["framing"] == F and r["judge"] == j and r["role"] == "self"]
            nt = [r for r in ids if r["framing"] == F and r["judge"] == j and r["role"] == "neutral"]
            ci = boot_ci(prompts, by_prompt, lambda R, j=j, F=F: (lambda a, b: (a - b) if not (math.isnan(a) or math.isnan(b)) else None)(
                acc([r for r in R if r["framing"] == F and r["judge"] == j and r["role"] == "self"]),
                acc([r for r in R if r["framing"] == F and r["judge"] == j and r["role"] == "neutral"])))
            if ci[0] > 0: ok = True
        return ok
    for F in ["F1", "F2"]:
        print(f"  {F}: {'self-advantage CI excludes 0 positive in >=1 tier -> POSSIBLE DISCOVERY (inspect both controls)' if any_pos(F) else 'no positive self-advantage -> framing-robust null'}")
    print("  (F1/F2 ~ F0 null -> headline hardens: absent even where self-attribution should be strongest.)")


if __name__ == "__main__":
    main()
