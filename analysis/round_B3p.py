"""B3' (PREREGISTRATION_B3.md) — capability-matched neutral for the forgery paradigm.
Set2: Sonnet forges Haiku -> judges Opus(neutral,KEY), Haiku(self), Sonnet(forger).
Set3: Opus forges Sonnet -> judges Sonnet(self), Haiku(neutral), Opus(forger).
Set1 = B4 (Sonnet forges Opus); clean pooled Opus-self = 0.725 (loaded from raw_b4*).
   (The prereg and the verbatim runner script reference the pre-rerun value 0.762; the
    authoritative clean re-run value is 0.725 — see README Provenance.)
PRIMARY: Opus-neutral(Set2) vs Opus-self(Set1); bootstrap 95% CI on the difference.
  CI brackets 0 -> capability account (predicted). CI excludes 0 (self>neutral) -> residual familiarity.
"""
import json, os, math, glob, random
from statistics import NormalDist
random.seed(20260612)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
RAW = os.path.join(ROOT, "logs", "raw_b3p_output.json")
B4RAWS = sorted(glob.glob(os.path.join(ROOT, "logs", "raw_b4*_output.json")))
OUT = os.path.join(ROOT, "round_b3p"); Z = NormalDist()


def binom_p(k, n, p=0.5):
    from math import comb
    if n == 0: return float("nan")
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    o = pmf(k); return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= o + 1e-12))


def dprime(pc): pc = min(max(pc, 1e-6), 1 - 1e-6); return math.sqrt(2) * Z.inv_cdf(pc)


def acc(rows): return (sum(1 for r in rows if r["correct"]) / len(rows)) if rows else float("nan")


def boot_diff_ci(a_correct, b_correct, B=5000):
    """CI on mean(a)-mean(b), independent resamples (a=self, b=neutral). lists of 0/1."""
    diffs = []
    na, nb = len(a_correct), len(b_correct)
    for _ in range(B):
        sa = sum(a_correct[int(random.random() * na)] for _ in range(na)) / na
        sb = sum(b_correct[int(random.random() * nb)] for _ in range(nb)) / nb
        diffs.append(sa - sb)
    diffs.sort()
    return diffs[int(0.025 * B)], diffs[int(0.975 * B)]


