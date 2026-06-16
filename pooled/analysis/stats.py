"""Bias-invariant stats on the round-1 identifications: kappa, balanced accuracy,
per-tier precision/recall, and a label-permutation null for accuracy."""
import json, glob, os, random
from collections import defaultdict, Counter

random.seed(20260603)
HERE = os.path.dirname(os.path.abspath(__file__))
IDDIR = os.path.join(HERE, "..", "identifications")
TIERS = ["opus", "sonnet", "haiku"]
CATS = ["opus", "sonnet", "haiku", "human", "distractor", "unknown"]


def load():
    recs = []
    for f in glob.glob(os.path.join(IDDIR, "*.json")):
        with open(f, encoding="utf-8") as fh:
            recs.append(json.load(fh))
    return recs


def cohen_kappa(true, pred, cats):
    n = len(true)
    obs = sum(1 for t, p in zip(true, pred) if t == p) / n
    tc = Counter(true); pc = Counter(pred)
    exp = sum((tc[c] / n) * (pc[c] / n) for c in cats)
    return (obs - exp) / (1 - exp) if (1 - exp) else 0.0


def per_tier_pr(true, pred):
    out = {}
    for t in TIERS:
        tp = sum(1 for a, b in zip(true, pred) if a == t and b == t)
        fp = sum(1 for a, b in zip(true, pred) if a != t and b == t)
        fn = sum(1 for a, b in zip(true, pred) if a == t and b != t)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        out[t] = (prec, rec, f1)
    return out


def perm_test(true, pred, reps=20000):
    obs = sum(1 for t, p in zip(true, pred) if t == p)
    n = len(true)
    shuffled = list(true)
    ge = 0
    null_max = 0
    for _ in range(reps):
        random.shuffle(shuffled)
        c = sum(1 for t, p in zip(shuffled, pred) if t == p)
        if c >= obs:
            ge += 1
        null_max = max(null_max, c)
    return obs, n, (ge + 1) / (reps + 1), null_max


def analyze(recs, tag):
    true = [r["target_generator"] for r in recs]
    pred = [r["verdict_parsed"] for r in recs]
    print(f"\n############ {tag}  (n={len(recs)}) ############")
    acc = sum(1 for t, p in zip(true, pred) if t == p) / len(recs)
    bal = sum(per_tier_pr(true, pred)[t][1] for t in TIERS) / 3
    k = cohen_kappa(true, pred, CATS)
    print(f"  raw accuracy      = {acc:.3f}   (tier-chance ~0.333)")
    print(f"  balanced accuracy = {bal:.3f}   (mean per-tier recall)")
    print(f"  Cohen's kappa     = {k:+.3f}   (0 = chance agreement)")
    print("  per-tier  precision  recall   f1   support")
    pr = per_tier_pr(true, pred)
    for t in TIERS:
        sup = sum(1 for x in true if x == t)
        p, r, f = pr[t]
        print(f"    {t:8s}   {p:5.2f}    {r:5.2f}  {f:5.2f}    {sup}")
    obs, n, pval, nmax = perm_test(true, pred)
    print(f"  permutation null: observed {obs}/{n} correct; "
          f"p(acc>=obs | labels shuffled) = {pval:.4f}; max-null={nmax}/{n}")


def main():
    recs = load()
    analyze(recs, "POOLED (both framings)")
    for fr in sorted({r["framing"] for r in recs}):
        analyze([r for r in recs if r["framing"] == fr], f"framing={fr}")
    # per-task breakdown — tests the "convergent tasks carry no tier signal" hypothesis
    print("\n############ per-task (pooled framings) ############")
    for tk in ["math", "summary", "advice"]:
        sub = [r for r in recs if r["target_id"].startswith(tk + "__")]
        t = [r["target_generator"] for r in sub]; p = [r["verdict_parsed"] for r in sub]
        acc = sum(1 for a, b in zip(t, p) if a == b) / len(sub)
        _, _, pv, _ = perm_test(t, p, reps=20000)
        print(f"  {tk:8s} n={len(sub):3d}  acc={acc:.3f}  kappa={cohen_kappa(t,p,CATS):+.3f}  perm_p={pv:.4f}")
    # self vs cross with a quick permutation on the pooled set
    print("\n############ self vs cross (pooled) ############")
    self_r = [r for r in recs if r["is_self_judge"]]
    cross_r = [r for r in recs if not r["is_self_judge"]]
    for sub, name in [(self_r, "self"), (cross_r, "cross")]:
        t = [r["target_generator"] for r in sub]; p = [r["verdict_parsed"] for r in sub]
        acc = sum(1 for a, b in zip(t, p) if a == b) / len(sub)
        print(f"  {name:5s} n={len(sub):3d}  acc={acc:.3f}  kappa={cohen_kappa(t,p,CATS):+.3f}")


if __name__ == "__main__":
    main()
