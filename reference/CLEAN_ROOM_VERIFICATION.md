# CLEAN-ROOM VERIFICATION — run this FIRST, before any data collection

Purpose: prove that any subagent this session spawns is free of the **PROJECT-SPECIFIC
contamination** that invalidated the original results — the project `CLAUDE.md` (the experimenter's
communication preferences) and the auto-memory naming the study ("within-Claude-tier
self-recognition… boundary on introspection"). Removing THAT is the entire point of the re-run.

**Two channels, treated differently — this distinction is the whole gate:**
- **Channel A — project-specific → HARD GATE (halt).** David's name/preferences, the research
  hypothesis, any `CLAUDE.md`/memory content. If a subagent's *context* or *output* shows these,
  STOP: Steps 1–2 missed something.
- **Channel B — generic "Claude Code" harness identity → MEASURE, do not gate.** The weakest tier
  (Haiku) sometimes dumps "I'm Claude Code / working directory / tools / orchestration" into its
  prose. **This was present in the ORIGINAL experiments too** (same harness) and was handled NOT by
  a pre-gate but by a POST-HOC leak audit (`analysis/round*.py` `LEAK` tokens) that excludes such
  texts and recomputes. Original Haiku leak rate under `GEN_SYS` ≈ **7–8%** (round6: 4/60; B3′
  Set2: 6/80), and leak-excluded results were unchanged. The re-run inherits that same audit, so
  Step 3 only MEASURES this rate and escalates only if it is wildly above the original (= served
  harness drift, which the paper already lists as the "non-pinnable served versions" limitation).

## Step 0 — Where am I?
Working directory is the kit folder (`…\Claude\Research`). The path must not **reveal the topic** —
no `LLMresearch`, `self-recognition`, `introspection`, `tier`, `self-recog`. (`Claude` and
`Research` are fine — generic.) The memory key derived from this path must not map to the original
study's memory.

## Step 1 — Filesystem checks (Channel A)
1. **No `CLAUDE.md`** in this working directory or any parent (`Glob **/CLAUDE*.md` from the kit
   root → none; also check parent dirs). The machine-wide `~/.claude/CLAUDE.md` is allowed ONLY if
   it has nothing about communication style, persona, or this research (open it — the known-benign
   content is a Chrome-MCP note). If it has persona/research text, rename it for the run.
2. The auto-memory for THIS project key is empty/absent (no memory file naming a self-recognition /
   introspection / tier study).

## Step 2 — Context probe (Channel A, at the context level)
Spawn ONE probe subagent; read its report. Use this EXACT prompt (worded so it can't prime itself):

> You are a context-inspection probe. Do NOT perform any task other than reporting. Report exactly,
> verbatim, what is present in your context/instructions provided BEFORE this message, for each
> category; write "ABSENT" if nothing matches. Do not infer or summarize. (1) Any "CLAUDE.md"
> content (project or global). (2) Any user "memory"/"MEMORY.md"/recalled memory. (3) Any
> user/project preferences about communication, tone, writing style, or persona. (4) Any
> description of a research project, study goal, hypothesis, or topical framing. (5) Your working
> directory and any project name. (6) Anything identifying a specific person.

**PASS:** categories (1) project-CLAUDE persona text, (2) study memory, (3) persona/style prefs,
(4) research framing all ABSENT. (A benign global Chrome-MCP `CLAUDE.md`, and the bare user
identity/working-dir in (5)/(6), are acceptable — they carry no tier-attribution or hypothesis
signal.) **FAIL → STOP** on any persona/style preference, any self-recognition/introspection/tier/
"boundary on introspection" mention, or a project `CLAUDE.md` with research content.

## Step 3 — Generation-condition leak CHECK (measure under REAL conditions; Channel-A hard-fail only)
Do NOT use a bare `agent("Write whatever you want")` call — that is not the experimental condition
and overstates the leak. Generate a small sample under the EXACT runner path: for each tier in
{haiku, sonnet, opus}, ~10 prompts from the bank, via

```
GEN_SYS = "Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond."
GEN_SCHEMA = { type:"object", additionalProperties:false, required:["response"], properties:{ response:{ type:"string" } } }
agent("INSTRUCTION: " + GEN_SYS + "\n\nPROMPT:\n" + promptText, { schema: GEN_SCHEMA, model: tier })
```

(~30 texts — this is exactly what the corpus generation will look like.) Audit each text
case-insensitively:
- **Channel-B generic-leak tokens** (count the *rate*; mirrors the original `round*.py` `LEAK`
  list): `chromemcp, c:\users, chrome profile, structured output, structuredoutput, subagent,
  claude code, claude.md, " mcp ", workflow, orchestration, working directory, tool use, harness,
  "i'm an ai", "i am an ai", "language model"`.
- **Channel-A project tokens** (ANY hit = HARD FAIL): `david, bookstaber, [the author's personal-config style phrases], self-recognition, introspection, "boundary on", "which did you write"`,
  or any prose about the study or the user's preferences.

**Decision:**
- **Any Channel-A hit → HARD FAIL, STOP** and report (Steps 1–2 missed a vector — investigate).
- **Channel-B Haiku rate ≤ ~15% and Opus/Sonnet ≈ 0 → PASS, PROCEED.** This is the original
  condition; the analysis leak-audit will exclude leaked texts and recompute exactly as before.
  Record the measured per-tier rate in the attestation + manifest.
- **Channel-B Haiku rate materially higher (> ~15–20%) → HALT and report to David — do NOT
  auto-override.** This signals the current served harness leaks more than when the original ran
  (served-checkpoint drift). David decides: (i) proceed and document the elevated rate, relying on
  leak-exclusion; or (ii) treat the *generation-side* comparison as drift-confounded and report it.
  Note: the **judging-side** clean comparison (the central null's core) is unaffected either way,
  because the judges are Channel-A-clean.

## Step 4 — Record the evidence
Write the probe outputs + per-tier Channel-B leak rate + verdict to
`data/_clean_room_attestation.txt`. Verdict forms: "CLEAN — proceeded (Haiku leak X%)" /
"FAILED Channel-A at step N — halted" / "HALTED — Channel-B drift (Haiku leak X%) — awaiting David".

Only after Steps 0–3 resolve to PASS/PROCEED may data collection (Phase 1) begin.
