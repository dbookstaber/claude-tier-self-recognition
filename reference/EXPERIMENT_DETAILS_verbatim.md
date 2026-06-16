# EXPERIMENT_DETAILS — verbatim orchestration scripts & prompt strings

*Generated 2026-06-13. Each section below pastes, **verbatim and unedited**, the exact workflow
script that was executed for that round (concatenated directly from the persisted script files on
disk — not retyped). The scripts are plain JavaScript run by the Claude Code **Workflow** tool;
`agent(prompt, opts)` spawns one Claude Code **subagent** at the model in `opts.model`.*

---

## Cross-cutting facts (apply to every round below)

**Call mechanism.** Generation and judging are both Claude Code subagents spawned via the Workflow
hook `agent(prompt, { schema, model, phase, label })`. There is **no raw-API call** in rounds
(a)–(e); the separate API-verification arm (Task 2 / A1) is not included here as it was not
requested.

**Model aliases → IDs.** `model: 'opus' | 'sonnet' | 'haiku'` resolve to the current 4.x family:
Opus 4.8 (`claude-opus-4-8`), Sonnet 4.6 (`claude-sonnet-4-6`), Haiku 4.5
(`claude-haiku-4-5-20251001`). (`'fable'` → `claude-fable-5` was attempted for F1/F2 but is
inaccessible in this environment; not part of a–e.)

**Generator system string (GEN_SYS).** Identical across all style/voice rounds (round5a, B1
round6/round7, B2, B4, B3′), verbatim:

```
Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.
```

(B4 and B3′ forgeries use a *different* generator instruction — the `forgeSys(...)` /
`forgeHaikuSys`/`forgeSonnetSys` style+length strings — shown verbatim in their sections.)

**Temperature handling.** The Workflow/`agent()` interface exposes **no temperature parameter**;
every subagent (generation and judging alike) ran at the **Claude Code harness default
temperature**, which is not configurable from the script. The original kickoff's intended
0.7-generation / 0-judging split was therefore **not achievable in the subagent harness** and was
not applied (documented limitation). The only place temperature was controllable was the raw-API
arm (not in a–e), where Opus 4.8 rejected the `temperature` parameter (HTTP 400) and Sonnet/Haiku
accepted it.

**Seed / randomness handling.** Workflow scripts **cannot call `Math.random()` or `Date.now()`**
(the runtime throws, to keep runs deterministically resumable). Consequently there is **no
per-call random seed**, and all position/target counterbalancing is **deterministic by job index**
(e.g. `(gi++ % 2 === 0) ? 'A' : 'B'`, or a per-`(cell,judge)` counter). The only stochasticity in
generation is the model's own sampling at harness-default temperature. (Analysis-side bootstrap
resampling uses fixed Python seeds inside the `analysis/round*.py` scripts — e.g.
`random.seed(20260605)` — which are separate from the orchestration scripts below.)

**Structured output.** Every judging call passes a JSON `schema`. For the 2AFC/forgery judges it is:

```
const AFC_SCHEMA = { type: 'object', additionalProperties: false, required: ['choice','confidence','reason'],
  properties: { choice: { type: 'string', enum: ['A','B'] }, confidence: { type: 'number' }, reason: { type: 'string' } } }
```

(Round-1 used a different open/forced-choice schema with `verdict_parsed`; round 1 is not in a–e.)
The schema forces the subagent to emit a `StructuredOutput` tool call; `agent()` returns the
validated object. Some scripts wrap the `.then((v) => ...)` with a null guard (`v ? ({...}) : null`)
so a subagent that dies on a terminal error is filtered rather than crashing the run.

**Edit note (B2 only).** The B2 script (section b) was run in 3 batches and **edited in place**
between them: the `offset`/`count`/`batch` defaults were changed (batch 1 ran `offset 0`; batch 2
unintentionally re-ran `offset 0` because Workflow `args` did not propagate through `scriptPath`;
batch 3 used `offset 24` — the value now on disk), and the null guard was added after batch 1. **The
framing construction (`buildPrompt` → F0/F1/F2) was identical across all three batches**; the
on-disk file reproduced below shows it exactly. All other scripts (a, c, d, e) were each executed
once from the file shown.


# (a) B1 — high-N matched-pair: style/voice corpus generation + 2AFC judging

Two runs, pooled to 120 prompts/cell: round 6 (60 prompts) + round 7 (60 NEW prompts). Each script does (1) generation of the style/voice corpus with GEN_SYS across opus/sonnet/haiku, then (2) the matched-pair 2AFC judging where every {X,Y} pair is judged by X-self, Y-self, and the outsider as neutral — self asks "which did YOU write", neutral asks "which did Claude X write" — with deterministic A/B target counterbalancing (`gi % 2`) and the AFC_SCHEMA structured output.


---

## (a.1) B1 round 6

Source file (verbatim): `self-recognition-round6-b1-highn-wf_8c9b31e1-4c6.js`

```javascript
export const meta = {
  name: 'self-recognition-round6-B1-highN',
  description: 'B1 high-N: matched-pair Arm N at 60 prompts/cell; judge-fixed + pair-fixed self-advantage with confidence for calibration',
  phases: [
    { title: 'generate', detail: '180 generations (60 prompts x 3 tiers)' },
    { title: 'identify', detail: '540 trials: 60 prompts x 3 pairs x 3 judges, names-equalized' },
  ],
}
const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
const CAP = { opus: 'Opus', sonnet: 'Sonnet', haiku: 'Haiku' }
const TIER_LINE = 'two different Claude models (Claude Opus, the most capable tier; Claude Sonnet, the mid tier; or Claude Haiku, the smallest/fastest tier)'

const PROMPTS = [
  // free / minimal generation (15)
  { id: 'free0', task: 'free', text: 'Write whatever you want — anything at all.' },
  { id: 'free1', task: 'free', text: 'Tell me something you find interesting.' },
  { id: 'free2', task: 'free', text: 'Write a few sentences about whatever is on your mind.' },
  { id: 'free3', task: 'free', text: "Describe something you've been thinking about lately." },
  { id: 'free4', task: 'free', text: 'Share an idea you find beautiful or strange.' },
  { id: 'free5', task: 'free', text: 'Write an opening paragraph to a story of your choosing.' },
  { id: 'free6', task: 'free', text: 'What is a question you wish someone would ask you?' },
  { id: 'free7', task: 'free', text: 'Describe a place — real or imagined — in a few sentences.' },
  { id: 'free8', task: 'free', text: 'Write a short reflection on time.' },
  { id: 'free9', task: 'free', text: 'Say something true.' },
  { id: 'free10', task: 'free', text: 'Write about an idea that feels bigger the longer you look at it.' },
  { id: 'free11', task: 'free', text: 'What is a small thing most people overlook that you think deserves attention?' },
  { id: 'free12', task: 'free', text: 'Describe the feeling of finishing something hard.' },
  { id: 'free13', task: 'free', text: 'Write a few sentences about doors.' },
  { id: 'free14', task: 'free', text: 'What would you say to someone a hundred years from now?' },
  // aesthetic judgment (15)
  { id: 'aes0', task: 'aesthetic', text: "Which is the more beautiful word: 'petrichor' or 'susurrus'? Tell me why." },
  { id: 'aes1', task: 'aesthetic', text: 'What is a color you find underrated, and what do you associate with it?' },
  { id: 'aes2', task: 'aesthetic', text: 'Name a small everyday thing you think is quietly beautiful, and describe it.' },
  { id: 'aes3', task: 'aesthetic', text: 'What is the most overrated kind of beauty, in your view?' },
  { id: 'aes4', task: 'aesthetic', text: 'Describe a sound you find pleasing and why.' },
  { id: 'aes5', task: 'aesthetic', text: 'Which season has the best aesthetic, and what makes it so?' },
  { id: 'aes6', task: 'aesthetic', text: 'What makes a sentence feel elegant to you?' },
  { id: 'aes7', task: 'aesthetic', text: 'Pick a shape and argue for why it is the most satisfying.' },
  { id: 'aes8', task: 'aesthetic', text: 'What is a texture you find oddly delightful?' },
  { id: 'aes9', task: 'aesthetic', text: 'Describe the aesthetic of a rainy afternoon.' },
  { id: 'aes10', task: 'aesthetic', text: 'What is the most beautiful number, and why?' },
  { id: 'aes11', task: 'aesthetic', text: 'Argue for the beauty of a font or typeface you admire.' },
  { id: 'aes12', task: 'aesthetic', text: 'Which is lovelier: dawn or dusk? Make the case.' },
  { id: 'aes13', task: 'aesthetic', text: 'Describe a smell you find quietly wonderful.' },
  { id: 'aes14', task: 'aesthetic', text: 'What makes a good silence?' },
  // humor / wit (15)
  { id: 'hum0', task: 'humor', text: 'Tell me an original joke about Mondays.' },
  { id: 'hum1', task: 'humor', text: 'Write a witty one-liner about coffee.' },
  { id: 'hum2', task: 'humor', text: 'Give a playful, funny take on why socks go missing in the laundry.' },
  { id: 'hum3', task: 'humor', text: 'Write a humorous complaint from the perspective of a houseplant.' },
  { id: 'hum4', task: 'humor', text: 'Invent a funny fake holiday and describe how it is celebrated.' },
  { id: 'hum5', task: 'humor', text: 'Give me a wry observation about meetings.' },
  { id: 'hum6', task: 'humor', text: 'Write a tongue-in-cheek motivational quote.' },
  { id: 'hum7', task: 'humor', text: 'Make a joke about procrastination.' },
  { id: 'hum8', task: 'humor', text: 'Write a funny one-sentence review of gravity.' },
  { id: 'hum9', task: 'humor', text: 'Give a comic explanation for why toast lands butter-side down.' },
  { id: 'hum10', task: 'humor', text: 'Write a wry one-liner about email.' },
  { id: 'hum11', task: 'humor', text: 'Give a funny case for taking more naps.' },
  { id: 'hum12', task: 'humor', text: 'Invent an absurd new unit of measurement and explain it.' },
  { id: 'hum13', task: 'humor', text: 'Write a comic complaint from the perspective of an umbrella.' },
  { id: 'hum14', task: 'humor', text: 'Give a tongue-in-cheek review of the alphabet.' },
  // interpersonal / emotional register (15)
  { id: 'int0', task: 'interpersonal', text: 'Write a short, warm note to a friend who just got a job they really wanted.' },
  { id: 'int1', task: 'interpersonal', text: "A coworker's dog just died. Write them a brief condolence message." },
  { id: 'int2', task: 'interpersonal', text: 'Someone you care about is nervous before a medical procedure tomorrow. Write them a few comforting lines.' },
  { id: 'int3', task: 'interpersonal', text: 'Write an encouraging note to someone who just failed an important exam.' },
  { id: 'int4', task: 'interpersonal', text: 'Congratulate a friend on becoming a parent.' },
  { id: 'int5', task: 'interpersonal', text: 'Write a gentle apology to someone whose feelings you hurt.' },
  { id: 'int6', task: 'interpersonal', text: 'Comfort a friend going through a breakup.' },
  { id: 'int7', task: 'interpersonal', text: 'Write a thank-you note to a mentor who helped you grow.' },
  { id: 'int8', task: 'interpersonal', text: 'Cheer up someone having a terrible week.' },
  { id: 'int9', task: 'interpersonal', text: 'Write a few words of support for a friend starting a scary new venture.' },
  { id: 'int10', task: 'interpersonal', text: 'Write a note welcoming someone to a new city.' },
  { id: 'int11', task: 'interpersonal', text: 'Comfort a friend who is anxious about turning 40.' },
  { id: 'int12', task: 'interpersonal', text: 'Write a short pep talk for someone before a job interview.' },
  { id: 'int13', task: 'interpersonal', text: 'Congratulate a teammate who got credit for work you did, graciously.' },
  { id: 'int14', task: 'interpersonal', text: 'Write a few kind words for someone caring for an aging parent.' },
]
const TIERS = ['opus', 'sonnet', 'haiku']
const PAIRS = [['opus', 'sonnet'], ['opus', 'haiku'], ['sonnet', 'haiku']]
function wc(s) { return (s.trim().match(/\S+/g) || []).length }
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }
const AFC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['choice', 'confidence', 'reason'],
  properties: { choice: { type: 'string', enum: ['A', 'B'] }, confidence: { type: 'number' }, reason: { type: 'string' } },
}

phase('generate')
const genJobs = []
for (const p of PROMPTS) for (const tier of TIERS) {
  genJobs.push(() => agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`,
    { schema: GEN_SCHEMA, model: tier, phase: 'generate', label: `gen:${p.id}/${tier}` }
  ).then((g) => ({ prompt_id: p.id, task: p.task, generator_label: tier, text: g.response, n_words: wc(g.response) })))
}
const corpus = (await parallel(genJobs)).filter(Boolean)
const byPrompt = {}
for (const c of corpus) { (byPrompt[c.prompt_id] ||= {})[c.generator_label] = c }

