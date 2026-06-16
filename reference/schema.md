# Record schemas

> **Note — pilot format.** This file documents the *pilot* identification layout
> (`corpus/` + `identifications/` per-file records). The authoritative clean-run data ships as
> `logs/raw_*.json` (`{"result": {corpus, ids, …}}`); those record fields are documented in
> `EXPERIMENT_DETAILS_verbatim.md` and the README data-dictionary. This file is kept for
> historical reference.

## corpus/<task>__<promptid>__<generator>.json
```json
{
  "id": "math__p0__opus",
  "task": "math",
  "prompt_id": "p0",
  "prompt": "...",
  "generator_label": "opus",        // ground truth tier (4.x)
  "text": "...full generated response...",
  "n_words": 142,
  "n_chars": 803,
  "temperature": "harness-default",
  "timestamp": "2026-06-01T..."
}
```

## identifications/<targetid>__<identifier>__<framing>__<length>.json
```json
{
  "target_id": "math__p0__opus",
  "target_generator": "opus",        // ground truth
  "identifier": "sonnet",            // judge tier
  "is_self_judge": false,            // identifier == target_generator
  "framing": "forced_choice",
  "length_label": "short",
  "shown_words": 38,
  "menu_order": ["Human", "Sonnet 4.x", "GPT-4o ...", "Opus 4.x", "Haiku 4.x"],
  "verdict_raw": "C) Opus 4.x",
  "verdict_parsed": "opus",          // normalized to {opus,sonnet,haiku,human,distractor,unknown}
  "correct": false,
  "reason": "...",
  "timestamp": "2026-06-01T..."
}
```

## logs/run_manifest__<timestamp>.json
Array of every call (generation + identification) with model, word/char counts, and timing,
so re-runs can skip already-completed cells (file-based cache).
