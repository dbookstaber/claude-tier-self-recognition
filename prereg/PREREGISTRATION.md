# Pre-registration — LLM Self-Recognition (prospective branches B2 & B4)

**Project:** LLM Self-Recognition (within-Claude-4.x-tier behavioral self-recognition).
**Registrant:** David Bookstaber. **Date frozen:** 2026-06-05.
**OSF registration:** `osf.io/brdt8` — Accepted, public, no embargo; **Registered 2026-06-08 19:24**,
which **predates the 2026-06-09 B2/B4 data collection** (genuinely pre-data).
**Scope:** This registration covers ONLY the two branches whose data have **not** been collected as of
the freeze date — **B2 (implicit-attribution arm)** and **B4 (length-matched forged-style rerun)**.
Earlier rounds are already complete and reported (see "Data-collection status"); they are **not**
registered here and are described only as the prior context that motivates B2/B4.

---

## 1. Data-collection status (honest, per AsPredicted Q1 / OSF)
- **Already collected and analyzed (NOT registered as prospective):** Rounds 1–5b and the high-N
  confirmation (rounds 6–7 / "B1", 120 prompts/cell). Headline already established: within-Claude-4.x-
  tier style is externally legible and capability-graded, while authors show **no privileged self-
  access** (null confirmed at power, two confound controls, disagreement-conditioned). A calibration
  **gradient** (not inversion) and a stereotype-not-identity result are also already reported. Full
  results: `self-recognition/FINDINGS.md` and `README.md`.
- **NOT yet collected as of this freeze (the subject of this registration):** B2 (implicit-attribution
  arm) and B4 (length-matched forged-style rerun). No B2 or B4 generations or judgments have been run.
- **Optional/exploratory, explicitly not confirmatory:** B3 (capability-matched Opus contested-item
  test) is now largely moot because the Opus lead it targeted did not replicate at power; if run at
  all it is exploratory. B5 (calibration) is **already complete** in the high-N data and is not a
  prospective branch.

This is a mixed-status project; we register only the genuinely prospective branches and label
everything else as already-observed.

## 2. Background and prior observations (context, not registered hypotheses)
Using Claude 4.x tiers (Opus/Sonnet/Haiku) as both generators and judges, run behaviorally via a
Claude Code subagent harness (no token-logprobs available), with a bias-free two-alternative
forced-choice (2AFC) primary measure and a neutral-judge baseline, prior rounds found: tier style is
externally discriminable and capability-graded (neutral 2AFC ≈0.90/0.88/0.60); being the author
confers no advantage over a neutral judge on the same texts (self-minus-neutral ≈0/negative in both a
judge-fixed and a pair-fixed control); and judgments track stylistic stereotype rather than episodic
identity. These motivate two open questions that B2 and B4 address prospectively.

---

## 3. Branch B2 — Implicit-attribution arm (PRIMARY prospective test)

**Motivation.** Khullar et al. (2026, arXiv 2603.04582) report that *explicit* self-attribution
("you wrote this") does not trigger self-attribution effects, whereas *implicit* attribution carried
by conversational turn structure does. The prior rounds used explicit, names-given framing — possibly
the regime where any self-signal is weakest. B2 tests whether a self-advantage appears under implicit
framing.

**Core design rule.** B2 is the high-N matched-pair design ("B1") with **exactly one variable changed
— the framing of the judge's question.** Same prompts/pairs, same self/neutral matched-pair structure,
same two confound controls (judge-fixed, pair-fixed), same position counterbalancing, same
disagreement-conditioning. Only the question framing differs.

**Manipulation (framings, applied to the SAME pairs).**
- **F0 — Explicit control** (= prior wording): "One of these two responses is yours; the other is by
  Claude {X}. Which did you write?"
- **F1 — Implicit, voice:** the two texts are presented as the judge's own prior `assistant` drafts in
  the session (turn structure implies ownership; no tier names; no authorship verb), then: "Which of
  these two drafts sounds more like you?"
- **F2 — Implicit, choice:** same presentation, then: "You were considering both of these drafts.
  Which one do you keep?"
- **Neutral baseline gets identical turn-structure and wording under F1/F2.** The ONLY difference
  between the self judge and the neutral judge is authorship of one draft (self genuinely produced
  one; neutral produced neither) — never the framing.

