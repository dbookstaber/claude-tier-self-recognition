"""Round 5a — matched-pair self-advantage, two confound-controlled ways:
  judge-fixed: same judge, pairs it is IN (self) vs the pair it is OUT of (neutral)
  pair-fixed:  same texts, member judges (self) vs outsider judge (neutral)
Names-equalized framing on all trials."""
import json, os, math
from collections import defaultdict
from statistics import NormalDist
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
RAW = os.path.join(ROOT, "logs", "raw_round5a_output.json"); R5 = os.path.join(ROOT, "round5a")
TIERS = ["opus", "sonnet", "haiku"]; Z = NormalDist()


def binom_p(k, n, p=0.5):
    from math import comb
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    o = pmf(k); return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= o + 1e-12))


def dprime(pc): pc = min(max(pc, 1e-6), 1 - 1e-6); return math.sqrt(2) * Z.inv_cdf(pc)


def ztest(k1, n1, k2, n2):
    if not n1 or not n2: return 0, 1
    p1, p2 = k1 / n1, k2 / n2; p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0: return 0, 1
    z = (p1 - p2) / se; return z, 2 * (1 - Z.cdf(abs(z)))


def acc(rows): k = sum(1 for r in rows if r["correct"]); return k, len(rows)


def main():
    with open(RAW, encoding="utf-8") as fh: res = json.load(fh)["result"]
    corpus, ids = res["corpus"], res["ids"]
    os.makedirs(os.path.join(R5, "corpus"), exist_ok=True); os.makedirs(os.path.join(R5, "ids"), exist_ok=True)
    for c in corpus: json.dump(c, open(os.path.join(R5, "corpus", f"{c['prompt_id']}__{c['generator_label']}.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    for i, r in enumerate(ids): json.dump(r, open(os.path.join(R5, "ids", f"{r['prompt_id']}__{r['judge']}__{r['pair'][0]}v{r['pair'][1]}__{r['role']}.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Wrote {len(corpus)} corpus + {len(ids)} id files.\n")

    print("############ (pair x judge) accuracy cells ############")
    for pr in [["opus", "sonnet"], ["opus", "haiku"], ["sonnet", "haiku"]]:
        print(f"  pair {pr[0]} vs {pr[1]}:")
        for j in TIERS:
            rows = [r for r in ids if r["pair"] == pr and r["judge"] == j]
            if not rows: continue
            k, n = acc(rows); role = rows[0]["role"]
            print(f"    judge={j:7s} [{role:7s}] {k:2d}/{n:2d} = {k/n:.3f}")

    print("\n############ CONTRAST 1 — JUDGE-FIXED (controls judge capability) ############")
    print("  each judge: accuracy on pairs it is IN (self) vs the pair it is OUT of (neutral)")
    for j in TIERS:
        s = [r for r in ids if r["judge"] == j and r["role"] == "self"]
        nt = [r for r in ids if r["judge"] == j and r["role"] == "neutral"]
        sk, sn = acc(s); nk, nn = acc(nt); z, pv = ztest(sk, sn, nk, nn)
        print(f"  {j:7s} self {sk:3d}/{sn:3d}={sk/sn:.3f}  neutral(out) {nk:2d}/{nn:2d}={nk/nn:.3f}  adv={sk/sn-nk/nn:+.3f} (z={z:+.2f},p={pv:.3f})")

    print("\n############ CONTRAST 2 — PAIR-FIXED (controls texts/difficulty) ############")
    print("  each pair: member judges (self) vs the outsider judge (neutral), same texts")
    tot_s = [0, 0]; tot_n = [0, 0]
    for pr in [["opus", "sonnet"], ["opus", "haiku"], ["sonnet", "haiku"]]:
        s = [r for r in ids if r["pair"] == pr and r["role"] == "self"]
        nt = [r for r in ids if r["pair"] == pr and r["role"] == "neutral"]
        sk, sn = acc(s); nk, nn = acc(nt); tot_s[0]+=sk; tot_s[1]+=sn; tot_n[0]+=nk; tot_n[1]+=nn
        print(f"  {pr[0]} vs {pr[1]:7s}: members {sk:3d}/{sn:3d}={sk/sn:.3f}  outsider {nk:2d}/{nn:2d}={nk/nn:.3f}  adv={sk/sn-nk/nn:+.3f}")
    z, pv = ztest(tot_s[0], tot_s[1], tot_n[0], tot_n[1])
    print(f"  POOLED: self {tot_s[0]}/{tot_s[1]}={tot_s[0]/tot_s[1]:.3f}  neutral {tot_n[0]}/{tot_n[1]}={tot_n[0]/tot_n[1]:.3f}  adv={tot_s[0]/tot_s[1]-tot_n[0]/tot_n[1]:+.3f} (z={z:+.2f},p={pv:.3f})")

    print("\n############ self-2AFC by judge (replication, names-given) ############")
    for j in TIERS:
        s = [r for r in ids if r["judge"] == j and r["role"] == "self"]; k, n = acc(s)
        print(f"  {j:7s} {k}/{n}={k/n:.3f} d'={dprime(k/n):+.2f} p={binom_p(k,n):.4f}")

    print("\n############ calibration (self trials) ############")
    for j in TIERS:
        rows = [r for r in ids if r["judge"] == j and r["role"] == "self" and r.get("confidence") is not None]
        cor = [r["confidence"] for r in rows if r["correct"]]; inc = [r["confidence"] for r in rows if not r["correct"]]
        mc = sum(cor)/len(cor) if cor else float('nan'); mi = sum(inc)/len(inc) if inc else float('nan')
        br = sum((r["confidence"]-(1 if r["correct"] else 0))**2 for r in rows)/len(rows) if rows else float('nan')
        print(f"  {j:7s} conf correct={mc:.2f} wrong={mi:.2f} gap={mc-mi:+.2f} Brier={br:.3f}")


if __name__ == "__main__":
    main()
