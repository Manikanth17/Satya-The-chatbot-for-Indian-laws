"""Conservative contradiction flags for review; not a legal contradiction oracle."""
from __future__ import annotations
import re
from typing import Any

NEGATIONS = {"not", "no", "never", "cannot", "can't", "shallnot", "prohibited", "禁止"}

def find_potential_conflicts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flagged = []
    for i, left in enumerate(records):
        lt = set(re.findall(r"[a-z0-9]+", str(left.get("exact_text", "")).lower()))
        for right in records[i + 1:]:
            rt = set(re.findall(r"[a-z0-9]+", str(right.get("exact_text", "")).lower()))
            union = lt | rt
            similarity = len(lt & rt) / max(len(union), 1)
            polarity_diff = bool(lt & NEGATIONS) != bool(rt & NEGATIONS)
            if similarity >= 0.45 and polarity_diff:
                flagged.append({"left_evidence_id": left.get("paragraph_id"), "right_evidence_id": right.get("paragraph_id"), "reason": "Similar wording with differing negation; human review required."})
    return flagged
