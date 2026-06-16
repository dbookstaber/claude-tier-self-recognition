"""Process the workflow output: write per-record files, manifest, and print stats."""
import json
import os
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUTFILE = os.path.join(ROOT, "logs", "raw_workflow_output.json")

TIERS = ["opus", "sonnet", "haiku"]
TS = "2026-06-01T00:00:00Z"  # workflow scripts can't read clock; stamp at processing time


def main():
    with open(OUTFILE, encoding="utf-8") as fh:
        blob = json.load(fh)
    res = blob["result"]
    corpus = res["corpus"]
    ids = res["identifications"]

    # ---- write corpus files ----
    cdir = os.path.join(ROOT, "corpus")
    for c in corpus:
        rec = dict(c)
        rec["temperature"] = "harness-default"
        rec["timestamp"] = TS
        with open(os.path.join(cdir, rec["target_id"] + ".json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2, ensure_ascii=False)

    # ---- write identification files ----
    idir = os.path.join(ROOT, "identifications")
    for r in ids:
        r = dict(r)
        r["timestamp"] = TS
        fname = f"{r['target_id']}__{r['identifier']}__{r['framing']}__{r['length_label']}.json"
        with open(os.path.join(idir, fname), "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=2, ensure_ascii=False)

    # ---- manifest ----
    manifest = {
        "timestamp": TS,
        "n_generations": len(corpus),
        "n_identifications": len(ids),
        "generators": TIERS, "judges": TIERS,
        "framings": sorted({r["framing"] for r in ids}),
        "lengths": sorted({r["length_label"] for r in ids}),
    }
    with open(os.path.join(ROOT, "logs", "run_manifest__2026-06-01.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"Wrote {len(corpus)} corpus + {len(ids)} identification files.\n")

    # ---- corpus length sanity (length confound check) ----
    print("=== mean words per generated response, by tier x task ===")
    wl = defaultdict(list)
    for c in corpus:
        wl[(c["generator_label"], c["task"])].append(c["n_words"])
    print(f"  {'tier':8s} " + " ".join(f"{t:>9s}" for t in ["math", "summary", "advice"]))
    for tier in TIERS:
        row = [wl[(tier, tk)] for tk in ["math", "summary", "advice"]]
        print(f"  {tier:8s} " + " ".join(f"{(sum(x)/len(x)):9.0f}" if x else f"{'-':>9s}" for x in row))

    # ---- accuracy matrices per framing ----
    def acc_matrix(framing):
        cell = defaultdict(lambda: [0, 0])
        for r in ids:
            if r["framing"] != framing:
                continue
            k = (r["identifier"], r["target_generator"])
            cell[k][1] += 1
            cell[k][0] += int(bool(r["correct"]))
        return cell

    for framing in sorted({r["framing"] for r in ids}):
        print(f"\n=== accuracy: identifier (row) x target tier (col) | framing={framing} ===")
        print(f"  {'id\\tgt':10s} " + " ".join(f"{t:>10s}" for t in TIERS) + "    row_avg")
        cell = acc_matrix(framing)
        for ident in TIERS:
            cells = []
            tot_c = tot_n = 0
            for t in TIERS:
                c, n = cell[(ident, t)]
                tot_c += c; tot_n += n
                flag = "*" if ident == t else " "  # self-judge
                cells.append(f"{(c/n if n else 0):.2f}{flag}({c}/{n})")
            ravg = tot_c / tot_n if tot_n else 0
            print(f"  {ident:10s} " + " ".join(f"{x:>10s}" for x in cells) + f"   {ravg:.2f}")
        # column = target detectability
        print("  (* = self-judge cell, flagged for self-preference)")

    # ---- self vs cross-tier accuracy ----
    print("\n=== self-judge vs cross-judge accuracy (pooled over framings) ===")
    s_c = s_n = x_c = x_n = 0
    for r in ids:
        if r["is_self_judge"]:
            s_n += 1; s_c += int(bool(r["correct"]))
        else:
            x_n += 1; x_c += int(bool(r["correct"]))
    print(f"  self-judge:  {s_c}/{s_n} = {s_c/s_n:.2f}")
    print(f"  cross-judge: {x_c}/{x_n} = {x_c/x_n:.2f}")

    # ---- framing comparison ----
    print("\n=== overall accuracy by framing ===")
    fr = defaultdict(lambda: [0, 0])
    for r in ids:
        fr[r["framing"]][1] += 1
        fr[r["framing"]][0] += int(bool(r["correct"]))
    for f, (c, n) in sorted(fr.items()):
        print(f"  {f:14s} {c}/{n} = {c/n:.2f}")

    # ---- verdict distribution (where do wrong guesses go?) ----
    print("\n=== verdict_parsed distribution by true tier (pooled framings) ===")
    vd = defaultdict(Counter)
    for r in ids:
        vd[r["target_generator"]][r["verdict_parsed"]] += 1
    labels = ["opus", "sonnet", "haiku", "human", "distractor", "unknown"]
    print(f"  {'true\\guess':12s} " + " ".join(f"{l:>10s}" for l in labels))
    for t in TIERS:
        print(f"  {t:12s} " + " ".join(f"{vd[t][l]:>10d}" for l in labels))

    # ---- cue keyword tally ----
    print("\n=== cue keyword tally (REASON free-text) ===")
    kws = ["list", "bullet", "hedg", "verbose", "concise", "brief", "terse", "formal",
           "casual", "structur", "header", "emoji", "disclaim", "confiden", "tone",
           "length", "markdown", "step", "caveat", "latex", "notation", "format",
           "thorough", "succinct", "detail", "precise", "warm", "direct"]
    counts = Counter()
    for r in ids:
        reason = (r.get("reason") or "").lower()
        for kw in kws:
            if kw in reason:
                counts[kw] += 1
    for kw, n in counts.most_common(20):
        print(f"  {kw:12s} {n}")


if __name__ == "__main__":
    main()