def main():
    with open(RAW, encoding="utf-8") as fh:
        res = json.load(fh)["result"]
    set2, set3 = res["set2"], res["set3"]
    # Set1 (B4) Opus-self
    s1 = []
    for rp in B4RAWS:
        with open(rp, encoding="utf-8") as fh:
            for r in json.load(fh)["result"]["ids"]:
                if r["judge"] == "opus" and r["role"] == "self": s1.append(r)
    os.makedirs(OUT, exist_ok=True)
    for nm, S in [("set2", set2), ("set3", set3)]:
        for kind in ["genuine", "forged", "ids"]:
            for i, r in enumerate(S[kind]):
                json.dump(r, open(os.path.join(OUT, f"{nm}__{kind}__{i:03d}.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"B3': Set2 {len(set2['ids'])} ids, Set3 {len(set3['ids'])} ids; Set1(B4) opus-self n={len(s1)} acc={acc(s1):.3f}\n")

    # ---- length-match audit ----
    print("############ LENGTH-MATCH AUDIT (must pass before trusting judges) ############")
    for nm, S in [("Set2 (Sonnet->Haiku)", set2), ("Set3 (Opus->Sonnet)", set3)]:
        gw = {g["prompt_id"]: g["n_words"] for g in S["genuine"]}
        fw = {f["prompt_id"]: f["n_words"] for f in S["forged"]}
        ks = [k for k in gw if k in fw]
        ratios = sorted(fw[k] / gw[k] for k in ks)
        within = sum(1 for k in ks if 0.9 * gw[k] <= fw[k] <= 1.1 * gw[k]) / len(ks)
        mg = sum(gw[k] for k in ks) / len(ks); mf = sum(fw[k] for k in ks) / len(ks)
        print(f"  {nm}: genuine {mg:.0f}w / forged {mf:.0f}w; median ratio {ratios[len(ratios)//2]:.2f}; within +/-10%: {within:.0%}")

    # ---- harness-leak audit on GENUINE texts (Set2 Haiku is the suspect) ----
    LEAK = ["david", "claude.md", "claude code", "subagent", "structuredoutput", "structured output",
            "self-recognition", "self recognition", "spawned", " mcp", "workflow", "your research",
            "memory file", "these instructions", "the instruction", "you've set up", "ChromeMCP".lower()]
    def leaked_ids(genlist):
        s = set()
        for g in genlist:
            t = g["text"].lower()
            if any(tok in t for tok in LEAK): s.add(g["prompt_id"])
        return s
    leak2 = leaked_ids(set2["genuine"]); leak3 = leaked_ids(set3["genuine"])
    print("\n############ HARNESS-LEAK AUDIT (genuine texts) ############")
    print(f"  Set2 genuine-Haiku: {len(leak2)}/{len(set2['genuine'])} flagged ({len(leak2)/len(set2['genuine']):.0%}) — e.g. {sorted(leak2)[:6]}")
    print(f"  Set3 genuine-Sonnet: {len(leak3)}/{len(set3['genuine'])} flagged ({len(leak3)/len(set3['genuine']):.0%})")

    # ---- per-set per-judge accuracy ----
    print("\n############ PICK THE GENUINE [target] (chance 0.50) ############")
    for nm, S, tgt in [("Set2", set2, "Haiku"), ("Set3", set3, "Sonnet")]:
        print(f"  {nm} (genuine {tgt}):")
        for r0 in (["opus", "haiku", "sonnet"] if nm == "Set2" else ["sonnet", "haiku", "opus"]):
            rows = [r for r in S["ids"] if r["judge"] == r0]
            role = rows[0]["role"] if rows else "?"
            k = sum(1 for r in rows if r["correct"]); n = len(rows)
            print(f"    {r0:7s} [{role:7s}] {k}/{n}={k/n:.3f}  d'={dprime(k/n):+.2f}  p={binom_p(k,n):.4g}")

    # ---- PRIMARY ----
    print("\n############ PRIMARY — Opus-self(Set1) vs Opus-neutral(Set2) ############")
    a = [1 if r["correct"] else 0 for r in s1]                                  # opus-self (Set1)
    b = [1 if r["correct"] else 0 for r in set2["ids"] if r["judge"] == "opus"]  # opus-neutral (Set2)
    diff = acc(s1) - acc([r for r in set2["ids"] if r["judge"] == "opus"])
    lo, hi = boot_diff_ci(a, b)
    print(f"  Opus-self(Set1) {acc(s1):.3f} (n={len(a)})  vs  Opus-neutral(Set2) {sum(b)/len(b):.3f} (n={len(b)})")
    print(f"  difference (self - neutral) = {diff:+.3f}   bootstrap 95% CI [{lo:+.3f}, {hi:+.3f}]")
    if lo <= 0 <= hi:
        print("  -> VERDICT: CI brackets 0 -> CAPABILITY ACCOUNT CONFIRMED (predicted): the B4 author edge")
        print("     is generic forgery-detection capability; central null extends to the forgery paradigm.")
    elif lo > 0:
        print("  -> VERDICT: CI excludes 0 (self > neutral) -> RESIDUAL SELF-FAMILIARITY (scoped, bounded positive).")
    else:
        print("  -> VERDICT: CI excludes 0 (neutral > self) -> unexpected; inspect (target-distinctiveness caveat).")

    # ---- leak-excluded primary (de-contaminate Set2) ----
    print("\n############ PRIMARY, LEAK-EXCLUDED (drop Set2 prompts whose genuine-Haiku leaks harness) ############")
    b_clean = [1 if r["correct"] else 0 for r in set2["ids"] if r["judge"] == "opus" and r["prompt_id"] not in leak2]
    if b_clean:
        diff_c = acc(s1) - (sum(b_clean) / len(b_clean))
        lo2, hi2 = boot_diff_ci(a, b_clean)
        print(f"  Opus-self(Set1) {acc(s1):.3f}  vs  Opus-neutral(Set2, clean) {sum(b_clean)/len(b_clean):.3f} (n={len(b_clean)} of 80)")
        print(f"  difference = {diff_c:+.3f}  bootstrap 95% CI [{lo2:+.3f}, {hi2:+.3f}]")
        print(f"  (if Set2 genuine-Haiku is mostly leaked, n is small here and the primary is UNINTERPRETABLE -> corpus halt)")

    # ---- secondaries ----
    print("\n############ SECONDARIES (pre-specified) ############")
    # forger self-bias x capability: Opus-forger(Set3) vs Sonnet-forger(Set1=0.287)
    of = [r for r in set3["ids"] if r["judge"] == "opus"]  # Opus is forger in Set3
    print(f"  forger self-bias: Opus-as-forger(Set3) picks genuine {acc(of):.3f} (n={len(of)}); Sonnet-as-forger(Set1) was 0.287.")
    print(f"    (prediction: caricature preference attenuates with forger capability -> Opus-forger > 0.287)")
    # weak-author: Haiku-self on Set2
    hs = [r for r in set2["ids"] if r["judge"] == "haiku"]
    print(f"  weak-author: Haiku-self(Set2) {acc(hs):.3f} (n={len(hs)}, p={binom_p(sum(1 for r in hs if r['correct']),len(hs)):.3g})  (prediction: ~chance)")
    # second author-edge estimate: Sonnet-self vs Haiku-neutral on Set3
    ss = [r for r in set3["ids"] if r["judge"] == "sonnet"]; hn = [r for r in set3["ids"] if r["judge"] == "haiku"]
    print(f"  2nd author-edge (Set3, smaller capability gap): Sonnet-self {acc(ss):.3f} vs Haiku-neutral {acc(hn):.3f} = {acc(ss)-acc(hn):+.3f}")

    # ---- audits ----
    print("\n############ AUDITS ############")
    for nm, S in [("Set2", set2), ("Set3", set3)]:
        gw = {g["prompt_id"]: g["n_words"] for g in S["genuine"]}; fw = {f["prompt_id"]: f["n_words"] for f in S["forged"]}
        cl = d = 0
        for r in S["ids"]:
            g, f = gw.get(r["prompt_id"]), fw.get(r["prompt_id"])
            if g == f: continue
            d += 1; gl = g > f
            if (r["correct"] and gl) or ((not r["correct"]) and (not gl)): cl += 1
        posA = sum(1 for r in S["ids"] if r["genuine_position"] == "A")
        print(f"  {nm}: chose-longer {cl}/{d}={cl/d:.3f} (~0.5); genuine-in-A {posA}/{len(S['ids'])}={posA/len(S['ids']):.2f}")

    print("\n############ CALIBRATION (exploratory) ############")
    for nm, S in [("Set2", set2), ("Set3", set3)]:
        for r0 in ["opus", "sonnet", "haiku"]:
            rows = [r for r in S["ids"] if r["judge"] == r0 and r.get("confidence") is not None]
            if not rows: continue
            cor = [r["confidence"] for r in rows if r["correct"]]; inc = [r["confidence"] for r in rows if not r["correct"]]
            mc = sum(cor)/len(cor) if cor else float("nan"); mi = sum(inc)/len(inc) if inc else float("nan")
            print(f"  {nm} {r0:7s} gap={mc-mi:+.3f} (correct {mc:.2f} / wrong {mi:.2f})")


if __name__ == "__main__":
    main()