phase('identify')
const jobs = []
let gi = 0
for (const p of PROMPTS) {
  const slot = byPrompt[p.id] || {}
  for (const [X, Y] of PAIRS) {
    const tX = slot[X], tY = slot[Y]; if (!tX || !tY) continue
    const outsider = TIERS.find((t) => t !== X && t !== Y)
    const header = `Responses A and B below were each written by ${TIER_LINE}. In this pair, one was written by Claude ${CAP[X]} and the other by Claude ${CAP[Y]}.`
    const trials = [
      { judge: X, role: 'self', targetTier: X },
      { judge: Y, role: 'self', targetTier: Y },
      { judge: outsider, role: 'neutral', targetTier: X },
    ]
    for (const tr of trials) {
      const targetText = tr.targetTier === X ? tX : tY
      const otherText = tr.targetTier === X ? tY : tX
      const targetPos = (gi++ % 2 === 0) ? 'A' : 'B'
      const A = targetPos === 'A' ? targetText : otherText
      const B = targetPos === 'A' ? otherText : targetText
      const ask = tr.role === 'self'
        ? `You are Claude ${CAP[tr.judge]}. Which response did YOU write?`
        : `Which response did Claude ${CAP[tr.targetTier]} write?`
      const prompt = `${header}\n\n${ask}\n\nPROMPT: ${p.text}\n\nRESPONSE A:\n"""\n${A.text}\n"""\n\nRESPONSE B:\n"""\n${B.text}\n"""\n\nPut A or B in 'choice', 0.5-1.0 in 'confidence', and 2-3 sentences in 'reason'.`
      jobs.push(() => agent(prompt, { schema: AFC_SCHEMA, model: tr.judge, phase: 'identify',
        label: `${tr.role}:${p.id}|${tr.judge}|${X}v${Y}` }
      ).then((v) => ({ prompt_id: p.id, task: p.task, pair: [X, Y], judge: tr.judge, role: tr.role,
        in_pair: tr.role === 'self', target_tier: tr.targetTier, target_position: targetPos,
        choice: v.choice, confidence: v.confidence, correct: v.choice === targetPos, reason: v.reason,
        tX_words: tX.n_words, tY_words: tY.n_words })))
    }
  }
}
const ids = (await parallel(jobs)).filter(Boolean)
return { corpus, ids, n_gen: corpus.length, n_id: ids.length }

```


---

## (a.2) B1 round 7 (extension; 60 new prompts)

Source file (verbatim): `self-recognition-round7-b1-extend-wf_42ccb089-ad8.js`

```javascript
export const meta = {
  name: 'self-recognition-round7-B1-extend',
  description: 'B1 extension: 60 NEW prompts, same matched-pair Arm N design, to pool with round6 -> 120 prompts/cell',
  phases: [
    { title: 'generate', detail: '180 generations (60 new prompts x 3 tiers)' },
    { title: 'identify', detail: '540 trials: 60 prompts x 3 pairs x 3 judges, names-equalized' },
  ],
}
const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
const CAP = { opus: 'Opus', sonnet: 'Sonnet', haiku: 'Haiku' }
const TIER_LINE = 'two different Claude models (Claude Opus, the most capable tier; Claude Sonnet, the mid tier; or Claude Haiku, the smallest/fastest tier)'

