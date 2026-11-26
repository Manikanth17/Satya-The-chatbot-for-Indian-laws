"""Conservative textual support checks for SATYA claims.

This module is a screening layer, not a legal entailment engine.
It must not treat keyword overlap as proof of legal correctness.
"""

from __future__ import annotations


import re
from typing import Any

from app.retrieval.tokenizer import tokenize


NUMBER_PATTERN = re.compile(
    r"(?<!\w)(?:₹\s*)?\d+(?:\.\d+)?%?(?!\w)"
)

NEGATIONS = {
    "not",
    "no",
    "never",
    "cannot",
    "can't",
    "prohibited",
}


NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty", "thirty", "forty",
    "fifty", "sixty", "seventy", "eighty",
    "ninety", "hundred", "thousand", "lakh",
    "lakhs", "crore", "crores"
}

def extract_numbers(text: str) -> set[str]:
    digits = {
        value.replace(" ", "")
        for value in NUMBER_PATTERN.findall(text)
    }

    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    written_numbers = words & NUMBER_WORDS

    return digits | written_numbers


def contains_negation(text: str) -> bool:
    """Detect simple negation markers."""
    words = set(re.findall(r"[a-zA-Z']+", text.lower()))
    return bool(words & NEGATIONS)


def assess_claim_support(claim: str, evidence: dict[str, Any]) -> str:
    claim = claim.strip()
    source = str(evidence.get("exact_text", "")).strip()

    if not claim or not source:
        return "unsupported"

    # Normalize whitespace and case for direct textual comparison
    normalized_claim = " ".join(claim.lower().split())
    normalized_source = " ".join(source.lower().split())

    claim_terms = set(tokenize(claim))
    source_terms = set(tokenize(source))

    if not claim_terms or not source_terms:
        return "uncertain"

    # Check topical relevance
    overlap = len(claim_terms & source_terms) / len(claim_terms)

    if overlap < 0.35:
        return "unsupported"

    # Check numerical consistency
    claim_numbers = extract_numbers(claim)
    source_numbers = extract_numbers(source)

    if claim_numbers and not claim_numbers.issubset(source_numbers):
        return "uncertain"

    # Check negation consistency
    if contains_negation(claim) != contains_negation(source):
        return "uncertain"

    # Only direct textual matches receive supported status
    if normalized_claim in normalized_source:
        return "supported"

    return "uncertain"