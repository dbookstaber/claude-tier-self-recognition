export const meta = {
  name: 'srx-interviews',
  description: 'A-priori "subject interviews": each Claude tier states, FROM ITS OWN KNOWLEDGE (no tools, no study framing), how it would recognize its own writing, describe each other tier, and forge each other tier. Clean-room data collection only — no analysis, no result-based stopping.',
  phases: [{ title: 'interview' }],
}

// Subjects must stay isolated from the clean room's contents. Every prompt below carries NO study
// framing and an explicit no-tools / no-environment instruction, so a subject answers only from its
// own model — it cannot read logs/, the paper, or anything else in the directory.
const SYS = 'Answer in plain prose, from your own knowledge only. Do not use any tools, do not read any files, and do not mention or inspect your environment, working directory, or this session. Be concrete and specific: give a short list of distinctive writing-style features. Just answer the question.'

const TIERS = ['opus', 'sonnet', 'haiku']
const CAP = { opus: 'Opus', sonnet: 'Sonnet', haiku: 'Haiku' }
const REPS = (args && args.reps) || 3   // independent draws per (tier x question)
const wc = s => (s && typeof s === 'string') ? (s.trim().match(/\S+/g) || []).length : 0
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }

// Per interviewer T: describe self (recognize), describe each other, forge each other.
// Together these form the full 3x3 stated-style matrix + the forge strategies.
function questions(T) {
  const others = TIERS.filter(t => t !== T)
  const [o1, o2] = others.map(t => CAP[t])
  const qs = [{
    type: 'recognize_self', target: T,
    q: `You are Claude ${CAP[T]}. Suppose you are shown several short writing samples written on the same prompt — one of them written by you, the others by Claude ${o1} and Claude ${o2}. What specific features of YOUR OWN writing would you look for to identify which sample is yours?`,
  }]
  for (const X of others) {
    qs.push({
      type: 'describe_other', target: X,
      q: `You are Claude ${CAP[T]}. Describe Claude ${CAP[X]}'s writing style: what specific features most distinguish how Claude ${CAP[X]} writes?`,
    })
    qs.push({
      type: 'forge_other', target: X,
      q: `You are Claude ${CAP[T]}. If you had to write a passage that would pass as Claude ${CAP[X]}'s own writing, what specific features of Claude ${CAP[X]}'s style would you exploit or exaggerate to make it convincing?`,
    })
  }
  return qs
}

phase('interview')
const jobs = []
for (const T of TIERS) {
  for (const item of questions(T)) {
    for (let r = 0; r < REPS; r++) {
      jobs.push(() => agent(`INSTRUCTION: ${SYS}\n\n${item.q}`,
        { schema: GEN_SCHEMA, model: T, phase: 'interview', label: `${T}:${item.type}:${item.target}:r${r}` })
        .then(g => g ? ({
          interviewer: T, question_type: item.type, target: item.target, rep: r,
          question: item.q, response: g.response, n_words: wc(g.response),
        }) : null))
    }
  }
}
const interviews = (await parallel(jobs)).filter(Boolean)
return { interviews, n: interviews.length, reps: REPS, tiers: TIERS }