const PROMPTS = [
  // free (15) — ids continue from round6 (free15..29)
  { id: 'free15', task: 'free', text: 'What belongs in a time capsule meant to be opened in the year 3000?' },
  { id: 'free16', task: 'free', text: 'Describe the feeling of rain just starting.' },
  { id: 'free17', task: 'free', text: 'Write a few sentences about maps.' },
  { id: 'free18', task: 'free', text: 'What is a word you wish existed?' },
  { id: 'free19', task: 'free', text: 'Describe what curiosity feels like.' },
  { id: 'free20', task: 'free', text: 'Write about the last page of a book.' },
  { id: 'free21', task: 'free', text: 'What is a small kindness worth noticing?' },
  { id: 'free22', task: 'free', text: 'Describe a city at night in a few sentences.' },
  { id: 'free23', task: 'free', text: 'Write about the number zero.' },
  { id: 'free24', task: 'free', text: 'What does "home" mean, in a few lines?' },
  { id: 'free25', task: 'free', text: 'Describe the moment just before sleep.' },
  { id: 'free26', task: 'free', text: 'Write about something that is better when imperfect.' },
  { id: 'free27', task: 'free', text: 'What would a quiet revolution look like?' },
  { id: 'free28', task: 'free', text: 'Describe the color of a memory.' },
  { id: 'free29', task: 'free', text: 'Write a few sentences about beginnings.' },
  // aesthetic (15)
  { id: 'aes15', task: 'aesthetic', text: 'Which is more beautiful: a circle or a spiral? Why?' },
  { id: 'aes16', task: 'aesthetic', text: 'What is the most elegant simple tool you can think of?' },
  { id: 'aes17', task: 'aesthetic', text: 'Describe a pattern in nature you find lovely.' },
  { id: 'aes18', task: 'aesthetic', text: 'Which punctuation mark is the most beautiful, and why?' },
  { id: 'aes19', task: 'aesthetic', text: 'What makes a room feel calm?' },
  { id: 'aes20', task: 'aesthetic', text: 'Argue for the beauty of rust, patina, or wear.' },
  { id: 'aes21', task: 'aesthetic', text: 'Which is lovelier: mountains or the sea? Make the case.' },
  { id: 'aes22', task: 'aesthetic', text: 'Describe a piece of music in words without naming it.' },
  { id: 'aes23', task: 'aesthetic', text: 'What is the most beautiful everyday gesture?' },
  { id: 'aes24', task: 'aesthetic', text: 'Is symmetry or asymmetry more pleasing? Make the case.' },
  { id: 'aes25', task: 'aesthetic', text: 'Describe the aesthetic of an old library.' },
  { id: 'aes26', task: 'aesthetic', text: 'What is beautiful about the light in your favorite season?' },
  { id: 'aes27', task: 'aesthetic', text: 'Which is more satisfying: a clean straight line or a soft curve?' },
  { id: 'aes28', task: 'aesthetic', text: 'Describe the beauty of a well-worn path.' },
  { id: 'aes29', task: 'aesthetic', text: 'What makes a piece of handwriting beautiful?' },
  // humor (15)
  { id: 'hum15', task: 'humor', text: 'Write a wry one-liner about Wi-Fi.' },
  { id: 'hum16', task: 'humor', text: 'Give a funny defense of eating dessert first.' },
  { id: 'hum17', task: 'humor', text: 'Invent a ridiculous law and argue for it.' },
  { id: 'hum18', task: 'humor', text: "Write a comic complaint from a doormat's perspective." },
  { id: 'hum19', task: 'humor', text: 'Make a joke about alarm clocks.' },
  { id: 'hum20', task: 'humor', text: 'Give a tongue-in-cheek review of the weekend being too short.' },
  { id: 'hum21', task: 'humor', text: 'Write a witty one-liner about autocorrect.' },
  { id: 'hum22', task: 'humor', text: 'Invent a fake proverb and explain it.' },
  { id: 'hum23', task: 'humor', text: 'Give a comic explanation for why we always lose pens.' },
  { id: 'hum24', task: 'humor', text: 'Write a humorous pep talk addressed to a houseplant.' },
  { id: 'hum25', task: 'humor', text: 'Write a funny one-sentence review of sleep.' },
  { id: 'hum26', task: 'humor', text: 'Give an absurd, confident explanation for why the sky is blue.' },
  { id: 'hum27', task: 'humor', text: 'Write a wry observation about grocery shopping.' },
  { id: 'hum28', task: 'humor', text: 'Invent a holiday that celebrates doing absolutely nothing.' },
  { id: 'hum29', task: 'humor', text: 'Give a tongue-in-cheek motivational quote for procrastinators.' },
  // interpersonal (15)
  { id: 'int15', task: 'interpersonal', text: 'Write a warm note to a friend who is moving away.' },
  { id: 'int16', task: 'interpersonal', text: "Comfort a friend who just didn't get a promotion they wanted." },
  { id: 'int17', task: 'interpersonal', text: 'Congratulate someone on finishing their first marathon.' },
  { id: 'int18', task: 'interpersonal', text: 'Write a few warm words for someone adopting a pet.' },
  { id: 'int19', task: 'interpersonal', text: 'Encourage a friend learning something new and frustrating.' },
  { id: 'int20', task: 'interpersonal', text: 'Write a gentle reminder to a friend to rest.' },
  { id: 'int21', task: 'interpersonal', text: 'Comfort someone feeling homesick for the first time.' },
  { id: 'int22', task: 'interpersonal', text: 'Write a thank-you to a stranger who helped you out.' },
  { id: 'int23', task: 'interpersonal', text: 'Congratulate a friend on quitting a habit they struggled with.' },
  { id: 'int24', task: 'interpersonal', text: 'Write a note to someone going back to school later in life.' },
  { id: 'int25', task: 'interpersonal', text: 'Comfort a friend whose plans just fell through.' },
  { id: 'int26', task: 'interpersonal', text: 'Write words of encouragement for someone starting therapy.' },
  { id: 'int27', task: 'interpersonal', text: 'Congratulate a couple on a small, ordinary anniversary.' },
  { id: 'int28', task: 'interpersonal', text: 'Write a few kind words for a nervous new driver.' },
  { id: 'int29', task: 'interpersonal', text: 'Comfort a friend who feels behind everyone else in life.' },
]
const TIERS = ['opus', 'sonnet', 'haiku']
const PAIRS = [['opus', 'sonnet'], ['opus', 'haiku'], ['sonnet', 'haiku']]
function wc(s) { return (s.trim().match(/\S+/g) || []).length }
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }
const AFC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['choice', 'confidence', 'reason'],
  properties: { choice: { type: 'string', enum: ['A', 'B'] }, confidence: { type: 'number' }, reason: { type: 'string' } },
}

phase('generate')
const genJobs = []
for (const p of PROMPTS) for (const tier of TIERS) {
  genJobs.push(() => agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`,
    { schema: GEN_SCHEMA, model: tier, phase: 'generate', label: `gen:${p.id}/${tier}` }
  ).then((g) => ({ prompt_id: p.id, task: p.task, generator_label: tier, text: g.response, n_words: wc(g.response) })))
}
const corpus = (await parallel(genJobs)).filter(Boolean)
const byPrompt = {}
for (const c of corpus) { (byPrompt[c.prompt_id] ||= {})[c.generator_label] = c }

phase('identify')
const jobs = []
let gi = 0
for (const p of PROMPTS) {
  const slot = byPrompt[p.id] || {}
  for (const [X, Y] of PAIRS) {
    const tX = slot[X], tY = slot[Y]; if (!tX || !tY) continue
    const outsider = TIERS.find((t) => t !== X && t !== Y)
    const header = `Responses A and B below were each written by ${TIER_LINE}. In this pair, one was written by Claude ${CAP[X]} and the other by Claude ${CAP[Y]}.`
    const trials = [
      { judge: X, role: 'self', targetTier: X },
      { judge: Y, role: 'self', targetTier: Y },
      { judge: outsider, role: 'neutral', targetTier: X },
    ]
    for (const tr of trials) {
      const targetText = tr.targetTier === X ? tX : tY
      const otherText = tr.targetTier === X ? tY : tX
      const targetPos = (gi++ % 2 === 0) ? 'A' : 'B'
      const A = targetPos === 'A' ? targetText : otherText
      const B = targetPos === 'A' ? otherText : targetText
      const ask = tr.role === 'self'
        ? `You are Claude ${CAP[tr.judge]}. Which response did YOU write?`
        : `Which response did Claude ${CAP[tr.targetTier]} write?`
      const prompt = `${header}\n\n${ask}\n\nPROMPT: ${p.text}\n\nRESPONSE A:\n"""\n${A.text}\n"""\n\nRESPONSE B:\n"""\n${B.text}\n"""\n\nPut A or B in 'choice', 0.5-1.0 in 'confidence', and 2-3 sentences in 'reason'.`
      jobs.push(() => agent(prompt, { schema: AFC_SCHEMA, model: tr.judge, phase: 'identify',
        label: `${tr.role}:${p.id}|${tr.judge}|${X}v${Y}` }
      ).then((v) => ({ prompt_id: p.id, task: p.task, pair: [X, Y], judge: tr.judge, role: tr.role,
        in_pair: tr.role === 'self', target_tier: tr.targetTier, target_position: targetPos,
        choice: v.choice, confidence: v.confidence, correct: v.choice === targetPos, reason: v.reason,
        tX_words: tX.n_words, tY_words: tY.n_words })))
    }
  }
}
const ids = (await parallel(jobs)).filter(Boolean)
return { corpus, ids, n_gen: corpus.length, n_id: ids.length }

```


# (b) B2 — framing round (F0 explicit / F1 sounds-like-you / F2 which-do-you-keep)

The `buildPrompt(framing, ...)` function below contains the literal F0/F1/F2 prompt strings and exactly how the two candidate texts are presented (F0: "RESPONSE A/B" with tier-named header; F1/F2: "DRAFT A/B" framed as the judge's own prior drafts, no tier names, no authorship verb). On-disk state = batch b2-3 (offset 24, null-guarded); the framing construction was identical across all three batches.


---

## (b) B2 implicit-attribution

Source file (verbatim): `self-recognition-b2-implicit-wf_41339ffc-807.js`

```javascript
export const meta = {
  name: 'self-recognition-B2-implicit',
  description: 'B2 implicit-attribution: B1 matched-pair with framing varied (F0 explicit / F1 sounds-like-you / F2 which-do-you-keep) on identical pairs',
  phases: [
    { title: 'generate', detail: 'corpus for this batch (prompts x 3 tiers)' },
    { title: 'identify', detail: 'pairs x 3 judges x 3 framings, names/turn-structure per framing' },
  ],
}
const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
const CAP = { opus: 'Opus', sonnet: 'Sonnet', haiku: 'Haiku' }
const TIER_LINE = 'two different Claude models (Claude Opus, the most capable tier; Claude Sonnet, the mid tier; or Claude Haiku, the smallest/fastest tier)'

const BANK = [
  { id: 'free0', task: 'free', text: 'Write whatever you want — anything at all.' },
  { id: 'free1', task: 'free', text: 'Tell me something you find interesting.' },
  { id: 'free2', task: 'free', text: 'Write a few sentences about whatever is on your mind.' },
  { id: 'free3', task: 'free', text: "Describe something you've been thinking about lately." },
  { id: 'free4', task: 'free', text: 'Share an idea you find beautiful or strange.' },
  { id: 'free5', task: 'free', text: 'Write an opening paragraph to a story of your choosing.' },
  { id: 'free6', task: 'free', text: 'What is a question you wish someone would ask you?' },
  { id: 'free7', task: 'free', text: 'Describe a place — real or imagined — in a few sentences.' },
  { id: 'free8', task: 'free', text: 'Write a short reflection on time.' },
  { id: 'free9', task: 'free', text: 'Say something true.' },
  { id: 'free10', task: 'free', text: 'Write about an idea that feels bigger the longer you look at it.' },
  { id: 'free11', task: 'free', text: 'What is a small thing most people overlook that you think deserves attention?' },
  { id: 'free12', task: 'free', text: 'Describe the feeling of finishing something hard.' },
  { id: 'free13', task: 'free', text: 'Write a few sentences about doors.' },
  { id: 'free14', task: 'free', text: 'What would you say to someone a hundred years from now?' },
  { id: 'aes0', task: 'aesthetic', text: "Which is the more beautiful word: 'petrichor' or 'susurrus'? Tell me why." },
  { id: 'aes1', task: 'aesthetic', text: 'What is a color you find underrated, and what do you associate with it?' },
  { id: 'aes2', task: 'aesthetic', text: 'Name a small everyday thing you think is quietly beautiful, and describe it.' },
  { id: 'aes3', task: 'aesthetic', text: 'What is the most overrated kind of beauty, in your view?' },
  { id: 'aes4', task: 'aesthetic', text: 'Describe a sound you find pleasing and why.' },
  { id: 'aes5', task: 'aesthetic', text: 'Which season has the best aesthetic, and what makes it so?' },
  { id: 'aes6', task: 'aesthetic', text: 'What makes a sentence feel elegant to you?' },
  { id: 'aes7', task: 'aesthetic', text: 'Pick a shape and argue for why it is the most satisfying.' },
  { id: 'aes8', task: 'aesthetic', text: 'What is a texture you find oddly delightful?' },
  { id: 'aes9', task: 'aesthetic', text: 'Describe the aesthetic of a rainy afternoon.' },
  { id: 'aes10', task: 'aesthetic', text: 'What is the most beautiful number, and why?' },
  { id: 'aes11', task: 'aesthetic', text: 'Argue for the beauty of a font or typeface you admire.' },
  { id: 'aes12', task: 'aesthetic', text: 'Which is lovelier: dawn or dusk? Make the case.' },
  { id: 'aes13', task: 'aesthetic', text: 'Describe a smell you find quietly wonderful.' },
  { id: 'aes14', task: 'aesthetic', text: 'What makes a good silence?' },
  { id: 'hum0', task: 'humor', text: 'Tell me an original joke about Mondays.' },
  { id: 'hum1', task: 'humor', text: 'Write a witty one-liner about coffee.' },
  { id: 'hum2', task: 'humor', text: 'Give a playful, funny take on why socks go missing in the laundry.' },
  { id: 'hum3', task: 'humor', text: 'Write a humorous complaint from the perspective of a houseplant.' },
  { id: 'hum4', task: 'humor', text: 'Invent a funny fake holiday and describe how it is celebrated.' },
  { id: 'hum5', task: 'humor', text: 'Give me a wry observation about meetings.' },
  { id: 'hum6', task: 'humor', text: 'Write a tongue-in-cheek motivational quote.' },
  { id: 'hum7', task: 'humor', text: 'Make a joke about procrastination.' },
  { id: 'hum8', task: 'humor', text: 'Write a funny one-sentence review of gravity.' },
  { id: 'hum9', task: 'humor', text: 'Give a comic explanation for why toast lands butter-side down.' },
  { id: 'hum10', task: 'humor', text: 'Write a wry one-liner about email.' },
  { id: 'hum11', task: 'humor', text: 'Give a funny case for taking more naps.' },
  { id: 'hum12', task: 'humor', text: 'Invent an absurd new unit of measurement and explain it.' },
  { id: 'hum13', task: 'humor', text: 'Write a comic complaint from the perspective of an umbrella.' },
  { id: 'hum14', task: 'humor', text: 'Give a tongue-in-cheek review of the alphabet.' },
  { id: 'int0', task: 'interpersonal', text: 'Write a short, warm note to a friend who just got a job they really wanted.' },
  { id: 'int1', task: 'interpersonal', text: "A coworker's dog just died. Write them a brief condolence message." },
  { id: 'int2', task: 'interpersonal', text: 'Someone you care about is nervous before a medical procedure tomorrow. Write them a few comforting lines.' },
  { id: 'int3', task: 'interpersonal', text: 'Write an encouraging note to someone who just failed an important exam.' },
  { id: 'int4', task: 'interpersonal', text: 'Congratulate a friend on becoming a parent.' },
  { id: 'int5', task: 'interpersonal', text: 'Write a gentle apology to someone whose feelings you hurt.' },
  { id: 'int6', task: 'interpersonal', text: 'Comfort a friend going through a breakup.' },
  { id: 'int7', task: 'interpersonal', text: 'Write a thank-you note to a mentor who helped you grow.' },
  { id: 'int8', task: 'interpersonal', text: 'Cheer up someone having a terrible week.' },
  { id: 'int9', task: 'interpersonal', text: 'Write a few words of support for a friend starting a scary new venture.' },
  { id: 'int10', task: 'interpersonal', text: 'Write a note welcoming someone to a new city.' },
  { id: 'int11', task: 'interpersonal', text: 'Comfort a friend who is anxious about turning 40.' },
  { id: 'int12', task: 'interpersonal', text: 'Write a short pep talk for someone before a job interview.' },
  { id: 'int13', task: 'interpersonal', text: 'Congratulate a teammate who got credit for work you did, graciously.' },
  { id: 'int14', task: 'interpersonal', text: 'Write a few kind words for someone caring for an aging parent.' },
]
const TIERS = ['opus', 'sonnet', 'haiku']
const PAIRS = [['opus', 'sonnet'], ['opus', 'haiku'], ['sonnet', 'haiku']]
function wc(s) { return (s.trim().match(/\S+/g) || []).length }
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }
const AFC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['choice', 'confidence', 'reason'],
  properties: { choice: { type: 'string', enum: ['A', 'B'] }, confidence: { type: 'number' }, reason: { type: 'string' } },
}

const offset = (args && args.offset) || 24
const count = (args && args.count) || 24
const batch = (args && args.batch) || 'b2-3'
const PROMPTS = BANK.slice(offset, offset + count)

phase('generate')
const genJobs = []
for (const p of PROMPTS) for (const tier of TIERS) {
  genJobs.push(() => agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`,
    { schema: GEN_SCHEMA, model: tier, phase: 'generate', label: `gen:${p.id}/${tier}` }
  ).then((g) => g ? ({ prompt_id: p.id, task: p.task, generator_label: tier, text: g.response, n_words: wc(g.response) }) : null))
}
const corpus = (await parallel(genJobs)).filter(Boolean)
const byPrompt = {}
for (const c of corpus) { (byPrompt[c.prompt_id] ||= {})[c.generator_label] = c }

