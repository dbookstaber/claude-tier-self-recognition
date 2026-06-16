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

