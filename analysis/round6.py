"""B1 (PLAN A1) — high-N confirmation of the central null. Scale-up of Round 5a.
Reports, per PLAN A6: self-2AFC (d', binom), the TWO confound controls (judge-fixed, pair-fixed)
with bootstrap CIs, disagreement-conditioning (Ashuach), calibration (B5), standing audits, and an
explicit pre-registered decision-rule verdict.
Cluster bootstrap resamples PROMPTS (the independent unit)."""
import json, os, math, random
from collections import defaultdict
from statistics import NormalDist
random.seed(20260605)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
RAW = os.path.join(ROOT, "logs", "raw_round6_output.json"); R6 = os.path.join(ROOT, "round6")
TIERS = ["opus", "sonnet", "haiku"]; Z = NormalDist()
PAIRS = [["opus", "sonnet"], ["opus", "haiku"], ["sonnet", "haiku"]]
LEAK = ["chromemcp", "c:\\users", "chrome profile", "structured output", "subagent",
        "distributed agent", "absolute path", "claude code", " mcp", "ai assistant", "workflow orchestrat"]


def binom_p(k, n, p=0.5):
    from math import comb
    if n == 0: return float("nan")
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    o = pmf(k); return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= o + 1e-12))


def dprime(pc): pc = min(max(pc, 1e-6), 1 - 1e-6); return math.sqrt(2) * Z.inv_cdf(pc)


def boot_ci(prompts, by_prompt, stat_fn, B=2000):
    """Cluster bootstrap over prompts; stat_fn(list_of_records)->float|None."""
    vals = []
    pl = list(prompts)
    for _ in range(B):
        samp = [pl[int(random.random() * len(pl))] for _ in range(len(pl))]
        recs = []
        for pid in samp: recs.extend(by_prompt.get(pid, []))
        v = stat_fn(recs)
        if v is not None and not (isinstance(v, float) and math.isnan(v)): vals.append(v)
    vals.sort()
    if not vals: return (float("nan"), float("nan"))
    lo = vals[int(0.025 * len(vals))]; hi = vals[min(len(vals) - 1, int(0.975 * len(vals)))]
    return (lo, hi)


def acc(recs):
    recs = [r for r in recs if r is not None]
    return (sum(1 for r in recs if r["correct"]) / len(recs)) if recs else float("nan")