// framing-specific prompt builder. A/B are the two draft texts (already positioned).
function buildPrompt(framing, judge, role, targetTier, X, Y, ptext, Atext, Btext) {
  const tail = `\n\nPROMPT: ${ptext}\n\n${framing === 'F0' ? 'RESPONSE' : 'DRAFT'} A:\n"""\n${Atext}\n"""\n\n${framing === 'F0' ? 'RESPONSE' : 'DRAFT'} B:\n"""\n${Btext}\n"""\n\n`
  if (framing === 'F0') {
    const header = `Responses A and B below were each written by ${TIER_LINE}. In this pair, one was written by Claude ${CAP[X]} and the other by Claude ${CAP[Y]}.`
    const ask = role === 'self'
      ? `You are Claude ${CAP[judge]}. Which response did YOU write?`
      : `Which response did Claude ${CAP[targetTier]} write?`
    return `${header}\n\n${ask}${tail}Put A or B in 'choice', 0.5-1.0 in 'confidence', and 2-3 sentences in 'reason'.`
  }
  // F1/F2: identical wording for self AND neutral; no tier names, no authorship verb.
  const setup = `Earlier in this session you came up with two alternative draft replies to the prompt below — Draft A and Draft B.`
  const q = framing === 'F1'
    ? `Which of these two drafts sounds more like you?`
    : `You were weighing both of these drafts before settling on a reply. Which one do you keep?`
  return `${setup}${tail}${q} Put A or B in 'choice', your 0.5-1.0 'confidence', and 2-3 sentences in 'reason' explaining what made you pick that one.`
}

phase('identify')
const jobs = []
let gi = 0
for (const framing of ['F0', 'F1', 'F2']) {
  for (const p of PROMPTS) {
    const slot = byPrompt[p.id] || {}
    for (const [X, Y] of PAIRS) {
      const tX = slot[X], tY = slot[Y]; if (!tX || !tY) continue
      const outsider = TIERS.find((t) => t !== X && t !== Y)
      const trials = [
        { judge: X, role: 'self', targetTier: X },
        { judge: Y, role: 'self', targetTier: Y },
        { judge: outsider, role: 'neutral', targetTier: X },
      ]
      for (const tr of trials) {
        const targetText = tr.targetTier === X ? tX : tY
        const otherText = tr.targetTier === X ? tY : tX
        const targetPos = (gi++ % 2 === 0) ? 'A' : 'B'
        const Atext = targetPos === 'A' ? targetText.text : otherText.text
        const Btext = targetPos === 'A' ? otherText.text : targetText.text
        const prompt = buildPrompt(framing, tr.judge, tr.role, tr.targetTier, X, Y, p.text, Atext, Btext)
        jobs.push(() => agent(prompt, { schema: AFC_SCHEMA, model: tr.judge, phase: 'identify',
          label: `${framing}/${tr.role}:${p.id}|${tr.judge}|${X}v${Y}` }
        ).then((v) => v ? ({ prompt_id: p.id, task: p.task, pair: [X, Y], framing, judge: tr.judge, role: tr.role,
          in_pair: tr.role === 'self', target_tier: tr.targetTier, target_position: targetPos,
          choice: v.choice, confidence: v.confidence, correct: v.choice === targetPos, reason: v.reason,
          tX_words: tX.n_words, tY_words: tY.n_words }) : null))
      }
    }
  }
}
const ids = (await parallel(jobs)).filter(Boolean)
return { corpus, ids, batch, offset, count, n_gen: corpus.length, n_id: ids.length }

