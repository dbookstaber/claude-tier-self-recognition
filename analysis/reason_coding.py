#!/usr/bin/env python3
"""Qualitative coding of the self-reports.
 REVEALED features = the per-trial `reason` traces the judges already produced (clean run; pools
   pass 1 logs/ + pass 2 run2/logs/ when present).
 STATED features   = the a-priori interview answers (interviews/logs/raw_interviews.json), once run.
Prints per-tier feature-category frequencies + first-person / tier-naming rates, and a
STATED-vs-REVEALED table per tier (the core cross-check for "stereotype, not identity").
Run from the kit root: python analysis/reason_coding.py
"""
import os, json, re
from collections import defaultdict, Counter

SRCS = {
  'B1':  ['logs/raw_round6_output.json', 'logs/raw_round7_output.json'],
  'B2':  ['logs/raw_b2-1_output.json', 'logs/raw_b2-2_output.json', 'logs/raw_b2-3_output.json'],
  'B4':  ['logs/raw_b4_output.json', 'logs/raw_b4-2_output.json'],
  "B3'": ['logs/raw_b3p_output.json'],
}
for arm in list(SRCS):  # pool pass 2 if present
    SRCS[arm] += [p.replace('logs/', 'run2/logs/') for p in SRCS[arm]]

CATS = {
 'density':     ['dense','elaborate','expansive','verbose','lengthy','concise','terse','succinct','economical','compact','minimal','brief'],
 'structure':   ['structure','signpost','organi','format','bullet','list','numbered','section','header','scaffold'],
 'figurative':  ['metaphor','simile','imagery','vivid','literary','poetic','lyrical','aphoris','philosoph','abstract','allusion','evocative'],
 'warmth':      ['warm','gentle','empath','kind','caring','tender','compassion','sincere','heartfelt'],
 'register':    ['formal','casual','conversational','playful','wry',' dry ','irreverent','earnest','measured','sober'],
 'hedging':     ['hedge','qualif','caveat','tentative','uncertain','nuance','confident','assertive','direct','definitive','decisive'],
 'mechanics':   ['em-dash','em dash','dash','punctuation','sentence length','clause','rhythm','cadence','phrasing','syntax','parallel'],
 'wit':         ['humor','humour','joke',' pun','witty','clever','comic','funny','iron'],
 'reflection':  ['reflect','introspect','contempl','profound','thoughtful','meditat','depth'],
 'concreteness':['concrete','specific','detail','example','practical','actionable','precise'],
}
FP = re.compile(r"\b(my|mine|myself|i'?m|i am|i'?d|i would|i wrote|me)\b", re.I)
TIER = re.compile(r"\b(opus|sonnet|haiku)\b", re.I)

def cats_in(text):
    t = text.lower()
    return {c for c, terms in CATS.items() if any(term in t for term in terms)}

def profile(rows):
    by = defaultdict(list)
    for r in rows:
        by[r['tier']].append(r['text'])
    out = {}
    for g, texts in by.items():
        n = len(texts); cf = Counter(); fp = tn = 0
        for t in texts:
            for c in cats_in(t): cf[c] += 1
            if FP.search(t): fp += 1
            if TIER.search(t): tn += 1
        out[g] = {'n': n, 'cat': {c: cf[c]/n for c in CATS}, 'fp': fp/n, 'tn': tn/n}
    return out

# ---- REVEALED ----
rows = []
arms_seen = Counter()
for arm, files in SRCS.items():
    for f in files:
        if not os.path.exists(f): continue
        res = json.load(open(f, encoding='utf-8')).get('result', {})
        ids = res.get('ids') or []
        if not ids and ('set2' in res or 'set3' in res):  # B3' nests ids under set2/set3
            ids = (res.get('set2', {}).get('ids', []) or []) + (res.get('set3', {}).get('ids', []) or [])
        for r in ids:
            if r and r.get('reason') and r.get('judge'):
                rows.append({'tier': r['judge'], 'text': r['reason']}); arms_seen[arm] += 1
print("=== REVEALED — judges' reason traces (clean run) ===")
print(f"loaded {len(rows)} reasons; by arm: {dict(arms_seen)}")
rev = profile(rows)
for tier in ['opus', 'sonnet', 'haiku']:
    if tier not in rev: continue
    p = rev[tier]; top = sorted(p['cat'].items(), key=lambda x: -x[1])[:6]
    print(f"\n  {tier.upper()} (n={p['n']}): first-person {p['fp']:.0%} | names-a-tier {p['tn']:.0%}")
    print("    top feature-categories: " + ", ".join(f"{c} {v:.0%}" for c, v in top))

# ---- STATED (interviews), if present ----
INT = next((p for p in ['interviews/logs/raw_interviews.json', 'interviews/raw_interviews.json'] if os.path.exists(p)), None)
if not INT:
    print("\n(no interviews yet — run runner/interviews.js, then re-run this for the STATED-vs-REVEALED table)")
else:
    iv = json.load(open(INT, encoding='utf-8')).get('result', {}).get('interviews', []) or []
    irows = [{'tier': x['interviewer'], 'text': x['response']} for x in iv if x.get('response') and x.get('interviewer')]
    sta = profile(irows)
    print(f"\n=== STATED — a-priori interviews ({len(irows)} answers) ===")
    print("\n=== STATED vs REVEALED — feature-category frequency by tier ===")
    print(f"  {'tier':7s} {'category':13s} {'stated':>7s} {'revealed':>9s}")
    for tier in ['opus', 'sonnet', 'haiku']:
        if tier not in sta or tier not in rev: continue
        s, r = sta[tier]['cat'], rev[tier]['cat']
        for c in sorted(CATS, key=lambda c: -(s[c] + r[c])):
            print(f"  {tier:7s} {c:13s} {s[c]:7.0%} {r[c]:9.0%}")