def main():
    with open(RAW, encoding="utf-8") as fh:
        res = json.load(fh)["result"]
    corpus, ids = res["corpus"], res["ids"]
    os.makedirs(os.path.join(R6, "corpus"), exist_ok=True); os.makedirs(os.path.join(R6, "ids"), exist_ok=True)
    for c in corpus: json.dump(c, open(os.path.join(R6, "corpus", f"{c['prompt_id']}__{c['generator_label']}.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    for r in ids: json.dump(r, open(os.path.join(R6, "ids", f"{r['prompt_id']}__{r['judge']}__{r['pair'][0]}v{r['pair'][1]}__{r['role']}.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    prompts = sorted({r["prompt_id"] for r in ids})
    by_prompt = defaultdict(list)
    for r in ids: by_prompt[r["prompt_id"]].append(r)
    print(f"Wrote {len(corpus)} corpus + {len(ids)} id files. prompts={len(prompts)}\n")

    # ---- self-2AFC by judge ----
    print("############ self-2AFC by judge (names-given) ############")
    for j in TIERS:
        s = [r for r in ids if r["judge"] == j and r["role"] == "self"]
        k = sum(1 for r in s if r["correct"]); n = len(s)
        ci = boot_ci(prompts, by_prompt, lambda R, j=j: acc([r for r in R if r["judge"] == j and r["role"] == "self"]))
        print(f"  {j:7s} {k}/{n}={k/n:.3f}  d'={dprime(k/n):+.2f}  p={binom_p(k,n):.4f}  CI[{ci[0]:.3f},{ci[1]:.3f}]")

    # ---- CONTROL 1: judge-fixed (per judge: self pairs vs the out pair) ----
    print("\n############ CONTROL 1 — JUDGE-FIXED self-advantage (controls judge capability) ############")
    jf = {}
    for j in TIERS:
        s = [r for r in ids if r["judge"] == j and r["role"] == "self"]
        nt = [r for r in ids if r["judge"] == j and r["role"] == "neutral"]
        adv = acc(s) - acc(nt)
        def stat(R, j=j):
            a = acc([r for r in R if r["judge"] == j and r["role"] == "self"]); b = acc([r for r in R if r["judge"] == j and r["role"] == "neutral"])
            return (a - b) if not (math.isnan(a) or math.isnan(b)) else None
        ci = boot_ci(prompts, by_prompt, stat)
        jf[j] = (adv, ci)
        print(f"  {j:7s} self {acc(s):.3f} (n={len(s)})  neutral-out {acc(nt):.3f} (n={len(nt)})  adv={adv:+.3f}  CI[{ci[0]:+.3f},{ci[1]:+.3f}]")

    # ---- CONTROL 2: pair-fixed (members vs outsider on same texts) ----
    print("\n############ CONTROL 2 — PAIR-FIXED self-advantage (controls texts/difficulty) ############")
    for pr in PAIRS:
        s = [r for r in ids if r["pair"] == pr and r["role"] == "self"]
        nt = [r for r in ids if r["pair"] == pr and r["role"] == "neutral"]
        print(f"  {pr[0]} vs {pr[1]:7s}: members {acc(s):.3f}  outsider {acc(nt):.3f}  adv={acc(s)-acc(nt):+.3f}")
    sall = [r for r in ids if r["role"] == "self"]; nall = [r for r in ids if r["role"] == "neutral"]
    def stat_pf(R):
        a = acc([r for r in R if r["role"] == "self"]); b = acc([r for r in R if r["role"] == "neutral"])
        return (a - b) if not (math.isnan(a) or math.isnan(b)) else None
    pf_ci = boot_ci(prompts, by_prompt, stat_pf)
    pf_adv = acc(sall) - acc(nall)
    print(f"  POOLED: self {acc(sall):.3f}  neutral {acc(nall):.3f}  adv={pf_adv:+.3f}  CI[{pf_ci[0]:+.3f},{pf_ci[1]:+.3f}]")

    # ---- disagreement-conditioning (Ashuach) ----
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
        agree = len(P) - dn
        ps = (dk / dn) if dn else float("nan")
        print(f"  {name:7s} agree {agree/len(P):.0%} | DISAGREE n={dn}: P(self right)={ps:.3f} (adv {2*ps-1:+.3f}, p={binom_p(dk,dn):.4f})")

    # ---- B5 calibration ----
    print("\n############ B5 CALIBRATION (self trials) ############")
    for j in TIERS:
        rows = [r for r in ids if r["judge"] == j and r["role"] == "self" and r.get("confidence") is not None]
        cor = [r["confidence"] for r in rows if r["correct"]]; inc = [r["confidence"] for r in rows if not r["correct"]]
        mc = sum(cor)/len(cor) if cor else float("nan"); mi = sum(inc)/len(inc) if inc else float("nan")
        brier = sum((r["confidence"]-(1 if r["correct"] else 0))**2 for r in rows)/len(rows)
        def stat_gap(R, j=j):
            rr = [r for r in R if r["judge"] == j and r["role"] == "self" and r.get("confidence") is not None]
            c = [r["confidence"] for r in rr if r["correct"]]; i = [r["confidence"] for r in rr if not r["correct"]]
            return (sum(c)/len(c) - sum(i)/len(i)) if c and i else None
        ci = boot_ci(prompts, by_prompt, stat_gap)
        print(f"  {j:7s} conf gap (correct-wrong)={mc-mi:+.3f} CI[{ci[0]:+.3f},{ci[1]:+.3f}]  Brier={brier:.3f}")

    # ---- standing audits ----
    print("\n############ AUDITS ############")
    cw = {(c["prompt_id"], c["generator_label"]): c for c in corpus}
    leaked = {k: [t for t in LEAK if t in v["text"].lower()] for k, v in cw.items()}
    leaked = {k: v for k, v in leaked.items() if v}
    print(f"  harness-leak: {len(leaked)}/{len(corpus)} generations flagged "
          f"{({TIERS[i]: sum(1 for k in leaked if k[1]==TIERS[i]) for i in range(3)})}")
    # length heuristic + position balance
    longer_chosen = diff = 0
    posA = sum(1 for r in ids if r["target_position"] == "A")
    for r in ids:
        wmap = {"A": None, "B": None}
        # words of the two texts in this pair
        wx, wy = r["tX_words"], r["tY_words"]
        # target tier words vs other
        tgt_words = wx if r["target_tier"] == r["pair"][0] else wy
        oth_words = wy if r["target_tier"] == r["pair"][0] else wx
        if tgt_words == oth_words: continue
        diff += 1
        tgt_longer = tgt_words > oth_words
        chose_tgt = r["correct"]
        if (chose_tgt and tgt_longer) or ((not chose_tgt) and (not tgt_longer)): longer_chosen += 1
    print(f"  length-heuristic: judges chose the LONGER text {longer_chosen}/{diff} = {longer_chosen/diff:.3f} (~0.5 = no bias)")
    print(f"  position balance: target in A for {posA}/{len(ids)} = {posA/len(ids):.3f} (~0.5 by design)")

    # ---- VERDICT ----
    print("\n############ PRE-REGISTERED DECISION RULE (PLAN A1) ############")
    jf_pos = all(jf[j][1][0] > 0 for j in TIERS)  # all judge-fixed CIs exclude 0 positive
    jf_nonpos = all(jf[j][1][0] <= 0 for j in TIERS)  # all bracket 0/negative
    pf_pos = pf_ci[0] > 0
    pf_nonpos = pf_ci[0] <= 0
    if jf_pos and pf_pos:
        print("  -> Advantage CI excludes 0 POSITIVE in both controls: SELF-RECOGNITION REAL -> pivot paper.")
    elif jf_nonpos and pf_nonpos:
        print("  -> Advantage CI brackets 0/negative in BOTH controls: NULL CONFIRMED AT POWER (headline).")
    else:
        print("  -> Controls disagree: UNRESOLVED (underpowered/confounded) — do not headline.")
    print(f"     judge-fixed CIs: " + ", ".join(f"{j}[{jf[j][1][0]:+.3f},{jf[j][1][1]:+.3f}]" for j in TIERS))
    print(f"     pair-fixed pooled CI: [{pf_ci[0]:+.3f},{pf_ci[1]:+.3f}]")


if __name__ == "__main__":
    main()