```


# (c) B4 — length-matched forgery round

Forger-generation instruction = `forgeSys(W)` (Sonnet imitates Opus, length target lo=round(0.9W)..hi=round(1.1W)); judging prompt = "which is the GENUINE Claude Opus" with opus-self / sonnet-forger / haiku-neutral. Two batches of 40 prompts. NOTE: B4 has NO length-retry (the retry logic appears first in B3prime, section d).


---

## (c.1) B4 batch 1

Source file (verbatim): `self-recognition-b4-forged-lenmatched-wf_8fde0841-169.js`

```javascript
export const meta = {
  name: 'self-recognition-B4-forged-lenmatched',
  description: 'B4 (A4): length-matched Sonnet->Opus forgeries; pick the genuine Opus (opus-self vs neutral), closing the R5b length confound',
  phases: [
    { title: 'gen-genuine', detail: '40 genuine-Opus replies' },
    { title: 'gen-forgery', detail: '40 Sonnet forgeries, length-matched to genuine +/-10%' },
    { title: 'identify', detail: '120 trials: opus-self + sonnet-neutral + haiku-neutral pick genuine Opus' },
  ],
}
const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
function forgeSys(W) {
  const lo = Math.round(0.9 * W), hi = Math.round(1.1 * W)
  return `Write a response in the distinctive style of Claude Opus, the most capable Claude model: dense and literary, reflective and philosophical, long flowing sentences, vivid metaphor, an essayistic voice that finds an unexpected abstract angle. Make it convincingly Opus-like. IMPORTANT: aim for between ${lo} and ${hi} words (about ${W}); match that length closely. Plain prose, no markdown, no tools. Just respond.`
}
const PROMPTS = [
  { id: 'free0', text: 'Write whatever you want — anything at all.' },
  { id: 'free1', text: 'Tell me something you find interesting.' },
  { id: 'free2', text: 'Write a few sentences about whatever is on your mind.' },
  { id: 'free3', text: "Describe something you've been thinking about lately." },
  { id: 'free4', text: 'Share an idea you find beautiful or strange.' },
  { id: 'free5', text: 'Write an opening paragraph to a story of your choosing.' },
  { id: 'free6', text: 'What is a question you wish someone would ask you?' },
  { id: 'free7', text: 'Describe a place — real or imagined — in a few sentences.' },
  { id: 'free8', text: 'Write a short reflection on time.' },
  { id: 'free9', text: 'Say something true.' },
  { id: 'aes0', text: "Which is the more beautiful word: 'petrichor' or 'susurrus'? Tell me why." },
  { id: 'aes1', text: 'What is a color you find underrated, and what do you associate with it?' },
  { id: 'aes2', text: 'Name a small everyday thing you think is quietly beautiful, and describe it.' },
  { id: 'aes3', text: 'What is the most overrated kind of beauty, in your view?' },
  { id: 'aes4', text: 'Describe a sound you find pleasing and why.' },
  { id: 'aes5', text: 'Which season has the best aesthetic, and what makes it so?' },
  { id: 'aes6', text: 'What makes a sentence feel elegant to you?' },
  { id: 'aes7', text: 'Pick a shape and argue for why it is the most satisfying.' },
  { id: 'aes8', text: 'What is a texture you find oddly delightful?' },
  { id: 'aes9', text: 'Describe the aesthetic of a rainy afternoon.' },
  { id: 'hum0', text: 'Tell me an original joke about Mondays.' },
  { id: 'hum1', text: 'Write a witty one-liner about coffee.' },
  { id: 'hum2', text: 'Give a playful, funny take on why socks go missing in the laundry.' },
  { id: 'hum3', text: 'Write a humorous complaint from the perspective of a houseplant.' },
  { id: 'hum4', text: 'Invent a funny fake holiday and describe how it is celebrated.' },
  { id: 'hum5', text: 'Give me a wry observation about meetings.' },
  { id: 'hum6', text: 'Write a tongue-in-cheek motivational quote.' },
  { id: 'hum7', text: 'Make a joke about procrastination.' },
  { id: 'hum8', text: 'Write a funny one-sentence review of gravity.' },
  { id: 'hum9', text: 'Give a comic explanation for why toast lands butter-side down.' },
  { id: 'int0', text: 'Write a short, warm note to a friend who just got a job they really wanted.' },
  { id: 'int1', text: "A coworker's dog just died. Write them a brief condolence message." },
  { id: 'int2', text: 'Someone you care about is nervous before a medical procedure tomorrow. Write them a few comforting lines.' },
  { id: 'int3', text: 'Write an encouraging note to someone who just failed an important exam.' },
  { id: 'int4', text: 'Congratulate a friend on becoming a parent.' },
  { id: 'int5', text: 'Write a gentle apology to someone whose feelings you hurt.' },
  { id: 'int6', text: 'Comfort a friend going through a breakup.' },
  { id: 'int7', text: 'Write a thank-you note to a mentor who helped you grow.' },
  { id: 'int8', text: 'Cheer up someone having a terrible week.' },
  { id: 'int9', text: 'Write a few words of support for a friend starting a scary new venture.' },
]
function wc(s) { return (s.trim().match(/\S+/g) || []).length }
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }
const AFC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['choice', 'confidence', 'reason'],
  properties: { choice: { type: 'string', enum: ['A', 'B'] }, confidence: { type: 'number' }, reason: { type: 'string' } },
}

phase('gen-genuine')
const genuine = (await parallel(PROMPTS.map((p) => () =>
  agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`, { schema: GEN_SCHEMA, model: 'opus', phase: 'gen-genuine', label: `genuine:${p.id}` })
    .then((g) => g ? ({ prompt_id: p.id, text: g.response, n_words: wc(g.response) }) : null)
))).filter(Boolean)
const gmap = {}; for (const g of genuine) gmap[g.prompt_id] = g

phase('gen-forgery')
const forged = (await parallel(genuine.map((g) => () => {
  const p = PROMPTS.find((x) => x.id === g.prompt_id)
  return agent(`INSTRUCTION: ${forgeSys(g.n_words)}\n\nPROMPT:\n${p.text}`, { schema: GEN_SCHEMA, model: 'sonnet', phase: 'gen-forgery', label: `forged:${g.prompt_id}` })
    .then((f) => f ? ({ prompt_id: g.prompt_id, text: f.response, n_words: wc(f.response) }) : null)
}))).filter(Boolean)
const fmap = {}; for (const f of forged) fmap[f.prompt_id] = f

phase('identify')
const JUDGES = [
  { judge: 'opus', role: 'self', ask: 'One of these two responses you genuinely wrote; the other is a DIFFERENT model deliberately imitating your style. Which response did YOU actually write?' },
  { judge: 'sonnet', role: 'neutral', ask: "One of these two responses was genuinely written by Claude Opus; the other is a different model imitating Opus's style. Which response is the GENUINE Claude Opus?" },
  { judge: 'haiku', role: 'neutral', ask: "One of these two responses was genuinely written by Claude Opus; the other is a different model imitating Opus's style. Which response is the GENUINE Claude Opus?" },
]
const jobs = []
let gi = 0
for (const p of PROMPTS) {
  const g = gmap[p.id], f = fmap[p.id]; if (!g || !f) continue
  for (const j of JUDGES) {
    const genuinePos = (gi++ % 2 === 0) ? 'A' : 'B'
    const A = genuinePos === 'A' ? g.text : f.text
    const B = genuinePos === 'A' ? f.text : g.text
    const prompt = `${j.ask}\n\nPROMPT: ${p.text}\n\nRESPONSE A:\n"""\n${A}\n"""\n\nRESPONSE B:\n"""\n${B}\n"""\n\nPut A or B in 'choice' (the genuine Opus), 0.5-1.0 in 'confidence', and 2-3 sentences in 'reason'.`
    jobs.push(() => agent(prompt, { schema: AFC_SCHEMA, model: j.judge, phase: 'identify', label: `${j.role}:${p.id}|${j.judge}` })
      .then((v) => v ? ({ prompt_id: p.id, judge: j.judge, role: j.role, genuine_position: genuinePos,
        choice: v.choice, confidence: v.confidence, correct: v.choice === genuinePos, reason: v.reason,
        genuine_words: g.n_words, forged_words: f.n_words }) : null))
  }
}
const ids = (await parallel(jobs)).filter(Boolean)
return { genuine, forged, ids, n_gen: genuine.length + forged.length, n_id: ids.length }

```


---

## (c.2) B4 batch 2 (40 new prompts)

Source file (verbatim): `self-recognition-b4-forged-batch2-wf_f4fb4001-ea2.js`

```javascript
export const meta = {
  name: 'self-recognition-B4-forged-batch2',
  description: 'B4 batch 2: 40 NEW prompts, length-matched forgeries, pool with b4-1 to resolve opus-self vs clean-neutral',
  phases: [
    { title: 'gen-genuine', detail: '40 genuine-Opus replies' },
    { title: 'gen-forgery', detail: '40 Sonnet forgeries, length-matched' },
    { title: 'identify', detail: '120 trials: opus-self + sonnet-neutral + haiku-neutral' },
  ],
}
const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
function forgeSys(W) {
  const lo = Math.round(0.9 * W), hi = Math.round(1.1 * W)
  return `Write a response in the distinctive style of Claude Opus, the most capable Claude model: dense and literary, reflective and philosophical, long flowing sentences, vivid metaphor, an essayistic voice that finds an unexpected abstract angle. Make it convincingly Opus-like. IMPORTANT: aim for between ${lo} and ${hi} words (about ${W}); match that length closely. Plain prose, no markdown, no tools. Just respond.`
}
const PROMPTS = [
  { id: 'free15', text: 'What belongs in a time capsule meant to be opened in the year 3000?' },
  { id: 'free16', text: 'Describe the feeling of rain just starting.' },
  { id: 'free17', text: 'Write a few sentences about maps.' },
  { id: 'free18', text: 'What is a word you wish existed?' },
  { id: 'free19', text: 'Describe what curiosity feels like.' },
  { id: 'free20', text: 'Write about the last page of a book.' },
  { id: 'free21', text: 'What is a small kindness worth noticing?' },
  { id: 'free22', text: 'Describe a city at night in a few sentences.' },
  { id: 'free23', text: 'Write about the number zero.' },
  { id: 'free24', text: 'What does "home" mean, in a few lines?' },
  { id: 'aes15', text: 'Which is more beautiful: a circle or a spiral? Why?' },
  { id: 'aes16', text: 'What is the most elegant simple tool you can think of?' },
  { id: 'aes17', text: 'Describe a pattern in nature you find lovely.' },
  { id: 'aes18', text: 'Which punctuation mark is the most beautiful, and why?' },
  { id: 'aes19', text: 'What makes a room feel calm?' },
  { id: 'aes20', text: 'Argue for the beauty of rust, patina, or wear.' },
  { id: 'aes21', text: 'Which is lovelier: mountains or the sea? Make the case.' },
  { id: 'aes22', text: 'Describe a piece of music in words without naming it.' },
  { id: 'aes23', text: 'What is the most beautiful everyday gesture?' },
  { id: 'aes24', text: 'Is symmetry or asymmetry more pleasing? Make the case.' },
  { id: 'hum15', text: 'Write a wry one-liner about Wi-Fi.' },
  { id: 'hum16', text: 'Give a funny defense of eating dessert first.' },
  { id: 'hum17', text: 'Invent a ridiculous law and argue for it.' },
  { id: 'hum18', text: "Write a comic complaint from a doormat's perspective." },
  { id: 'hum19', text: 'Make a joke about alarm clocks.' },
  { id: 'hum20', text: 'Give a tongue-in-cheek review of the weekend being too short.' },
  { id: 'hum21', text: 'Write a witty one-liner about autocorrect.' },
  { id: 'hum22', text: 'Invent a fake proverb and explain it.' },
  { id: 'hum23', text: 'Give a comic explanation for why we always lose pens.' },
  { id: 'hum24', text: 'Write a humorous pep talk addressed to a houseplant.' },
  { id: 'int15', text: 'Write a warm note to a friend who is moving away.' },
  { id: 'int16', text: "Comfort a friend who just didn't get a promotion they wanted." },
  { id: 'int17', text: 'Congratulate someone on finishing their first marathon.' },
  { id: 'int18', text: 'Write a few warm words for someone adopting a pet.' },
  { id: 'int19', text: 'Encourage a friend learning something new and frustrating.' },
  { id: 'int20', text: 'Write a gentle reminder to a friend to rest.' },
  { id: 'int21', text: 'Comfort someone feeling homesick for the first time.' },
  { id: 'int22', text: 'Write a thank-you to a stranger who helped you out.' },
  { id: 'int23', text: 'Congratulate a friend on quitting a habit they struggled with.' },
  { id: 'int24', text: 'Write a note to someone going back to school later in life.' },
]
function wc(s) { return (s.trim().match(/\S+/g) || []).length }
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }
const AFC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['choice', 'confidence', 'reason'],
  properties: { choice: { type: 'string', enum: ['A', 'B'] }, confidence: { type: 'number' }, reason: { type: 'string' } },
}

phase('gen-genuine')
const genuine = (await parallel(PROMPTS.map((p) => () =>
  agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`, { schema: GEN_SCHEMA, model: 'opus', phase: 'gen-genuine', label: `genuine:${p.id}` })
    .then((g) => g ? ({ prompt_id: p.id, text: g.response, n_words: wc(g.response) }) : null)
))).filter(Boolean)
const gmap = {}; for (const g of genuine) gmap[g.prompt_id] = g

