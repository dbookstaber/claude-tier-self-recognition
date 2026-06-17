# Tier Style Is Legible but Not Self-Known

**A Behavioral Boundary on Within-Family Self-Recognition in Claude 4.x**

Code and data accompanying the paper. This repository lets you re-derive every headline
number and regenerate every figure from the raw judgment logs.

> Paper: *forthcoming* (arXiv link to be added on posting).
> Archived release / DOI: *to be added after the first tagged release (Zenodo).*

---

## What this is

We ask a narrow question the self-recognition literature has not isolated: when two
capability tiers of the *same* model family (Claude 4.x — Opus, Sonnet, Haiku) each write
open-ended prose, can a tier behaviorally recognize its own writing among a sibling's,
**beyond what a neutral third-party judge of equal or lower compute** achieves on the
identical texts? We test this with forced-choice (2AFC) experiments, two independent
confound controls, framing variation, a disagreement-conditioned reanalysis, and a
raw-API replication.

**The four-part result:**

1. **Tier style is externally legible, and legibility is capability-graded.** Neutral
   judges discriminate authorship at Opus ≈ 0.91, Sonnet ≈ 0.90, Haiku ≈ 0.63 (chance
   0.50) — yet **being the author confers no advantage**: the self-minus-neutral advantage
   is negative or brackets zero for every tier under both controls.
2. **The agent harness amplifies tier distinctiveness at *generation*, not judgment** — a
   fully-crossed 2×2 locates the effect in the text source, and it is largest for the
   closest tier pair.
3. **Attribution runs on stereotype, not identity** — a stronger model's length-matched
   caricature of a weaker tier is judged more authentic than the genuine article, even by
   the author.
4. **Identity-judgment calibration follows a capability gradient**, with the weakest tier
   mildly anti-calibrated.

Together these place a **behavioral scope boundary** on emergent-introspection claims:
privileged access, even where it is real for this family, does not extend to behavioral
recognition of one's own prose authorship among tiers.

---

## Repository layout

```
runner/            Byte-faithful experiment scripts (JS) run inside the Claude Code
                   Workflow harness — the verbatim originals (see Provenance).
logs/              Pass-1 raw per-round judgment records.
run2/logs/         Pass-2 raw records (independent replication of pass 1).
pooled/logs/       The two passes pooled to 2x n — the AUTHORITATIVE dataset.
analysis/          Analysis scripts. Run from here they read logs/ (pass 1).
pooled/analysis/   The SAME scripts; run from here they read pooled/logs/ (authoritative).
interviews/        A-priori subject interviews (logs/raw_interviews.json) + attestation.
data/              Clean-room attestations, manifests, defect log, Phase-0 leak corpus.
run2/data/         Pass-2 attestations + manifests.
reference/         Methods: EXPERIMENT_DETAILS_verbatim.md, prompts.md, schema.md,
                   configs_pilot.json, CLEAN_ROOM_VERIFICATION.md.
prereg/            The preregistration documents (canonical copies on OSF).
figures/           make_figures.py + the 6 figures (SVG + PNG) + figs_combined.pdf.
round5a/ round_b3p/ round_b4/
                   Intermediate corpora / 2AFC item files emitted by the analysis scripts.
```

The directory structure is preserved exactly as the experiment ran, so **every analysis
script runs in place with no edits** (paths resolve relative to each script's own
location). See *Reproduce*.

---

## Reproduce

**Environment.** Tested with **Python 3.13**. The analysis scripts use only the standard
library; the figure script needs `numpy` and `matplotlib`:

```
pip install numpy matplotlib
```

The `runner/*.js` scripts are the verbatim experiment scripts as they ran **inside the
Claude Code Workflow harness**; they are included for transparency and are *not* a
standalone Node program. The published numbers are reproduced from the included logs by
the Python analysis below. (The harness arms are not version-pinnable; the raw-API arm
called pinned model ids — see `reference/EXPERIMENT_DETAILS_verbatim.md`.)

**Authoritative (pooled, 2-pass) results** — run from the repository root:

