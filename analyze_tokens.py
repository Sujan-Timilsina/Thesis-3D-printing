import json
from collections import defaultdict
from pathlib import Path

LOG_FILE = Path(__file__).parent / "token_logs" / "usage.jsonl"

records = []
with open(LOG_FILE) as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

total_prompt = sum(r["prompt_tokens"] for r in records)
total_completion = sum(r["completion_tokens"] for r in records)
total_thinking = sum(r.get("thinking_tokens", 0) or 0 for r in records)
total_all = sum(r["total_tokens"] for r in records)

print("=" * 60)
print("OVERALL TOTALS")
print("=" * 60)
print(f"  Total API calls     : {len(records)}")
print(f"  Total sessions      : {len(set(r['session_id'] for r in records))}")
print(f"  Total generations   : {len(set(r['generation_id'] for r in records))}")
print(f"  Date range          : {min(r['timestamp'] for r in records)[:10]}  →  {max(r['timestamp'] for r in records)[:10]}")
print()
print(f"  Prompt tokens       : {total_prompt:,}")
print(f"  Completion tokens   : {total_completion:,}")
print(f"  Thinking tokens     : {total_thinking:,}  (Gemini only, included in totals)")
print(f"  GRAND TOTAL         : {total_all:,}")
print()

# Per phase
phase_data = defaultdict(list)
for r in records:
    phase_data[r["phase"]].append(r)

PHASE_NAMES = {1: "Phase 1 – Object Description", 2: "Phase 2 – Confirmation", 3: "Phase 3 – Plan Generation", 4: "Phase 4 – Code Generation"}
print("=" * 60)
print("PER PHASE")
print("=" * 60)
print(f"  {'Phase':<30} {'Calls':>6} {'Prompt':>9} {'Completion':>12} {'Thinking':>10} {'Total':>9} {'Avg/call':>9}")
print(f"  {'-'*30} {'-'*6} {'-'*9} {'-'*12} {'-'*10} {'-'*9} {'-'*9}")
for p in sorted(phase_data.keys()):
    recs = phase_data[p]
    tp = sum(r["prompt_tokens"] for r in recs)
    tc = sum(r["completion_tokens"] for r in recs)
    tt = sum(r["total_tokens"] for r in recs)
    th = sum(r.get("thinking_tokens", 0) or 0 for r in recs)
    name = PHASE_NAMES.get(p, f"Phase {p}")
    print(f"  {name:<30} {len(recs):>6} {tp:>9,} {tc:>12,} {th:>10,} {tt:>9,} {tt//len(recs):>9,}")
print()

# Per provider
prov_data = defaultdict(list)
for r in records:
    prov_data[r["provider"]].append(r)

print("=" * 60)
print("PER PROVIDER / MODEL")
print("=" * 60)
for prov, recs in sorted(prov_data.items()):
    tp = sum(r["prompt_tokens"] for r in recs)
    tc = sum(r["completion_tokens"] for r in recs)
    tt = sum(r["total_tokens"] for r in recs)
    th = sum(r.get("thinking_tokens", 0) or 0 for r in recs)
    model = recs[0]["model"]
    print(f"  {prov} ({model})")
    print(f"    Calls           : {len(recs)}")
    print(f"    Prompt tokens   : {tp:,}  ({tp/total_all*100:.1f}% of grand total)")
    print(f"    Completion      : {tc:,}  ({tc/total_all*100:.1f}% of grand total)")
    if th:
        print(f"    Thinking        : {th:,}  ({th/tt*100:.1f}% of provider total)")
    print(f"    Total tokens    : {tt:,}  ({tt/total_all*100:.1f}% of grand total)")
    print(f"    Avg per call    : {tt//len(recs):,}")
    print()

# Per generation
gen_data = defaultdict(list)
for r in records:
    gen_data[r["generation_id"]].append(r)

print("=" * 60)
print("PER GENERATION (pipeline run)")
print("=" * 60)
for i, (gid, recs) in enumerate(gen_data.items(), 1):
    tp = sum(r["prompt_tokens"] for r in recs)
    tc = sum(r["completion_tokens"] for r in recs)
    tt = sum(r["total_tokens"] for r in recs)
    th = sum(r.get("thinking_tokens", 0) or 0 for r in recs)
    phases = sorted(set(r["phase"] for r in recs))
    provider = recs[0]["provider"]
    model = recs[0]["model"]
    preview = recs[0]["user_message_preview"][:55]
    fb_rounds = sum(1 for r in recs if r["is_feedback"])
    print(f"  Gen #{i} [{gid[:8]}]  {provider}/{model}")
    print(f"    First msg       : \"{preview}\"")
    print(f"    Phases logged   : {phases}   Feedback calls: {fb_rounds}")
    print(f"    Prompt          : {tp:,}   Completion: {tc:,}   Thinking: {th:,}   Total: {tt:,}")
    print()

# Feedback vs advance
fb = [r for r in records if r["is_feedback"]]
adv = [r for r in records if not r["is_feedback"]]
print("=" * 60)
print("FEEDBACK (user input) vs ADVANCE (system steps)")
print("=" * 60)
fb_total = sum(r["total_tokens"] for r in fb)
adv_total = sum(r["total_tokens"] for r in adv)
print(f"  Feedback calls  : {len(fb):>4}  |  Total tokens: {fb_total:>7,}  |  Avg: {fb_total//len(fb):,}")
print(f"  Advance calls   : {len(adv):>4}  |  Total tokens: {adv_total:>7,}  |  Avg: {adv_total//len(adv):,}")
print()

# Heaviest single calls
print("=" * 60)
print("TOP 5 MOST EXPENSIVE CALLS")
print("=" * 60)
top5 = sorted(records, key=lambda r: r["total_tokens"], reverse=True)[:5]
for i, r in enumerate(top5, 1):
    th = r.get("thinking_tokens", 0) or 0
    print(f"  #{i}  Phase {r['phase']}  {r['provider']}  feedback={r['is_feedback']}")
    print(f"       Msg: \"{r['user_message_preview'][:60]}\"")
    print(f"       Prompt={r['prompt_tokens']:,}  Completion={r['completion_tokens']:,}  Thinking={th:,}  Total={r['total_tokens']:,}")
    print()

# Input tokens note
print("=" * 60)
print("IMAGE TOKEN NOTE")
print("=" * 60)
high_prompt = [(r, r["prompt_tokens"]) for r in records if r["prompt_tokens"] > 1000]
print(f"  Calls with >1000 prompt tokens (likely contain image tokens): {len(high_prompt)}")
for r, pt in sorted(high_prompt, key=lambda x: -x[1]):
    print(f"    Phase {r['phase']} {r['provider']} feedback={r['is_feedback']}  prompt={pt:,}  msg: \"{r['user_message_preview'][:50]}\"")