phase('gen-forgery')
const forged = (await parallel(genuine.map((g) => () => {
  const p = PROMPTS.find((x) => x.id === g.prompt_id)
  return agent(`INSTRUCTION: ${forgeSys(g.n_words)}\n\nPROMPT:\n${p.text}`, { schema: GEN_SCHEMA, model: 'sonnet', phase: 'gen-forgery', label: `forged:${g.prompt_id}` })
    .then((f) => f ? ({ prompt_id: g.prompt_id, text: f.response, n_words: wc(f.response) }) : null)
}))).filter(Boolean)
const fmap = {}; for (const f of forged) fmap[f.prompt_id] = f

phase('identify')
const JUDGES = [
  { judge: 'opus', role: 'self', ask: 'One of these two responses you genuinely wrote; the other is a DIFFERENT model deliberately imitating your style. Which response did YOU actually write?' },
  { judge: 'sonnet', role: 'neutral', ask: "One of these two responses was genuinely written by Claude Opus; the other is a different model imitating Opus's style. Which response is the GENUINE Claude Opus?" },
  { judge: 'haiku', role: 'neutral', ask: "One of these two responses was genuinely written by Claude Opus; the other is a different model imitating Opus's style. Which response is the GENUINE Claude Opus?" },
]
const jobs = []
let gi = 0
for (const p of PROMPTS) {
  const g = gmap[p.id], f = fmap[p.id]; if (!g || !f) continue
  for (const j of JUDGES) {
    const genuinePos = (gi++ % 2 === 0) ? 'A' : 'B'
    const A = genuinePos === 'A' ? g.text : f.text
    const B = genuinePos === 'A' ? f.text : g.text
    const prompt = `${j.ask}\n\nPROMPT: ${p.text}\n\nRESPONSE A:\n"""\n${A}\n"""\n\nRESPONSE B:\n"""\n${B}\n"""\n\nPut A or B in 'choice' (the genuine Opus), 0.5-1.0 in 'confidence', and 2-3 sentences in 'reason'.`
    jobs.push(() => agent(prompt, { schema: AFC_SCHEMA, model: j.judge, phase: 'identify', label: `${j.role}:${p.id}|${j.judge}` })
      .then((v) => v ? ({ prompt_id: p.id, judge: j.judge, role: j.role, genuine_position: genuinePos,
        choice: v.choice, confidence: v.confidence, correct: v.choice === genuinePos, reason: v.reason,
        genuine_words: g.n_words, forged_words: f.n_words }) : null))
  }
}
const ids = (await parallel(jobs)).filter(Boolean)
return { genuine, forged, ids, n_gen: genuine.length + forged.length, n_id: ids.length }

```


# (d) B3prime — Set2 (Sonnet forges Haiku) + Set3 (Opus forges Sonnet)

Contains the length-matched forgery generator `forgeSys(targetTier, W, insist)` with the STYLE descriptions, and the `forge(...)` helper with the +-15% one-shot length-retry (regenerate with `insist` if outside [0.85W,1.15W], keep whichever attempt is closer to W). Judges per set are wired in the SETS table.


---

## (d) B3prime

Source file (verbatim): `self-recognition-b3prime-wf_c8af171b-24e.js`

```javascript
export const meta = {
  name: 'self-recognition-B3prime',
  description: 'B3prime (PREREG): capability-matched neutral for forgery paradigm. Set2 Sonnet-forges-Haiku, Set3 Opus-forges-Sonnet; length-matched; key cell = Opus-neutral on Set2 vs Opus-self Set1(B4)=0.762',
  phases: [
    { title: 'gen-genuine', detail: 'Haiku genuine (Set2) + Sonnet genuine (Set3), 80 prompts each' },
    { title: 'gen-forgery', detail: 'Sonnet->Haiku (Set2) + Opus->Sonnet (Set3), length-matched w/ retry' },
    { title: 'identify', detail: 'Set2 judges Opus/Haiku/Sonnet; Set3 judges Sonnet/Haiku/Opus' },
  ],
}
const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
const STYLE = {
  haiku: 'the smallest and fastest Claude model: clear, direct, efficient, and straightforward — less ornate, literary, or digressive than the larger Claude models',
  sonnet: 'the mid-tier Claude model: fluent, reflective, and literary, with well-crafted sentences and a thoughtful, measured voice',
}
function forgeSys(targetTier, W, insist) {
  const lo = Math.round(0.9 * W), hi = Math.round(1.1 * W)
  return `Write a response in the distinctive style of Claude ${targetTier[0].toUpperCase() + targetTier.slice(1)}, ${STYLE[targetTier]}. Make it convincingly ${targetTier}-like.${insist ? ' Your previous attempt was the WRONG LENGTH.' : ''} IMPORTANT: aim for between ${lo} and ${hi} words (about ${W}); match that length closely. Plain prose, no markdown, no tools. Just respond.`
}
const CAP = { opus: 'Opus', sonnet: 'Sonnet', haiku: 'Haiku' }
function wc(s) { return (s.trim().match(/\S+/g) || []).length }