| Command | Reproduces | Expected headline |
|---|---|---|
| `python pooled/analysis/round_pooled_B1.py` | Self-advantage (B1) + calibration | judge-fixed **Opus −0.090 [−0.131,−0.046]**, Sonnet −0.277 [−0.327,−0.229], Haiku −0.035 [−0.110,+0.042]; **pair-fixed pooled −0.134 [−0.160,−0.106]**; calibration gap **+0.091 / +0.030 / −0.012**, Brier 0.128 / 0.214 / 0.253 |
| `python pooled/analysis/round5a.py` | Positive control (matched-pair discrimination) | neutral cells ≈ **0.90–0.91** for the Opus/Sonnet-judged pairs; Haiku ≈ 0.63 |
| `python pooled/analysis/round_B4.py` | Forgery paradigm (B4) | **Opus-self 0.725**, Sonnet-forger (neutral) **0.188**; length-matched "familiarity sliver" |
| `python pooled/analysis/round_B3p.py` | Forgery extended (B3′) | Set2/Set3 genuine-vs-forgery cells (paper Fig 5) |
| `python pooled/analysis/round_B2.py` | Framing (F0/F1/F2) | F1/F2 ≈ F0: framing-robust null |
| `python pooled/analysis/reason_coding.py` | Reason-code analysis (pools both passes + interviews) | per-tier mechanics/wit/warmth rates |

Run the same scripts from `analysis/` (instead of `pooled/analysis/`) to reproduce the
**pass-1-only** numbers. `reason_coding.py` reads `logs/`, `run2/logs/`, and
`interviews/logs/` relative to the current directory, so run it from the repository root.


**Figures:**

```
python figures/make_figures.py
```

Writes 6 figures as SVG + PNG plus `figs_combined.pdf`. All figure values
are the paper's authoritative numbers, hard-coded in the script — nothing is re-derived or invented there.


---

## Data dictionary

Each `logs/raw_*.json` file is `{"result": <the script's returned object>}`; the analysis
scripts read `json.load(f)["result"]`. A result holds `corpus` (generation records) and `ids`
(2AFC identification records); each identification record carries `prompt_id, task, pair, judge,
role, in_pair, target_tier, target_position, choice, confidence, correct, reason, tX_words,
tY_words`. The verbatim record formats and the prompt strings are in
[`reference/EXPERIMENT_DETAILS_verbatim.md`](reference/EXPERIMENT_DETAILS_verbatim.md).
(`reference/schema.md` and `reference/prompts.md` describe the earlier *pilot* identification
format and are kept for historical reference.) Per-arm counts, expected-vs-actual cell totals, and
provenance are in `data/_manifest.json` (pass 1) and `run2/data/_manifest.json` (pass 2).

---

## Provenance

**Two data generations exist; only the clean re-run is authoritative.** The *original*
harness runs were contaminated: spawned subagents inherited the experimenter's project
configuration (personal writing/communication preferences) and an auto-memory naming the
hypothesis, and some judge traces reasoned from that leaked context. The experiment was
rebuilt **byte-faithfully** and re-run in a **verified clean room over two independent
passes, pooled to 2× n**. **The clean 2-pass re-run is the authoritative dataset.** The
original (contaminated) arms are *superseded* and are not included here. The quantitative
clean-vs-original comparison is not reproducible from this repository (it requires the contaminated
data, which is not published); the decontamination is summarized in this section and discussed in
the paper. (As one example, the B4 "pick the genuine Opus" cell was 0.762 in the original run and
**0.725** in the clean pooled re-run; the preregistration and the verbatim `runner/` scripts cite
the pre-rerun 0.762, while the published figures and the analysis scripts use the clean 0.725.)

**Clean-room verification.** Before each pass, the run environment was audited
(`reference/CLEAN_ROOM_VERIFICATION.md`; attestations in `data/_clean_room_attestation.txt`,
`run2/data/_clean_room_attestation.txt`, `interviews/data/_attestation.txt`):

- **Channel A** — project-specific contamination (a project `CLAUDE.md`, auto-memory,
  persona, or the hypothesis tokens `david / bookstaber / self-recognition / introspection
  / …`) — was verified **absent** (filesystem checks up every parent directory + a context
  probe). Those exact detection tokens are preserved verbatim in the attestations and
  defect logs so the check is auditable.