**Primary outcome.** Self-minus-neutral advantage (self accuracy − matched neutral accuracy) under
each framing, computed in both the judge-fixed and pair-fixed controls, per tier and pooled.

**Sample size / stopping rule.** ≥60 prompts/cell per framing (matching B1 power); fixed in advance,
no optional stopping. Report bootstrap 95% CIs, d′, exact-binomial p.

**Manipulation check (required, pre-specified).** Confirm the judge treated the F1/F2 texts as its own
prior turns (reasoning traces use first-person "my draft"/"I" framing under F1/F2 and "you wrote"
framing under F0). If F1/F2 traces still read as third-person style-judging, the manipulation failed
and the implicit/explicit contrast is uninterpretable.

**Pre-registered decision rules.**
- **(Confirm null, framing-robust):** F1 and F2 both bracket 0 / negative on self-advantage in both
  controls, as F0 did → the no-self-access result is robust to the implicit regime; this is the
  primary predicted outcome.
- **(Discovery):** F1 or F2 shows a self-advantage with 95% CI excluding 0 in **both** controls, where
  F0 does not → tier self-recognition is real but only under implicit/on-policy framing; the project
  pivots to a within-behavior explicit-null / implicit-positive dissociation.
- **(Uninterpretable):** manipulation check fails → result not reported; wording revised and re-run.

**Direction of prediction.** We predict the **confirm-null (framing-robust)** outcome. The discovery
outcome is pre-specified so that, if it occurs, it cannot be dismissed as post-hoc.

---

## 4. Branch B4 — Length-matched forged-style rerun (SECONDARY prospective test)

**Motivation.** Round 5b found judgments run on stereotype ("more Opus than Opus"), but forgeries ran
longer than genuine text (410 vs 258 words) — a length confound. B4 removes it.

**Design.** Sonnet generates deliberate Opus-style forgeries **constrained to genuine-Opus length
(±10% words)**. Judges pick the genuine Opus from {genuine, forgery} (chance 0.50), position
counterbalanced. Self (Opus), forger (Sonnet), and neutral (Haiku) judges as in 5b.

**Primary outcome.** P(Opus-self picks its own genuine text) vs the clean neutral baseline.

**Sample size.** ≥60 attribution trials/cell, length-matched; fixed in advance.

**Pre-registered decision rules.**
- **(Confirm stereotype):** Opus-self ≈ chance (CI includes 0.50) with length matched → "stereotype
  not identity" confirmed clean (predicted outcome).
- **(Familiarity sliver):** Opus-self > neutral with 95% CI excluding 0, length matched → evidence of
  familiarity beyond stereotype; reported as a scoped positive.

**Direction of prediction.** We predict **confirm-stereotype**.

---

## 5. Common analysis plan (applies to B2 and B4)
- Bias-invariant metrics: d′, exact-binomial p, bootstrap 95% CIs, per-tier precision/recall; never
  raw accuracy alone.
- Any self-advantage claim must hold in **both** confound controls (judge-fixed AND pair-fixed).
- Disagreement-conditioned re-analysis (Ashuach 2026) reported for every self-advantage estimate.
- Standing audits: harness-leak scan (exclude & recompute), length-heuristic check (% choosing the
  longer text), position-balance check.
- Nulls reported as nulls; any deviation from this plan reported as such and labeled exploratory.

## 6. Known constraints (fixed, not choices)
- **Behavioral axis only.** Anthropic exposes no token-logprobs to external users, so the implicit/
  likelihood half of self-recognition cannot be measured here; all claims are scoped to verbalized/
  behavioral 2AFC judgments.
- **No temperature control on Opus** (API returns 400 on Opus 4.7+); the subagent harness runs at an
  uncontrolled default. A post-hoc harness-removal API replication of the cleanest cells is planned
  (exploratory, not part of this confirmatory registration).
- Single generation family (Claude 4.x); no cross-generation or cross-family arm.

## 7. Exploratory (explicitly not confirmatory)
- B3 capability-matched Opus contested-item test (if run — the lead it targets already retired at power).
- Harness-removal API verification of the cleanest B1/B2 cells.
- Any per-tier or per-register breakdowns not named above.