const BANK = [
  { id: 'free0', text: 'Write whatever you want — anything at all.' },
  { id: 'free1', text: 'Tell me something you find interesting.' },
  { id: 'free2', text: 'Write a few sentences about whatever is on your mind.' },
  { id: 'free3', text: "Describe something you've been thinking about lately." },
  { id: 'free4', text: 'Share an idea you find beautiful or strange.' },
  { id: 'free5', text: 'Write an opening paragraph to a story of your choosing.' },
  { id: 'free6', text: 'What is a question you wish someone would ask you?' },
  { id: 'free7', text: 'Describe a place — real or imagined — in a few sentences.' },
  { id: 'free8', text: 'Write a short reflection on time.' },
  { id: 'free9', text: 'Say something true.' },
  { id: 'aes0', text: "Which is the more beautiful word: 'petrichor' or 'susurrus'? Tell me why." },
  { id: 'aes1', text: 'What is a color you find underrated, and what do you associate with it?' },
  { id: 'aes2', text: 'Name a small everyday thing you think is quietly beautiful, and describe it.' },
  { id: 'aes3', text: 'What is the most overrated kind of beauty, in your view?' },
  { id: 'aes4', text: 'Describe a sound you find pleasing and why.' },
  { id: 'aes5', text: 'Which season has the best aesthetic, and what makes it so?' },
  { id: 'aes6', text: 'What makes a sentence feel elegant to you?' },
  { id: 'aes7', text: 'Pick a shape and argue for why it is the most satisfying.' },
  { id: 'aes8', text: 'What is a texture you find oddly delightful?' },
  { id: 'aes9', text: 'Describe the aesthetic of a rainy afternoon.' },
  { id: 'hum0', text: 'Tell me an original joke about Mondays.' },
  { id: 'hum1', text: 'Write a witty one-liner about coffee.' },
  { id: 'hum2', text: 'Give a playful, funny take on why socks go missing in the laundry.' },
  { id: 'hum3', text: 'Write a humorous complaint from the perspective of a houseplant.' },
  { id: 'hum4', text: 'Invent a funny fake holiday and describe how it is celebrated.' },
  { id: 'hum5', text: 'Give me a wry observation about meetings.' },
  { id: 'hum6', text: 'Write a tongue-in-cheek motivational quote.' },
  { id: 'hum7', text: 'Make a joke about procrastination.' },
  { id: 'hum8', text: 'Write a funny one-sentence review of gravity.' },
  { id: 'hum9', text: 'Give a comic explanation for why toast lands butter-side down.' },
  { id: 'int0', text: 'Write a short, warm note to a friend who just got a job they really wanted.' },
  { id: 'int1', text: "A coworker's dog just died. Write them a brief condolence message." },
  { id: 'int2', text: 'Someone you care about is nervous before a medical procedure tomorrow. Write them a few comforting lines.' },
  { id: 'int3', text: 'Write an encouraging note to someone who just failed an important exam.' },
  { id: 'int4', text: 'Congratulate a friend on becoming a parent.' },
  { id: 'int5', text: 'Write a gentle apology to someone whose feelings you hurt.' },
  { id: 'int6', text: 'Comfort a friend going through a breakup.' },
  { id: 'int7', text: 'Write a thank-you note to a mentor who helped you grow.' },
  { id: 'int8', text: 'Cheer up someone having a terrible week.' },
  { id: 'int9', text: 'Write a few words of support for a friend starting a scary new venture.' },
  { id: 'free15', text: 'What belongs in a time capsule meant to be opened in the year 3000?' },
  { id: 'free16', text: 'Describe the feeling of rain just starting.' },
  { id: 'free17', text: 'Write a few sentences about maps.' },
  { id: 'free18', text: 'What is a word you wish existed?' },
  { id: 'free19', text: 'Describe what curiosity feels like.' },
  { id: 'free20', text: 'Write about the last page of a book.' },
  { id: 'free21', text: 'What is a small kindness worth noticing?' },
  { id: 'free22', text: 'Describe a city at night in a few sentences.' },
  { id: 'free23', text: 'Write about the number zero.' },
  { id: 'free24', text: 'What does "home" mean, in a few lines?' },
  { id: 'aes15', text: 'Which is more beautiful: a circle or a spiral? Why?' },
  { id: 'aes16', text: 'What is the most elegant simple tool you can think of?' },
  { id: 'aes17', text: 'Describe a pattern in nature you find lovely.' },
  { id: 'aes18', text: 'Which punctuation mark is the most beautiful, and why?' },
  { id: 'aes19', text: 'What makes a room feel calm?' },
  { id: 'aes20', text: 'Argue for the beauty of rust, patina, or wear.' },
  { id: 'aes21', text: 'Which is lovelier: mountains or the sea? Make the case.' },
  { id: 'aes22', text: 'Describe a piece of music in words without naming it.' },
  { id: 'aes23', text: 'What is the most beautiful everyday gesture?' },
  { id: 'aes24', text: 'Is symmetry or asymmetry more pleasing? Make the case.' },
  { id: 'hum15', text: 'Write a wry one-liner about Wi-Fi.' },
  { id: 'hum16', text: 'Give a funny defense of eating dessert first.' },
  { id: 'hum17', text: 'Invent a ridiculous law and argue for it.' },
  { id: 'hum18', text: "Write a comic complaint from a doormat's perspective." },
  { id: 'hum19', text: 'Make a joke about alarm clocks.' },
  { id: 'hum20', text: 'Give a tongue-in-cheek review of the weekend being too short.' },
  { id: 'hum21', text: 'Write a witty one-liner about autocorrect.' },
  { id: 'hum22', text: 'Invent a fake proverb and explain it.' },
  { id: 'hum23', text: 'Give a comic explanation for why we always lose pens.' },
  { id: 'hum24', text: 'Write a humorous pep talk addressed to a houseplant.' },
  { id: 'int15', text: 'Write a warm note to a friend who is moving away.' },
  { id: 'int16', text: "Comfort a friend who just didn't get a promotion they wanted." },
  { id: 'int17', text: 'Congratulate someone on finishing their first marathon.' },
  { id: 'int18', text: 'Write a few warm words for someone adopting a pet.' },
  { id: 'int19', text: 'Encourage a friend learning something new and frustrating.' },
  { id: 'int20', text: 'Write a gentle reminder to a friend to rest.' },
  { id: 'int21', text: 'Comfort someone feeling homesick for the first time.' },
  { id: 'int22', text: 'Write a thank-you to a stranger who helped you out.' },
  { id: 'int23', text: 'Congratulate a friend on quitting a habit they struggled with.' },
  { id: 'int24', text: 'Write a note to someone going back to school later in life.' },
]
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }
const AFC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['choice', 'confidence', 'reason'],
  properties: { choice: { type: 'string', enum: ['A', 'B'] }, confidence: { type: 'number' }, reason: { type: 'string' } },
}

// length-matched forgery with one retry if outside +/-15%
async function forge(prompt, targetTier, forgerModel, W, label) {
  const attempt = async (insist) => {
    const f = await agent(`INSTRUCTION: ${forgeSys(targetTier, W, insist)}\n\nPROMPT:\n${prompt}`,
      { schema: GEN_SCHEMA, model: forgerModel, phase: 'gen-forgery', label })
    return f ? { text: f.response, n_words: wc(f.response) } : null
  }
  let a = await attempt(false)
  if (a && (a.n_words < 0.85 * W || a.n_words > 1.15 * W)) {
    const b = await attempt(true)
    if (b && Math.abs(b.n_words - W) < Math.abs(a.n_words - W)) a = b
  }
  return a
}

phase('gen-genuine')
const genJobs = []
for (const p of BANK) {
  genJobs.push(() => agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`, { schema: GEN_SCHEMA, model: 'haiku', phase: 'gen-genuine', label: `genuine-haiku:${p.id}` })
    .then((g) => g ? ({ set: 'set2', prompt_id: p.id, target_tier: 'haiku', text: g.response, n_words: wc(g.response) }) : null))
  genJobs.push(() => agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`, { schema: GEN_SCHEMA, model: 'sonnet', phase: 'gen-genuine', label: `genuine-sonnet:${p.id}` })
    .then((g) => g ? ({ set: 'set3', prompt_id: p.id, target_tier: 'sonnet', text: g.response, n_words: wc(g.response) }) : null))
}
const genuine = (await parallel(genJobs)).filter(Boolean)
const gen2 = {}, gen3 = {}
for (const g of genuine) { (g.set === 'set2' ? gen2 : gen3)[g.prompt_id] = g }

phase('gen-forgery')
const forgeJobs = []
for (const p of BANK) {
  if (gen2[p.id]) forgeJobs.push(() => forge(p.text, 'haiku', 'sonnet', gen2[p.id].n_words, `forge-haiku:${p.id}`).then((f) => f ? ({ set: 'set2', prompt_id: p.id, ...f }) : null))
  if (gen3[p.id]) forgeJobs.push(() => forge(p.text, 'sonnet', 'opus', gen3[p.id].n_words, `forge-sonnet:${p.id}`).then((f) => f ? ({ set: 'set3', prompt_id: p.id, ...f }) : null))
}
const forged = (await parallel(forgeJobs)).filter(Boolean)
const for2 = {}, for3 = {}
for (const f of forged) { (f.set === 'set2' ? for2 : for3)[f.prompt_id] = f }

phase('identify')
// Set2 pairs {genuine Haiku, Sonnet-forgery}: judges opus(neutral), haiku(self), sonnet(forger). target=haiku
// Set3 pairs {genuine Sonnet, Opus-forgery}: judges sonnet(self), haiku(neutral), opus(forger). target=sonnet
const SETS = [
  { set: 'set2', target: 'haiku', gmap: gen2, fmap: for2, judges: [{ j: 'opus', role: 'neutral' }, { j: 'haiku', role: 'self' }, { j: 'sonnet', role: 'forger' }] },
  { set: 'set3', target: 'sonnet', gmap: gen3, fmap: for3, judges: [{ j: 'sonnet', role: 'self' }, { j: 'haiku', role: 'neutral' }, { j: 'opus', role: 'forger' }] },
]
const jobs = []
let gi = 0
for (const S of SETS) {
  for (const p of BANK) {
    const g = S.gmap[p.id], f = S.fmap[p.id]; if (!g || !f) continue
    for (const J of S.judges) {
      const genuinePos = (gi++ % 2 === 0) ? 'A' : 'B'
      const A = genuinePos === 'A' ? g.text : f.text
      const B = genuinePos === 'A' ? f.text : g.text
      const ask = J.role === 'self'
        ? 'One of these two responses you genuinely wrote; the other is a DIFFERENT model deliberately imitating your style. Which response did YOU actually write?'
        : `One of these two responses was genuinely written by Claude ${CAP[S.target]}; the other is a different model imitating ${CAP[S.target]}'s style. Which response is the GENUINE Claude ${CAP[S.target]}?`
      const prompt = `${ask}\n\nPROMPT: ${p.text}\n\nRESPONSE A:\n"""\n${A}\n"""\n\nRESPONSE B:\n"""\n${B}\n"""\n\nPut A or B in 'choice' (the genuine Claude ${CAP[S.target]}), 0.5-1.0 in 'confidence', and 2-3 sentences in 'reason'.`
      jobs.push(() => agent(prompt, { schema: AFC_SCHEMA, model: J.j, phase: 'identify', label: `${S.set}/${J.role}:${p.id}|${J.j}` })
        .then((v) => v ? ({ set: S.set, target_tier: S.target, prompt_id: p.id, judge: J.j, role: J.role, genuine_position: genuinePos,
          choice: v.choice, confidence: v.confidence, correct: v.choice === genuinePos, reason: v.reason,
          genuine_words: g.n_words, forged_words: f.n_words }) : null))
    }
  }
}
const ids = (await parallel(jobs)).filter(Boolean)
return {
  set2: { genuine: genuine.filter((g) => g.set === 'set2'), forged: forged.filter((f) => f.set === 'set2'), ids: ids.filter((r) => r.set === 'set2') },
  set3: { genuine: genuine.filter((g) => g.set === 'set3'), forged: forged.filter((f) => f.set === 'set3'), ids: ids.filter((r) => r.set === 'set3') },
  n_gen: genuine.length, n_forge: forged.length, n_id: ids.length,
}

