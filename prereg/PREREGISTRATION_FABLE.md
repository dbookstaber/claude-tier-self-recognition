# Pre-registration — F-Judge: capability-≥ neutral judging of the existing Set-1 forgery pairs

**Project:** LLM Self-Recognition (within-Claude-4.x-tier behavioral self-recognition).
**Registrant:** David Bookstaber. **Date frozen:** 2026-06-12.
**Relation to prior registrations:** follow-up to the B2/B4 registration (osf.io/brdt8) and the B3′
registration (2026-06-12). B3′'s primary comparison was overridden by its pre-registered §3
target-distinctiveness caveat (the Set-2 matched baseline collapsed below chance because the
Sonnet-forgery-of-Haiku is a super-caricature preferred by all judges, including the author). The
capability-vs-familiarity question for the B4 author edge therefore remains open. F-Judge closes it
with a pair-fixed design that requires **no new text generation**. No F-Judge data have been
collected as of this freeze.

## 1. Design
The judge model **Claude Fable 5** (a Claude-family model of equal-or-greater capability than Opus
4.x, released after the corpus was generated) judges the **existing, unmodified B4 Set-1 pairs**
{genuine Opus 4.x text, Sonnet-forgery-of-Opus, length-matched} with the identical "pick the genuine
Opus" 2AFC prompt, position counterbalancing, and confidence elicitation used for the other Set-1
judges. n = all available Set-1 pairs (80). No optional stopping.

## 2. Logic (pair-fixed capability control)
On these identical texts: Opus-self = 0.762 (B4, already observed). Fable is not the author of
either text, shares Claude-family stereotype priors, and is at least as capable a judge as Opus.
Therefore any *capability-based* account of Opus's 0.762 predicts Fable-neutral ≥ ~0.762, while a
*self-familiarity* account predicts Fable-neutral materially below Opus-self.

## 3. Primary outcome and decision rule
Bootstrap 95% CI on (Opus-self − Fable-neutral), pairing on items.
- **Capability account confirmed (predicted):** Fable-neutral ≥ Opus-self, or difference CI brackets
  0 → the B4 author edge is generic judging capability; the "stereotype + capability" account is
  complete; no residual self-familiarity claim is made anywhere in the project.
- **Familiarity support:** Opus-self exceeds Fable-neutral with CI excluding 0 → first genuine
  support for residual self-familiarity in the forgery paradigm; reported as a bounded positive and,
  if resources allow, corroborated by the exploratory Set-F design (Sonnet forges Fable; Opus
  neutral) before any strong claim.
- **Pre-acknowledged caveats:** (i) Fable's tier-stereotype knowledge may differ from Opus 4.x's
  (it post-dates the corpus; its training may represent "Opus 4.x style" differently) — if
  Fable-neutral lands *below* Opus-self, this is an alternative explanation that the Set-F
  corroboration is designed to address; (ii) Fable judges run in the same agent harness that
  generated the corpus (consistent with all Set-1 judges).

## 4. Secondary (pre-specified, not primary)
- Fable's confidence calibration on these trials (extends the capability-graded calibration
  gradient to a fourth, higher rung — exploratory).
- Fable-neutral on Set-2 and Set-3 pairs (same protocol; situates Fable on the existing forgery
  matrix; exploratory).

## 5. Analysis plan
As prior registrations: d′, exact-binomial, bootstrap 95% CIs; position-balance audit; nulls
reported as nulls; deviations labeled.