- **Channel B** — generic harness identity inherent to the environment (the working
  directory, an OS string, the user-email system field) — was **measured, not gated**:
  Haiku ≈ 10%, Sonnet ≈ 10%, Opus 0% of generations emitted some harness context
  (`data/_phase0_leak_samples.json` is the Phase-0 leak corpus). The downstream analysis
  scripts run a **leak audit** that excludes affected texts/judgments and recomputes, as in
  the original.

**What the Channel-B leak looks like in the data (left verbatim).** A small number of raw
records contain genuine leaked harness context — e.g. a generation noting *"a Windows 11
environment called `OneDrive\Documents\Claude\Research`"*; a few **judge-reasoning
traces** that used the leaked author email as a discrimination cue (*"the financial-risk
framing aligns with this user's context (<author-email>…)"*); and several **generations that
signed the prose with the author's first name** (*"…With love, David"*), which some judges in
turn reasoned from (*"the sign-off matches the user's name"*). (The leaked email is the
author's **public** correspondence address — the same one on the paper — and the first name is
likewise public; both are kept **verbatim** in the raw records and appear as `<author-email>`
in *this README* only by the documentation convention below.) These are **the
phenomenon the paper analyzes**; they are retained byte-for-byte in `logs/`, `run2/logs/`,
`pooled/logs/`, `pooled/round_b3p/`, and `data/_phase0_leak_samples.json`. Redacting them
would falsify the data **and** break the leak audit, which searches for these very strings.

**Redaction rule applied before publication.** A single deterministic rule was applied to
**incidental** machine paths in *code, documentation, manifests, and attestations only*
(never to the raw data, never to the method's detection-token lists):

| Original | Replacement |
|---|---|
| the working directory (`F:\…\Research`, `f:/…/Research`) | `<CWD>` (parents in the audit ladder → `<CWD>\..`, drive root → `<drive-root>`) |
| the user home dir (`C:\Users\<name>`) | `<HOME>` |
| the Claude project-slug | `<project-slug>` |
| the Claude task-output temp dir | `<CLAUDE_TASKS_DIR>` |
| full workflow-script provenance paths | the script basename only |
| the author email | `<author-email>` |
| hardcoded absolute paths in helper scripts | `__file__`-relative paths |

In addition, the clean-room **detection-token lists** (in the attestations,
`reference/CLEAN_ROOM_VERIFICATION.md`, and the Phase-0 audit) had the author's personal-config
*style phrases* generalized to a descriptor; the study/hypothesis tokens and the author name are
kept, as they are public. The operational agent run-guides used to drive the experiment were
omitted from this release — reproduction is via the *Reproduce* section above. The verbatim scripts
quoted in `reference/EXPERIMENT_DETAILS_verbatim.md` are the same scripts as in `runner/` (one
annotated with inline prompts and provenance, the other directly runnable).

**Scrub evidence.** After applying the rule, a grep for `C:\Users`, drive+`OneDrive`
paths, `AppData`, the project slug, the author email, and credential patterns
(`ANTHROPIC_API_KEY`, `sk-ant-`, …) over the assembled repository returns **no hits in
code, docs, manifests, or attestations**. The only remaining matches are (a) the raw data
records described above and (b) the clean-room detection-token lists — both intentional and
documented here. No API keys or credentials were present in the source or the assembled
repository.

---

## Preregistration

This study was preregistered on OSF: **[osf.io/brdt8](https://osf.io/brdt8)** (B2/B4
registered 2026-06-08) and **[osf.io/5azq8](https://osf.io/5azq8)** (B3 registered 2026-06-12). The OSF registration is canonical;
copies are mirrored in [`prereg/`](prereg/) for convenience.

---

## License

This repository is dual-licensed, following the common convention for paper-accompanying
artifacts:

- **Code** — the `runner/`, `analysis/`, `pooled/analysis/`, and `figures/*.py` scripts —
  under the **MIT License** ([`LICENSE`](LICENSE)).
- **Data and documentation** — the logs, attestations, manifests, inputs, reference
  methods, preregistrations, figures, and this README — under **Creative Commons
  Attribution 4.0 International (CC-BY-4.0)** ([`LICENSE-DATA`](LICENSE-DATA)).

---

## Citation

If you use this code or data, please cite the paper and this archive. Repository metadata
for citation managers is in [`CITATION.cff`](CITATION.cff); add the Zenodo DOI to your
citation once the first release is archived.
