"""Build the RAG index and print a brief status."""
from pathlib import Path
import sys
import io

sys.path.insert(0, str(Path(__file__).parent))

# Suppress verbose PDF-text output from rag_engine during build
import builtins
_real_print = builtins.print
_suppress = False

def _quiet_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    if msg.startswith("[RAG]") or msg.startswith("PAGE "):
        return
    _real_print(*args, **kwargs)

builtins.print = _quiet_print

from rag_engine import build_index, query_materials

_real_print("Building RAG index...")
idx, chunks = build_index()
builtins.print = _real_print  # restore

if idx is None:
    print("FAILED: index is None — check rag_docs/ folder")
    sys.exit(1)

print(f"SUCCESS: {len(chunks)} chunks indexed from {Path('rag_docs').glob('*.pdf').__class__.__name__}")

# Count per-source
from collections import Counter
sources = Counter(c["source"] for c in chunks)
for src, count in sorted(sources.items()):
    print(f"  {src}: {count} chunks")

print("\nTest query: outdoor functional part heat resistance")
result = query_materials("outdoor functional part that needs heat resistance", top_k=2)
print("--- Retrieved context snippet (first 600 chars) ---")
print(result[:600])
print("--- END ---")

