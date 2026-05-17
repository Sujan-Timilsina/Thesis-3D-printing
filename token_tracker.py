"""
Token usage tracker — logs every API call to a persistent JSON-lines file
and provides aggregation helpers for analysis.

Each record:
{
  "timestamp": "ISO-8601",
  "session_id": "<uuid>",
  "generation_id": "<uuid>",       # one per full 4-phase cycle
  "phase": 1-4,
  "is_feedback": true/false,        # typed feedback vs advance action
  "provider": "openai" | "gemini",
  "model": "gpt-5-mini" | "gemini-3.1-pro-preview" | ...,
  "prompt_tokens": int,
  "completion_tokens": int,
  "total_tokens": int,
  "thinking_tokens": int | null,    # Gemini thinking tokens
  "user_message_preview": "first 120 chars..."
}
"""

import json
import os
import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "token_logs"
LOG_FILE = LOG_DIR / "usage.jsonl"


def _ensure_dir():
    LOG_DIR.mkdir(exist_ok=True)


def log_usage(
    session_id: str,
    generation_id: str,
    phase: int,
    is_feedback: bool,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    thinking_tokens: int = 0,
    user_message_preview: str = "",
):
    """Append one usage record to the JSONL log file."""
    _ensure_dir()
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "session_id": session_id,
        "generation_id": generation_id,
        "phase": phase,
        "is_feedback": is_feedback,
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "thinking_tokens": thinking_tokens,
        "user_message_preview": (user_message_preview or "")[:120],
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[TOKEN] phase={phase} feedback={is_feedback} prompt={prompt_tokens} "
          f"completion={completion_tokens} total={total_tokens} thinking={thinking_tokens}")


def load_all_records():
    """Load every record from the log file."""
    if not LOG_FILE.exists():
        return []
    records = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def get_summary():
    """
    Return a dict with aggregated stats:
      - total_calls, total_tokens, total_prompt, total_completion
      - per_phase: {1: {calls, avg_prompt, avg_completion, avg_total}, ...}
      - per_generation: [{generation_id, total_tokens, phases_used, feedback_rounds}, ...]
      - feedback_stats: {calls, avg_tokens}
      - advance_stats: {calls, avg_tokens}
      - per_provider: {provider: {calls, avg_total}, ...}
    """
    records = load_all_records()
    if not records:
        return None

    summary = {
        "total_calls": len(records),
        "total_tokens": sum(r["total_tokens"] for r in records),
        "total_prompt": sum(r["prompt_tokens"] for r in records),
        "total_completion": sum(r["completion_tokens"] for r in records),
        "total_thinking": sum(r.get("thinking_tokens", 0) or 0 for r in records),
        "per_phase": {},
        "per_generation": [],
        "feedback_stats": {"calls": 0, "total_tokens": 0},
        "advance_stats": {"calls": 0, "total_tokens": 0},
        "per_provider": {},
    }

    # Per phase
    from collections import defaultdict
    phase_data = defaultdict(list)
    for r in records:
        phase_data[r["phase"]].append(r)
    for p in sorted(phase_data.keys()):
        recs = phase_data[p]
        summary["per_phase"][p] = {
            "calls": len(recs),
            "avg_prompt": round(sum(r["prompt_tokens"] for r in recs) / len(recs)),
            "avg_completion": round(sum(r["completion_tokens"] for r in recs) / len(recs)),
            "avg_total": round(sum(r["total_tokens"] for r in recs) / len(recs)),
        }

    # Per generation
    gen_data = defaultdict(list)
    for r in records:
        gen_data[r["generation_id"]].append(r)
    for gid, recs in gen_data.items():
        summary["per_generation"].append({
            "generation_id": gid,
            "total_tokens": sum(r["total_tokens"] for r in recs),
            "total_prompt": sum(r["prompt_tokens"] for r in recs),
            "total_completion": sum(r["completion_tokens"] for r in recs),
            "phases_used": sorted(set(r["phase"] for r in recs)),
            "feedback_rounds": sum(1 for r in recs if r["is_feedback"]),
            "advance_rounds": sum(1 for r in recs if not r["is_feedback"]),
            "calls": len(recs),
        })

    # Feedback vs advance
    fb = [r for r in records if r["is_feedback"]]
    adv = [r for r in records if not r["is_feedback"]]
    summary["feedback_stats"] = {
        "calls": len(fb),
        "total_tokens": sum(r["total_tokens"] for r in fb),
        "avg_tokens": round(sum(r["total_tokens"] for r in fb) / len(fb)) if fb else 0,
    }
    summary["advance_stats"] = {
        "calls": len(adv),
        "total_tokens": sum(r["total_tokens"] for r in adv),
        "avg_tokens": round(sum(r["total_tokens"] for r in adv) / len(adv)) if adv else 0,
    }

    # Per provider
    prov_data = defaultdict(list)
    for r in records:
        prov_data[r["provider"]].append(r)
    for prov, recs in prov_data.items():
        summary["per_provider"][prov] = {
            "calls": len(recs),
            "total_tokens": sum(r["total_tokens"] for r in recs),
            "avg_total": round(sum(r["total_tokens"] for r in recs) / len(recs)),
        }

    return summary
