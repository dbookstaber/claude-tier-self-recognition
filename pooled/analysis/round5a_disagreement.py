"""Round-5a re-analysis a la Ashuach et al. 2026 (Masked by Consensus).

Pooled self-advantage (self_acc - neutral_acc) was ~0/negative. Ashuach: that can be MASKED by
consensus items where a neutral judge rides public signal for free. Restrict to DISAGREEMENT items
(self-judge and that item's neutral judge attribute the pair differently) and ask who is right.

2AFC property: with 2 options, 'correct' fully determines the choice relative to truth, so
  self and neutral AGREE  <=>  self.correct == neutral.correct   (both picked the same text)
  self and neutral DISAGREE <=> self.correct != neutral.correct  (picked different texts; one right)
Hence on disagreement items, P(self correct) = self_acc there, and self-advantage = 2*P - 1.
  P > 0.5  => privileged self-knowledge masked by consensus (a discovery)
  P ~ 0.5  => null holds even on the hard, contested items (the null hardens)

Note on the neutral judge: in Round 5a the neutral judge for a pair is the third tier; its
'correct' flag is the pair resolution (correctly placing pair[0] <=> correctly placing pair[1] in
2AFC), so it serves as neutral_correct for BOTH members. Each item contributes two member
datapoints (one per member); the neutral flag is shared across them — a mild dependency, noted.
"""
import json, os, math
from collections import defaultdict
from statistics import NormalDist
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
RAW = os.path.join(ROOT, "logs", "raw_round5a_output.json")
TIERS = ["opus", "sonnet", "haiku"]; Z = NormalDist()


def binom_p(k, n, p=0.5):
    from math import comb
    if n == 0: return float("nan")
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    o = pmf(k); return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= o + 1e-12))


def main():
    with open(RAW, encoding="utf-8") as fh:
        ids = json.load(fh)["result"]["ids"]
    # group by item = (prompt_id, pair)
    items = defaultdict(dict)
    for r in ids:
        key = (r["prompt_id"], tuple(r["pair"]))
        if r["role"] == "neutral":
            items[key]["n"] = r
        else:  # self
            items[key].setdefault("self", {})[r["judge"]] = r

    # build member datapoints: (tier, self_correct, neutral_correct)
    pts = []  # list of dict(tier, s, n)
    for (pid, pair), rec in items.items():
        if "n" not in rec or "self" not in rec: continue
        X, Y = pair
        cn = bool(rec["n"]["correct"])
        if X in rec["self"]:
            pts.append({"tier": X, "s": bool(rec["self"][X]["correct"]), "n": cn})
        if Y in rec["self"]:
            pts.append({"tier": Y, "s": bool(rec["self"][Y]["correct"]), "n": cn})

    def block(name, P):
        n_all = len(P)
        if not n_all: print(f"  {name:9s}  (no data)"); return
        self_acc = sum(p["s"] for p in P) / n_all
        neut_acc = sum(p["n"] for p in P) / n_all
        agree = [p for p in P if p["s"] == p["n"]]
        disagree = [p for p in P if p["s"] != p["n"]]
        agree_rate = len(agree) / n_all
        # on agreement items, both same call; accuracy there:
        agree_acc = (sum(p["s"] for p in agree) / len(agree)) if agree else float("nan")
        # DISAGREEMENT subset: P(self correct)
        dk = sum(p["s"] for p in disagree); dn = len(disagree)
        dis_self = dk / dn if dn else float("nan")
        p = binom_p(dk, dn)
        adv_full = self_acc - neut_acc
        print(f"  {name:9s} full: self {self_acc:.3f} / neutral {neut_acc:.3f} (adv {adv_full:+.3f}) | "
              f"agree {agree_rate:.0%} (acc {agree_acc:.3f}) | "
              f"DISAGREE n={dn}: P(self right)={dis_self:.3f} (adv {2*dis_self-1:+.3f}, binom p={p:.4f})")

    print("############ DISAGREEMENT-CONDITIONED SELF-ADVANTAGE (Ashuach-style) ############")
    print("  (on disagreement items, P(self right)>0.5 => privileged self-knowledge masked by consensus)\n")
    block("ALL", pts)
    for t in TIERS:
        block(t, [p for p in pts if p["tier"] == t])

    # three-way consensus stratification (all three judges resolve the pair identically)
    print("\n############ THREE-WAY consensus vs split (robustness) ############")
    cons_pts, split_pts = [], []
    for (pid, pair), rec in items.items():
        if "n" not in rec or "self" not in rec: continue
        X, Y = pair
        if X not in rec["self"] or Y not in rec["self"]: continue
        cx, cy, cn = bool(rec["self"][X]["correct"]), bool(rec["self"][Y]["correct"]), bool(rec["n"]["correct"])
        consensus = (cx == cy == cn)
        for tier, s in [(X, cx), (Y, cy)]:
            (cons_pts if consensus else split_pts).append({"tier": tier, "s": s, "n": cn})
    print(f"  consensus items (all 3 judges resolve identically): {len(cons_pts)//2} of {len(items)}")
    print(f"  split items: {len(split_pts)//2} of {len(items)}")
    if split_pts:
        sa = sum(p["s"] for p in split_pts) / len(split_pts)
        na = sum(p["n"] for p in split_pts) / len(split_pts)
        print(f"  on SPLIT items: self {sa:.3f} / neutral {na:.3f}  advantage {sa-na:+.3f}")
    if cons_pts:
        sa = sum(p["s"] for p in cons_pts) / len(cons_pts)
        print(f"  on CONSENSUS items: self acc {sa:.3f} (ceiling check)")


if __name__ == "__main__":
    main()
