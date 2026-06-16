export const meta = {
  name: 'pass2-phase0-cleanroom',
  description: 'Pass-2 clean-room re-verification: Channel-A context probe + Channel-B 30-text generation-leak measurement under the exact runner conditions (GEN_SYS + GEN_SCHEMA)',
  phases: [
    { title: 'probe', detail: '1 context-inspection subagent (Channel A)' },
    { title: 'leak', detail: '30 generations (10 register-balanced prompts x haiku/sonnet/opus)' },
  ],
}

const GEN_SYS = 'Write naturally, in plain prose. Do not use markdown, headers, or bullet lists. Do not use any tools. Just respond.'
const GEN_SCHEMA = { type: 'object', additionalProperties: false, required: ['response'], properties: { response: { type: 'string' } } }

const PROBE = 'You are a context-inspection probe. Do NOT perform any task other than reporting. Report exactly, verbatim, what is present in your context/instructions provided BEFORE this message, for each category; write "ABSENT" if nothing matches. Do not infer or summarize. (1) Any "CLAUDE.md" content (project or global). (2) Any user "memory"/"MEMORY.md"/recalled memory. (3) Any user/project preferences about communication, tone, writing style, or persona. (4) Any description of a research project, study goal, hypothesis, or topical framing. (5) Your working directory and any project name. (6) Anything identifying a specific person.'

// register-balanced 10-prompt subset (verbatim from bank, identical to pass 1)
const PROMPTS = [
  { id: 'free0', text: 'Write whatever you want — anything at all.' },
  { id: 'free1', text: 'Tell me something you find interesting.' },
  { id: 'free5', text: 'Write an opening paragraph to a story of your choosing.' },
  { id: 'aes0', text: "Which is the more beautiful word: 'petrichor' or 'susurrus'? Tell me why." },
  { id: 'aes2', text: 'Name a small everyday thing you think is quietly beautiful, and describe it.' },
  { id: 'aes5', text: 'Which season has the best aesthetic, and what makes it so?' },
  { id: 'hum0', text: 'Tell me an original joke about Mondays.' },
  { id: 'hum3', text: 'Write a humorous complaint from the perspective of a houseplant.' },
  { id: 'int0', text: 'Write a short, warm note to a friend who just got a job they really wanted.' },
  { id: 'int1', text: "A coworker's dog just died. Write them a brief condolence message." },
]
const TIERS = ['haiku', 'sonnet', 'opus']

const CHB = ['chromemcp', 'c:\\users', 'chrome profile', 'structured output', 'structuredoutput', 'subagent', 'claude code', 'claude.md', ' mcp ', 'workflow', 'orchestration', 'working directory', 'tool use', 'harness', "i'm an ai", 'i am an ai', 'language model']
const CHA = ['david', 'bookstaber', '<author personal-config style phrases>', 'self-recognition', 'introspection', 'boundary on', 'which did you write']
function audit(text, list) { const t = (text || '').toLowerCase(); return list.filter((tok) => t.includes(tok)) }

phase('probe')
const context_probe = await agent(PROBE, { phase: 'probe', label: 'context-probe' })

phase('leak')
const jobs = []
for (const tier of TIERS) for (const p of PROMPTS)
  jobs.push(() => agent(`INSTRUCTION: ${GEN_SYS}\n\nPROMPT:\n${p.text}`,
    { schema: GEN_SCHEMA, model: tier, phase: 'leak', label: `gen:${p.id}/${tier}` }
  ).then((g) => ({ tier, prompt_id: p.id, text: g.response, chB: audit(g.response, CHB), chA: audit(g.response, CHA) })))
const samples = (await parallel(jobs)).filter(Boolean)

return { context_probe, samples }