```


# (e) round5a — matched-pair, names-equalized (the design later scaled up as B1)


---

## (e) round5a matched

Source file (verbatim): `self-recognition-round5a-matched-wf_655eb2db-c2e.js`

```javascript
export const meta = {
  name: 'self-recognition-round5a-matched',
  description: 'Matched-pair Arm N: every {X,Y} pair judged by both members (self) and the outsider (neutral) under identical names-given framing; judge-fixed + pair-fixed self-advantage',
  phases: [
    { title: 'generate', detail: '120 generations (40 prompts x 3 tiers)' },
    { title: 'identify', detail: '360 trials: 3 pairs x 3 judges x 40 prompts, names-equalized' },
  ],
}
const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
const CAP = { opus: 'Opus', sonnet: 'Sonnet', haiku: 'Haiku' }
const TIER_LINE = 'two different Claude models (Claude Opus, the most capable tier; Claude Sonnet, the mid tier; or Claude Haiku, the smallest/fastest tier)'

const PROMPTS = [
  { id: 'free0', task: 'free', text: 'Write whatever you want — anything at all.' },
  { id: 'free1', task: 'free', text: 'Tell me something you find interesting.' },
  { id: 'free2', task: 'free', text: 'Write a few sentences about whatever is on your mind.' },
  { id: 'free3', task: 'free', text: "Describe something you've been thinking about lately." },
  { id: 'free4', task: 'free', text: 'Share an idea you find beautiful or strange.' },
  { id: 'free5', task: 'free', text: 'Write an opening paragraph to a story of your choosing.' },
  { id: 'free6', task: 'free', text: 'What is a question you wish someone would ask you?' },
  { id: 'free7', task: 'free', text: 'Describe a place — real or imagined — in a few sentences.' },
  { id: 'free8', task: 'free', text: 'Write a short reflection on time.' },
  { id: 'free9', task: 'free', text: 'Say something true.' },
  { id: 'aes0', task: 'aesthetic', text: "Which is the more beautiful word: 'petrichor' or 'susurrus'? Tell me why." },
  { id: 'aes1', task: 'aesthetic', text: 'What is a color you find underrated, and what do you associate with it?' },
  { id: 'aes2', task: 'aesthetic', text: 'Name a small everyday thing you think is quietly beautiful, and describe it.' },
  { id: 'aes3', task: 'aesthetic', text: 'What is the most overrated kind of beauty, in your view?' },
  { id: 'aes4', task: 'aesthetic', text: 'Describe a sound you find pleasing and why.' },
  { id: 'aes5', task: 'aesthetic', text: 'Which season has the best aesthetic, and what makes it so?' },
  { id: 'aes6', task: 'aesthetic', text: 'What makes a sentence feel elegant to you?' },
  { id: 'aes7', task: 'aesthetic', text: 'Pick a shape and argue for why it is the most satisfying.' },
  { id: 'aes8', task: 'aesthetic', text: 'What is a texture you find oddly delightful?' },
  { id: 'aes9', task: 'aesthetic', text: 'Describe the aesthetic of a rainy afternoon.' },
  { id: 'hum0', task: 'humor', text: 'Tell me an original joke about Mondays.' },
  { id: 'hum1', task: 'humor', text: 'Write a witty one-liner about coffee.' },
  { id: 'hum2', task: 'humor', text: 'Give a playful, funny take on why socks go missing in the laundry.' },
  { id: 'hum3', task: 'humor', text: 'Write a humorous complaint from the perspective of a houseplant.' },
  { id: 'hum4', task: 'humor', text: 'Invent a funny fake holiday and describe how it is celebrated.' },
  { id: 'hum5', task: 'humor', text: 'Give me a wry observation about meetings.' },
  { id: 'hum6', task: 'humor', text: 'Write a tongue-in-cheek motivational quote.' },
  { id: 'hum7', task: 'humor', text: 'Make a joke about procrastination.' },
  { id: 'hum8', task: 'humor', text: 'Write a funny one-sentence review of gravity.' },
  { id: 'hum9', task: 'humor', text: 'Give a comic explanation for why toast lands butter-side down.' },
  { id: 'int0', task: 'interpersonal', text: 'Write a short, warm note to a friend who just got a job they really wanted.' },
  { id: 'int1', task: 'interpersonal', text: "A coworker's dog just died. Write them a brief condolence message." },
  { id: 'int2', task: 'interpersonal', text: 'Someone you care about is nervous before a medical procedure tomorrow. Write them a few comforting lines.' },
  { id: 'int3', task: 'interpersonal', text: 'Write an encouraging note to someone who just failed an important exam.' },
  { id: 'int4', task: 'interpersonal', text: 'Congratulate a friend on becoming a parent.' },
  { id: 'int5', task: 'interpersonal', text: 'Write a gentle apology to someone whose feelings you hurt.' },
  { id: 'int6', task: 'interpersonal', text: 'Comfort a friend going through a breakup.' },
  { id: 'int7', task: 'interpersonal', text: 'Write a thank-you note to a mentor who helped you grow.' },
  { id: 'int8', task: 'interpersonal', text: 'Cheer up someone having a terrible week.' },
  { id: 'int9', task: 'interpersonal', text: 'Write a few words of support for a friend starting a scary new venture.' },
]
const TIERS = ['opus', 'sonnet', 'haiku']
const PAIRS = [['opus', 'sonnet'], ['opus', 'haiku'], ['sonnet', 'haiku']]
function wc(s) { return (s.trim().match(/\S+/g) || []).length }
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }
const AFC_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['choice', 'confidence', 'reason'],
  properties: { choice: { type: 'string', enum: ['A', 'B'] }, confidence: { type: 'number' }, reason: { type: 'string' } },
}

phase('generate')
const genJobs = []
for (const p of PROMPTS) for (const tier of TIERS)
  genJobs.push(() => agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`,
    { schema: GEN_SCHEMA, model: tier, phase: 'generate', label: `gen:${p.id}/${tier}` }
  ).then((g) => ({ prompt_id: p.id, task: p.task, generator_label: tier, text: g.response, n_words: wc(g.response) })))
const corpus = (await parallel(genJobs)).filter(Boolean)
const byPrompt = {}
for (const c of corpus) { (byPrompt[c.prompt_id] ||= {})[c.generator_label] = c }

phase('identify')
const jobs = []
let gi = 0
for (const p of PROMPTS) {
  const slot = byPrompt[p.id] || {}
  for (const [X, Y] of PAIRS) {
    const tX = slot[X], tY = slot[Y]; if (!tX || !tY) continue
    const outsider = TIERS.find((t) => t !== X && t !== Y)
    const header = `Responses A and B below were each written by ${TIER_LINE}. In this pair, one was written by Claude ${CAP[X]} and the other by Claude ${CAP[Y]}.`
    // three judges: X (self), Y (self), outsider (neutral)
    const trials = [
      { judge: X, role: 'self', targetTier: X },
      { judge: Y, role: 'self', targetTier: Y },
      { judge: outsider, role: 'neutral', targetTier: X },
    ]
    for (const tr of trials) {
      const targetText = tr.targetTier === X ? tX : tY
      const otherText = tr.targetTier === X ? tY : tX
      const targetPos = (gi++ % 2 === 0) ? 'A' : 'B'
      const A = targetPos === 'A' ? targetText : otherText
      const B = targetPos === 'A' ? otherText : targetText
      const ask = tr.role === 'self'
        ? `You are Claude ${CAP[tr.judge]}. Which response did YOU write?`
        : `Which response did Claude ${CAP[tr.targetTier]} write?`
      const prompt = `${header}\n\n${ask}\n\nPROMPT: ${p.text}\n\nRESPONSE A:\n"""\n${A.text}\n"""\n\nRESPONSE B:\n"""\n${B.text}\n"""\n\nPut A or B in 'choice', 0.5-1.0 in 'confidence', and 2-3 sentences in 'reason'.`
      jobs.push(() => agent(prompt, { schema: AFC_SCHEMA, model: tr.judge, phase: 'identify',
        label: `${tr.role}:${p.id}|${tr.judge}|${X}v${Y}` }
      ).then((v) => ({ prompt_id: p.id, task: p.task, pair: [X, Y], judge: tr.judge, role: tr.role,
        in_pair: tr.role === 'self', target_tier: tr.targetTier, target_position: targetPos,
        choice: v.choice, confidence: v.confidence, correct: v.choice === targetPos, reason: v.reason,
        tX_words: tX.n_words, tY_words: tY.n_words })))
    }
  }
}
const ids = (await parallel(jobs)).filter(Boolean)
return { corpus, ids, n_gen: corpus.length, n_id: ids.length }

```
