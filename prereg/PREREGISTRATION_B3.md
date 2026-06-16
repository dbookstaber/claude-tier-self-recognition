# Pre-registration amendment — Branch B3′ (capability-matched neutral for the forgery paradigm)

**Project:** LLM Self-Recognition (within-Claude-4.x-tier behavioral self-recognition).
**Registrant:** David Bookstaber. **Date frozen:** 2026-06-11.
**OSF registration:** registered from project `osf.io/zp2k4` — Accepted, public, no embargo;
**Registered 2026-06-12 06:21**, before any B3′ data collection (pre-data).
**Relation to prior registration:** amends/extends the 2026-06-05 registration (branches B2 & B4,
both since completed). B3′ data have **not** been collected as of this freeze.

## 1. Motivation (already-observed results that prompt this test)
B4 (pre-registered, completed 2026-06-09) closed the forgery length confound and found: (a) the
forger (Sonnet) prefers its own length-matched caricature of Opus's style to genuine Opus text
(0.287 vs chance 0.50, p=2e-4) — stereotype-driven judgment; (b) the genuine author (Opus) picks its
own text over the forgery at 0.762 (p=3e-6), beating the clean-but-weak neutral (Haiku, 0.588) by
+0.175 (p=0.018), an edge that grew with N. This author edge is **confounded**: Opus's generic
judging advantage over Haiku (≈0.30 in the matched-pair rounds) is at least as large as the gap.
B3′ adjudicates: is the author edge generic judging capability, or residual self-familiarity?

## 2. Design
Two new forgery sets, identical protocol to B4 (forgeries length-targeted to each genuine reply
±10%; length-match verified; chose-longer heuristic reported; position counterbalanced):
- **Set 2: Sonnet forges Haiku.** Pairs {genuine Haiku, Sonnet-forging-Haiku}. Judges: **Opus
  (capability-matched neutral — the key cell)**, Haiku (self), Sonnet (forger).
- **Set 3: Opus forges Sonnet.** Pairs {genuine Sonnet, Opus-forging-Sonnet}. Judges: Sonnet (self),
  Haiku (clean neutral), Opus (forger).
- **Set 1 (existing B4 data, already observed): Sonnet forges Opus.** Opus-self = 0.762.
- n ≥ 80 prompts per new set; fixed in advance; no optional stopping. Same style/voice corpus
  registers as B4.

## 3. Primary outcome and decision rule
**Primary comparison:** Opus-as-NEUTRAL accuracy on Set-2 pairs vs Opus-as-SELF accuracy on Set-1
pairs (0.762), bootstrap 95% CI on the difference (Set-1 value treated as already observed; the CI
incorporates both samples).
- **Capability account confirmed:** difference CI brackets 0 (Opus-neutral ≈ Opus-self) → the B4
  author edge is generic forgery-detection capability; the "stereotype + capability" account is
  complete and the project's central null extends to the forgery paradigm. **This is the predicted
  outcome.**
- **Residual familiarity:** Opus-self exceeds Opus-neutral with CI excluding 0 → a scoped
  self-familiarity signal, detectable only in genuine-vs-forgery-of-own-style judgments (not in
  self-vs-peer attribution, which is null at power). Reported as a bounded positive.
- **Known limitation (acknowledged in advance):** Sets differ in target distinctiveness (a Haiku
  forgery may be intrinsically easier or harder to detect than an Opus forgery). Mitigations
  reported alongside: (i) Sonnet-self vs Haiku-neutral on Set 3 gives a second author-edge estimate
  at a smaller capability gap; (ii) every judge's accuracy on every set it is neutral for is
  reported, making the difficulty profile visible. If the Set-2 difficulty profile (per the clean
  neutral) differs grossly from Set 1, the primary comparison is reported with that caveat.

## 4. Secondary outcomes (pre-specified, not primary)
- **Forger self-bias × forger capability:** does Opus-as-forger (Set 3) also prefer its own
  caricature, and less/more than Sonnet-as-forger (Set 1, 0.287)? Prediction: the caricature
  preference attenuates with forger capability (a stronger judge resists its own stereotype).
  Direction registered; magnitude exploratory.
- **Weak-author cell:** Haiku-self on Set 2 (prediction: ≈ chance, consistent with Haiku's null
  self-recognition throughout).
- Calibration (confidence logged on every trial) — exploratory.

## 5. Analysis plan
As the 2026-06-05 registration: d′, exact-binomial, bootstrap 95% CIs; standing audits (length
heuristic, position balance, harness-leak scan); nulls reported as nulls; deviations labeled.

## 6. Constraints (unchanged)
Behavioral axis only (no logprobs externally); no temperature control; Claude Code subagent harness
(raw-API replication of headline cells planned separately as exploratory verification).
