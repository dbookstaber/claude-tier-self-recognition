"""B4 (PLAN A4) — length-matched forged-style. Pick the genuine Opus from {genuine, Sonnet-forgery}.
Closes the R5b length confound. Decision rule: opus-self ~ chance (length matched) -> stereotype
not identity, clean; opus-self > clean neutral -> a familiarity sliver."""
import json, os, math, glob
from statistics import NormalDist
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
RAWS = sorted(glob.glob(os.path.join(ROOT, "logs", "raw_b4*_output.json"))); B4 = os.path.join(ROOT, "round_b4")
Z = NormalDist()


def binom_p(k, n, p=0.5):
    from math import comb
    if n == 0: return float("nan")
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    o = pmf(k); return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= o + 1e-12))


def ztest(k1, n1, k2, n2):
    if not n1 or not n2: return 0, 1
    p1, p2 = k1 / n1, k2 / n2; p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0: return 0, 1
    z = (p1 - p2) / se; return z, 2 * (1 - Z.cdf(abs(z)))


def main():
    genuine, forged, ids = [], [], []
    for rp in RAWS:
        with open(rp, encoding="utf-8") as fh:
            res = json.load(fh)["result"]
        genuine += res["genuine"]; forged += res["forged"]; ids += res["ids"]
    print(f"Pooled B4 over {len(RAWS)} batch(es): {[os.path.basename(r) for r in RAWS]}")
    os.makedirs(os.path.join(B4, "gens"), exist_ok=True); os.makedirs(os.path.join(B4, "ids"), exist_ok=True)
    for g in genuine: json.dump(g, open(os.path.join(B4, "gens", f"{g['prompt_id']}__genuine.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    for f in forged: json.dump(f, open(os.path.join(B4, "gens", f"{f['prompt_id']}__forged.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    for r in ids: json.dump(r, open(os.path.join(B4, "ids", f"{r['prompt_id']}__{r['judge']}.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Wrote {len(genuine)} genuine + {len(forged)} forged + {len(ids)} id files.\n")

    # ---- length-match audit (did the confound close?) ----
    gw = {g["prompt_id"]: g["n_words"] for g in genuine}
    fw = {f["prompt_id"]: f["n_words"] for f in forged}
    pairs = [(gw[k], fw[k]) for k in gw if k in fw]
    mg = sum(a for a, b in pairs) / len(pairs); mf = sum(b for a, b in pairs) / len(pairs)
    within = sum(1 for a, b in pairs if 0.9 * a <= b <= 1.1 * a) / len(pairs)
    ratios = sorted(b / a for a, b in pairs)
    med = ratios[len(ratios) // 2]
    print("############ LENGTH-MATCH AUDIT (vs R5b: genuine 258 / forged 410) ############")
    print(f"  genuine mean {mg:.0f} w; forged mean {mf:.0f} w; median forged/genuine ratio {med:.2f}; within +/-10%: {within:.0%}")

    # ---- pick the genuine Opus (chance 0.50) ----
    print("\n############ PICK THE GENUINE OPUS (chance 0.50) ############")
    res_by = {}
    for j in ["opus", "sonnet", "haiku"]:
        rows = [r for r in ids if r["judge"] == j]
        k = sum(1 for r in rows if r["correct"]); n = len(rows); res_by[j] = (k, n)
        role = rows[0]["role"] if rows else "?"
        print(f"  {j:7s} [{role:7s}] {k}/{n} = {k/n:.3f}  p={binom_p(k,n):.4g}")
    ok, on = res_by["opus"]
    print("\n  decisive contrasts:")
    for nj in ["haiku", "sonnet"]:
        nk, nn = res_by[nj]; z, pv = ztest(ok, on, nk, nn)
        tag = "CLEAN neutral" if nj == "haiku" else "forger (self-bias)"
        print(f"    opus-self {ok/on:.3f} vs {nj}-neutral {nk/nn:.3f} [{tag}]  adv={ok/on-nk/nn:+.3f} (z={z:+.2f}, p={pv:.3f})")

    # ---- length heuristic residual ----
    chose_longer = diff = 0
    for r in ids:
        g, f = gw.get(r["prompt_id"]), fw.get(r["prompt_id"])
        if g == f: continue
        diff += 1
        genuine_longer = g > f
        if (r["correct"] and genuine_longer) or ((not r["correct"]) and (not genuine_longer)): chose_longer += 1
    if diff: print(f"\n  length-heuristic residual: chose LONGER text {chose_longer}/{diff} = {chose_longer/diff:.3f} (~0.5 = neutralized)")

    print("\n############ DECISION RULE (PLAN A4) ############")
    p_self = binom_p(ok, on)
    z_h, pv_h = ztest(ok, on, *res_by["haiku"])
    if ok / on > 0.5 and p_self < 0.05 and res_by["haiku"][0] / res_by["haiku"][1] < ok / on and pv_h < 0.05:
        print("  -> opus-self > clean neutral with length matched: a FAMILIARITY SLIVER -> report alongside B3.")
    elif abs(ok / on - 0.5) < 0.15 or p_self >= 0.05:
        print("  -> opus-self ~ chance with length matched: STEREOTYPE-NOT-IDENTITY confirmed clean (R5b confound closed).")
    else:
        print("  -> ambiguous; inspect.")


if __name__ == "__main__":
    main()
