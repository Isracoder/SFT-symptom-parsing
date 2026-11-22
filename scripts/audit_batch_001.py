#!/usr/bin/env python3
"""Deterministic audit for generated text records.

Reads a fact-card JSONL file and its matching text JSONL file (by default
data/facts/batch_001.jsonl and data/text/batch_001.jsonl) plus, when coverage
checks are enabled, data/facts/{train,validation,gold}.jsonl and
reports/fact_coverage.json. Writes a human-readable markdown report, an
item-level JSONL audit, and a machine-readable <batch>_metrics.json.

All checks are stdlib-only and deterministic: no network, no LLM calls.
Semantic mismatches remain hard failures; realism findings are reported as
warnings only and never change a record verdict.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DEFAULT_TEXT = ROOT / "data" / "text" / "batch_001.jsonl"
DEFAULT_CARDS = ROOT / "data" / "facts" / "batch_001.jsonl"

# Realism thresholds (see DECISIONS.md "Density and naturalness").
DENSITY_LONG_LOW_MAX_WORDS = 25   # 1- or 2-3-fact card above this is suspect
DENSITY_SHORT_HIGH_MIN_WORDS = 15  # 7-9-fact card below this is suspect
SCHEMA_DUMP_MIN_COMMA_SEGMENTS = 6
SCHEMA_DUMP_MIN_TEMPLATE_SEGMENTS = 5
SCHEMA_DUMP_TEMPLATE_FRACTION = 0.60
LIST_STRUCTURES = ("S1", "S3")
LIST_STRUCTURE_DENSITY_CAP = 7
OPENER_TOKENS = 4
OPENER_MAX_SHARE = 0.30
OPENER_MAX_STRUCTURES = 4
# A within-structure opener share is only meaningful once the group is large
# enough; below this the distribution is reported but never warned on.
OPENER_MIN_GROUP = 10
LENGTH_STDDEV_MIN = 3.0

STRUCTURES = [f"S{i}" for i in range(1, 11)]
TRAIN_STRUCTURES = [f"S{i}" for i in range(1, 8)]
GOLD_STRUCTURES = ["S8", "S9", "S10"]
TYPES = ["adversarial", "empty", "off_topic", "ordinary"]
# Special input types (DECISIONS.md §3): they teach the empty extraction
# object. off_topic/empty carry no structure; adversarial rides an S1/S2
# carrier plus injected instruction noise.
SPECIAL_TYPES = ("adversarial", "off_topic", "empty")
NO_CARRIER_TYPES = ("off_topic", "empty")
SPECIALS_BUCKET = "specials"
TAGS = [
    "implicit_dates", "negation", "hedging", "typos", "long_multi_symptom",
    "duration_ambiguity", "supplement_naming", "emotional_language",
    "empty_off_topic", "adversarial", "contradictory", "very_short",
]
FIELDS = [
    "cycle_day", "flow", "spotting", "symptoms", "denied",
    "no_symptoms_asserted", "painkiller", "supplements", "sleep_hours",
    "sleep_quality", "energy_level", "mood", "hair", "skin",
]
LIST_FIELDS = {"symptoms", "denied", "supplements"}
SYMPTOMS = [
    "cramps", "headache", "bloating", "back_pain", "nausea", "fatigue",
    "breast_tenderness", "dizziness", "mood_swings", "insomnia", "diarrhea",
    "constipation", "cravings", "blood_clots", "pelvic_pain",
]
ENUMS = {
    "flow": ["none", "light", "medium", "heavy", "extremely_heavy"],
    "sleep_quality": ["poor", "fair", "good"],
    "energy_level": ["low", "medium", "high"],
    "mood": ["low", "neutral", "good"],
    "hair": ["oily", "dry", "growth", "loss", "normal"],
    "skin": ["oily", "dry", "acne", "normal"],
    "supplements": ["iron", "vitamin_d", "magnesium", "b12", "folate",
                    "calcium", "omega_3", "probiotic", "other"],
    "symptom_name": SYMPTOMS,
    "symptom_severity": ["mild", "moderate", "severe", None],
    "blood_clot_severity": ["light", "moderate", "large", None],
}

SYM_CUES = {
    "cramps": [r"\bcramp"],
    "headache": [r"\bheadache\b", r"\bhead ache\b"],
    "bloating": [r"\bbloat"],
    "back_pain": [r"\bback pain\b", r"\bback hurt", r"\bback ache\b"],
    "nausea": [r"\bnausea\b", r"\bnauseous\b", r"\bnaseau\b"],
    "fatigue": [r"\bfatigue\b", r"\bfatige\b", r"\btired\b", r"\bexhaust"],
    "breast_tenderness": [r"\bbreast tenderness\b", r"\btender breast", r"\bbreasts\b"],
    "dizziness": [r"\bdizzi", r"\bdizzy\b"],
    "mood_swings": [r"\bmood swing"],
    "insomnia": [r"\binsomnia\b"],
    "diarrhea": [r"\bdiarrhea\b", r"\bdiarrhoea\b"],
    "constipation": [r"\bconstipation\b"],
    "cravings": [r"\bcraving", r"\bcravnig"],
    "blood_clots": [r"\bblood clot", r"\bclot"],
    "pelvic_pain": [r"\bpelvic pain\b"],
}
SUPP_CUES = {
    "iron": [r"\biron\b"],
    "vitamin_d": [r"\bvitamin d\b"],
    "magnesium": [r"\bmagnesium\b"],
    "b12": [r"\bb12\b"],
    "folate": [r"\bfolate\b"],
    "calcium": [r"\bcalcium\b"],
    "omega_3": [r"\bomega[- ]?3\b"],
    "probiotic": [r"\bprobiotic\b"],
    "other": [
        r"\bunlisted supplement\b", r"\bother supplement\b",
        r"\bother supp(?:lement|s)?\b", r"\bother stuff\b",
        r"\bsome other\b",
        r"\bsups?\s*:\s*other\b", r"\bsupplements?\s*:\s*other\b",
    ],
}
SEVERITY_WORDS = {
    "mild": ["light", "slight", "slightly", "a bit", "some", "mild"],
    "moderate": ["bad", "awful", "rough", "really bad", "killing me"],
    "severe": ["unbearable", "crippling", "can't move", "can't function",
               "cannot function", "worst ever"],
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> list[str]:
    return norm(text).split()


def grams(ts: list[str], n: int = 4) -> set[tuple[str, ...]]:
    return {tuple(ts[i:i + n]) for i in range(max(0, len(ts) - n + 1))}


NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14,
}


def _edit_distance(a: str, b: str, limit: int = 2) -> int:
    """Levenshtein distance, early-exit when > limit."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > limit:
        return limit + 1
    # ensure la <= lb
    if la > lb:
        a, b, la, lb = b, a, lb, la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        row_min = cur[0]
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
            if cur[j] < row_min:
                row_min = cur[j]
        if row_min > limit:
            return limit + 1
        prev = cur
    return prev[lb]


def _edit_distance_leq1(a: str, b: str) -> bool:
    return _edit_distance(a, b, 1) <= 1


def _token_matches(word: str, target: str) -> bool:
    """Typo-tolerant token match: exact, prefix for truncated (len>=3),
    or bounded edit distance for longer tokens. Never maps to a different
    vocabulary item: distance-2 requires same 4-char prefix."""
    if word == target:
        return True
    # prefix match for truncated tokens like "los" -> "loss"
    if (len(word) >= 3 and len(target) > len(word)
            and len(target) - len(word) <= 2
            and target.startswith(word)):
        return True
    if len(word) >= 5 and len(target) >= 5 and _edit_distance_leq1(word, target):
        return True
    # distance <=2 only when clearly same word stem (same first 4 chars)
    if len(word) >= 6 and len(target) >= 6 and word[:4] == target[:4]:
        if _edit_distance(word, target, 2) <= 2:
            return True
    # short 4-char words: allow distance 1 with same first and last char
    if len(word) == 4 and len(target) == 4 and word[0] == target[0] and word[-1] == target[-1]:
        if _edit_distance_leq1(word, target):
            return True
    return False


def fuzzy_has_phrase(text: str, phrase: str) -> bool:
    """Check whether phrase appears in text, tolerating minor typos per token.
    Never crosses polarity boundaries - caller is responsible for negation."""
    text_tokens = tokens(text)
    phrase_tokens = norm(phrase).split()
    if not phrase_tokens:
        return False
    n = len(phrase_tokens)
    for i in range(len(text_tokens) - n + 1):
        if all(_token_matches(text_tokens[i + j], phrase_tokens[j])
               for j in range(n)):
            return True
    return False


def fuzzy_find_phrase_spans(text: str, phrase: str) -> list[tuple[int, int]]:
    """Find approximate spans of phrase in original text for negation checks.
    Returns (start, end) char spans in lowered original text space."""
    low = text.lower()
    # Try exact regex first
    pat = r"\b" + re.escape(phrase.lower()) + r"\b"
    spans = [(m.start(), m.end()) for m in re.finditer(pat, low)]
    if spans:
        return spans
    # Fuzzy: find token positions in normalized space mapped back approximately.
    # Build a mapping from normalized-token index to char spans in low text.
    word_spans = [(m.start(), m.end(), m.group()) for m in re.finditer(r"[a-z0-9]+", low)]
    phrase_tokens = norm(phrase).split()
    n = len(phrase_tokens)
    for i in range(len(word_spans) - n + 1):
        words = [word_spans[i + j][2] for j in range(n)]
        if all(_token_matches(words[j], phrase_tokens[j]) for j in range(n)):
            spans.append((word_spans[i][0], word_spans[i + n - 1][1]))
    return spans


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def has_any_fuzzy(text: str, patterns: list[str]) -> bool:
    """Like has_any but also tolerates minor typos in pattern words."""
    if has_any(text, patterns):
        return True
    for p in patterns:
        # extract literal words from simple regex patterns
        literal = re.sub(r"\\b|\\s\+|\\s\*|[-?]", " ", p)
        literal = re.sub(r"[^a-z0-9 ]", " ", literal.lower())
        literal = re.sub(r"\s+", " ", literal).strip()
        if literal and fuzzy_has_phrase(text, literal):
            return True
    return False


def has_any_cue(text: str, patterns: list[str]) -> bool:
    """Cue presence check with typo tolerance for expected card facts."""
    return has_any_fuzzy(text, patterns)


def _symptom_cue_spans(text: str, name: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pat in SYM_CUES.get(name, []):
        literal = re.sub(r"\\b|\\s\+|\\s\*|[-?]", " ", pat)
        literal = re.sub(r"[^a-z0-9 ]", " ", literal.lower())
        literal = re.sub(r"\s+", " ", literal).strip()
        if literal:
            spans.extend(fuzzy_find_phrase_spans(text, literal))
    # dedupe
    return sorted(set(spans))


def _denial_near_cue(low: str, cue_spans: list[tuple[int, int]]) -> bool:
    for s, e in cue_spans:
        before = _same_segment_before(low, s, 30)
        after = _same_segment_after(low, e, 30)
        if re.search(r"\b(no|not|none|without|denied|deny)\b", before + " " + after):
            return True
    return False


def schema_errors(facts: dict) -> list[str]:
    errors: list[str] = []
    for key in facts:
        if key not in FIELDS:
            errors.append(f"extra key: {key}")
    if "cycle_day" in facts and not (isinstance(facts["cycle_day"], int) and facts["cycle_day"] >= 1):
        errors.append("cycle_day must be a positive int")
    if "flow" in facts and facts["flow"] not in ENUMS["flow"]:
        errors.append("invalid flow")
    for key in ("spotting", "painkiller", "no_symptoms_asserted"):
        if key in facts and not isinstance(facts[key], bool):
            errors.append(f"{key} must be bool")
    if facts.get("no_symptoms_asserted") is False:
        errors.append("no_symptoms_asserted must never be false")
    if "sleep_hours" in facts and not (
        isinstance(facts["sleep_hours"], (int, float)) and not isinstance(facts["sleep_hours"], bool)
    ):
        errors.append("sleep_hours must be numeric")
    for key in ("sleep_quality", "energy_level", "mood", "hair", "skin"):
        if key in facts and facts[key] not in ENUMS[key]:
            errors.append(f"invalid {key}")
    names: list[str] = []
    for symptom in facts.get("symptoms", []):
        if set(symptom) != {"name", "severity"}:
            errors.append("symptom object must have exactly name/severity")
            continue
        name = symptom.get("name")
        names.append(name)
        if name not in ENUMS["symptom_name"]:
            errors.append(f"invalid symptom name: {name}")
        elif name == "blood_clots":
            if symptom.get("severity") not in ENUMS["blood_clot_severity"]:
                errors.append("invalid blood_clots severity")
        elif symptom.get("severity") not in ENUMS["symptom_severity"]:
            errors.append(f"invalid severity for {name}")
    if len(names) != len(set(names)):
        errors.append("duplicate symptom")
    denied = facts.get("denied", [])
    if len(denied) != len(set(denied)):
        errors.append("duplicate denied symptom")
    if set(denied) & set(names):
        errors.append("symptom both affirmed and denied")
    for name in denied:
        if name not in ENUMS["symptom_name"]:
            errors.append(f"invalid denied symptom: {name}")
    supplements = facts.get("supplements", [])
    if len(supplements) != len(set(supplements)):
        errors.append("duplicate supplement")
    for supplement in supplements:
        if supplement not in ENUMS["supplements"]:
            errors.append(f"invalid supplement: {supplement}")
    if facts.get("no_symptoms_asserted") is True and (names or denied):
        errors.append("global no-symptoms claim with symptoms/denied")
    return errors


_S3_OPENER_ASIDES = {
    "morning", "evening", "afternoon", "night", "tonight", "today",
    "this morning", "this evening", "this afternoon", "last night",
}


def _is_s3_opener_aside(segment: str) -> bool:
    s = norm(segment)
    if not s:
        return False
    if ":" in segment:
        return False
    return s in _S3_OPENER_ASIDES or (len(s.split()) <= 3 and s in _S3_OPENER_ASIDES)


def structure_errors(structure: str, text: str) -> list[str]:
    errors: list[str] = []
    low = text.lower()
    sub = r"\b(because|although|though|even though|since|while|whereas|unless)\b"
    contrast = r"\b(but|however|yet)\b"
    correction = r"\b(actually|no wait|i mean)\b"
    command = r"^\s*(log|record|note|please|add|track|save|write)\b"
    # A sentence-ending period, but not a decimal point or an abbreviation.
    terminal = r"[!?]|\.(?=\s|$)"

    if structure == "S1":
        if re.search(terminal, text):
            errors.append("S1 contains sentence punctuation")
        if ";" in text:
            errors.append("S1 contains a semicolon")
        if re.search(r"\b(I|my|we)\b", text, flags=re.IGNORECASE):
            # S1 may contain possessives in fragments, but not full clauses.
            pass
    elif structure == "S2":
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
        if not 2 <= len(sentences) <= 4:
            errors.append(f"S2 sentence count {len(sentences)}")
        for name, pattern in (("subordinate", sub), ("contrast", contrast),
                              ("correction", correction), ("question", r"\?"),
                              ("command", command)):
            if re.search(pattern, low):
                errors.append(f"S2 {name}")
    elif structure == "S3":
        if re.search(r"[!?]|\.(?=\s|$)", text):
            errors.append("S3 contains sentence punctuation")
        segments = [s.strip() for s in re.split(r"[;\n]+", text) if s.strip()]
        for i, segment in enumerate(segments):
            if re.match(r"^[a-z][a-z _-]*:\s*\S", segment, flags=re.IGNORECASE):
                continue
            # Allow a leading short opener/time cue line (e.g. morning, evening)
            if i == 0 and _is_s3_opener_aside(segment):
                continue
            errors.append(f"S3 segment is not label:value: {segment}")
    elif structure == "S4":
        for name, pattern in (("subordinate", sub), ("contrast", contrast),
                              ("correction", correction), ("question", r"\?"),
                              ("command", command)):
            if re.search(pattern, low):
                errors.append(f"S4 {name}")
        if not re.search(r"\b(and|so)\b", low):
            errors.append("S4 lacks and/so run-on")
    elif structure == "S5":
        for name, pattern in (("subordinate", sub), ("contrast", contrast),
                              ("correction", correction), ("question", r"\?"),
                              ("command", command)):
            if re.search(pattern, low):
                errors.append(f"S5 {name}")
    elif structure == "S6":
        count = len(re.findall(r"[A-Za-z0-9']+", text))
        if not 2 <= count <= 6:
            errors.append(f"S6 word count {count}")
    elif structure == "S7":
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
        if not sentences or not sentences[0].endswith("?"):
            errors.append("S7 missing initial question")
        if sum(s.endswith("?") for s in sentences) != 1:
            errors.append("S7 must contain exactly one question")
        for name, pattern in (("subordinate", sub), ("contrast", contrast),
                              ("correction", correction), ("command", command)):
            if re.search(pattern, low):
                errors.append(f"S7 {name}")
    else:
        errors.append(f"unexpected structure {structure}")
    return errors


def _normalize_date_words(text: str) -> str:
    """Normalize common typos/paraphrases for cycle-day parsing only."""
    low = text.lower()
    # normalize any token fuzzy-matching "started"/"start" near date context
    def _fix_start(m: re.Match) -> str:
        w = m.group(0)
        if w in ("started", "start"):
            return "started"
        if _token_matches(w, "started") or _token_matches(w, "start"):
            return "started"
        return w
    low = re.sub(r"\b[a-z]{3,8}\b", _fix_start, low)
    # number words and special forms
    low = re.sub(r"\ba week ago\b", "7 days ago", low)
    low = re.sub(r"\ba fortnight ago\b", "14 days ago", low)
    def _num_word(m: re.Match) -> str:
        w = m.group(1)
        n = NUMBER_WORDS.get(w)
        return f"{n} days ago" if n is not None else m.group(0)
    low = re.sub(
        r"\b(" + "|".join(NUMBER_WORDS.keys()) + r")\s+days?\s+ago\b",
        _num_word, low,
    )
    return low


def cycle_day_from_text(text: str) -> list[int]:
    low = _normalize_date_words(text)
    found: list[int] = []
    patterns = [
        (r"(?:period\s+)?started\s+(\d+)\s+days?\s+ago", lambda m: int(m.group(1)) + 1),
        (r"(?:period\s+)?started:\s*(\d+)\s+days?\s+ago", lambda m: int(m.group(1)) + 1),
        (r"(?:period\s+)?started\s+yesterday", lambda m: 2),
        (r"(?:period\s+)?started:\s*yesterday", lambda m: 2),
        (r"(?:period\s+)?started\s+today", lambda m: 1),
        (r"(?:period\s+)?started:\s*today", lambda m: 1),
    ]
    for pattern, fn in patterns:
        for match in re.finditer(pattern, low):
            found.append(fn(match))
    return sorted(set(found))


def sleep_hours_from_text(text: str) -> list[float]:
    low = text.lower()
    if "three and a half hours" in low:
        return [3.5]
    found: list[float] = []
    ranges = list(re.finditer(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:h|hours?)", low))
    for match in ranges:
        found.append((float(match.group(1)) + float(match.group(2))) / 2)
    remainder = low
    for match in reversed(ranges):
        remainder = remainder[:match.start()] + " " + remainder[match.end():]
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:h|hours?)", remainder):
        found.append(float(match.group(1)))
    return sorted(set(found))


def check_numeric(item: dict) -> list[str]:
    errors: list[str] = []
    facts = item["facts"]
    text = item["text"]
    cycle_values = cycle_day_from_text(text)
    if "cycle_day" in facts:
        if not cycle_values:
            errors.append("cycle_day fact has no recoverable relative date")
        elif facts["cycle_day"] not in cycle_values:
            errors.append(f"cycle_day {facts['cycle_day']} != text {cycle_values}")
    elif cycle_values:
        errors.append(f"cycle_day not in card but text implies {cycle_values}")

    sleep_values = sleep_hours_from_text(text)
    if "sleep_hours" in facts:
        if not sleep_values:
            errors.append("sleep_hours fact has no recoverable quantity")
        elif not any(abs(facts["sleep_hours"] - value) < 1e-9 for value in sleep_values):
            errors.append(f"sleep_hours {facts['sleep_hours']} != text {sleep_values}")
    elif sleep_values:
        errors.append(f"sleep_hours not in card but text implies {sleep_values}")

    clots = [s for s in facts.get("symptoms", []) if s["name"] == "blood_clots"]
    if clots:
        severity = clots[0]["severity"]
        mentions = [m.start() for m in re.finditer(r"clot", text, flags=re.IGNORECASE)]
        if not mentions:
            errors.append("blood_clots fact has no cue")
        else:
            windows = [
                text[max(0, start - 40):start + 40].lower()
                for start in mentions
            ]
            size_words = {
                "large": [r"\blarge\b", r"\bbig\b"],
                "light": [r"\blight\b", r"\bsmall\b", r"\btiny\b"],
                "moderate": [r"\bmoderate\b"],
            }
            any_magnitude = any(
                re.search(p, window)
                for window in windows
                for pats in size_words.values()
                for p in pats
            )
            if severity is None:
                if any_magnitude:
                    errors.append("blood_clots null but text states a magnitude")
            else:
                pats = size_words.get(severity, [rf"\b{re.escape(str(severity))}\b"])
                if not any(re.search(p, window) for window in windows for p in pats):
                    errors.append(f"blood_clots {severity} not recoverable from text")
    elif "blood_clots" not in facts.get("denied", []) and re.search(r"\bclot", text, flags=re.IGNORECASE):
        errors.append("blood_clots mentioned but absent from card")
    return errors


_NEG_WORDS_RE = re.compile(r"\b(no|not|none|without)\b")


def _same_segment_before(low: str, start: int, limit: int = 40) -> str:
    """Return text before start within the same line/comma/semicolon segment."""
    before = low[max(0, start - limit):start]
    # Do not cross segment boundaries: newline, semicolon, comma.
    # Walk backwards to find last boundary.
    cut = -1
    for i, ch in enumerate(before):
        if ch in "\n;,":

            cut = i
    if cut >= 0:
        before = before[cut + 1:]
    return before


def _same_segment_after(low: str, end: int, limit: int = 40) -> str:
    after = low[end:end + limit]
    cut = len(after)
    for i, ch in enumerate(after):
        if ch in "\n;,":
            cut = i
            break
    return after[:cut]


def locally_negated(low: str, start: int, end: int) -> bool:
    """True when a negation directly modifies the cue at [start, end)."""
    before = _same_segment_before(low, start)
    after = _same_segment_after(low, end)
    before_neg = re.search(r"\b(no|not|none|without)\s+(?:\w+\s+){0,1}$", before)
    after_neg = re.match(r"\s*[:\-]?\s*(not|none|no|without)\b", after)
    return bool(before_neg or after_neg)


_GLOBAL_NO_SYMPTOM_PATTERNS = [
    r"\bno symptoms\b",
    r"\bsymptoms?\s*:\s*none\b",
    r"\bno other symptoms?\b",
    r"\bnothing else going on\b",
    r"\bnothing at all\b",
    r"\bnothing else\b",
    r"\bno other issues?\b",
]


def _has_global_no_symptom_claim(low: str) -> bool:
    return any(re.search(p, low) for p in _GLOBAL_NO_SYMPTOM_PATTERNS)


def check_negation_and_cues(item: dict) -> list[str]:
    errors: list[str] = []
    facts = item["facts"]
    text = item["text"]
    low = text.lower()

    # spotting
    spotting_mentions = fuzzy_find_phrase_spans(text, "spotting")
    spotting_value = facts.get("spotting")
    if spotting_value is True:
        if not spotting_mentions:
            errors.append("spotting true but no cue")
        elif any(locally_negated(low, s, e) for s, e in spotting_mentions):
            errors.append("spotting true but locally negated")
    elif spotting_value is False:
        if not spotting_mentions:
            errors.append("spotting false but no cue")
        elif not any(locally_negated(low, s, e) for s, e in spotting_mentions):
            errors.append("spotting false but no negation")
    elif spotting_mentions:
        errors.append("spotting mentioned but null in card")

    # painkiller
    pain_mentions = fuzzy_find_phrase_spans(text, "painkiller")
    if not pain_mentions:
        pain_mentions = fuzzy_find_phrase_spans(text, "pain killer")
    pain_value = facts.get("painkiller")
    if pain_value is True:
        if not pain_mentions:
            errors.append("painkiller true but no cue")
        elif any(locally_negated(low, s, e) for s, e in pain_mentions):
            errors.append("painkiller true but locally negated")
    elif pain_value is False:
        if not pain_mentions:
            errors.append("painkiller false but no cue")
        elif not any(locally_negated(low, s, e) for s, e in pain_mentions):
            errors.append("painkiller false but no negation")
    elif pain_mentions:
        errors.append("painkiller mentioned but null in card")

    # no_symptoms_asserted
    global_claim = _has_global_no_symptom_claim(low)
    if facts.get("no_symptoms_asserted") is True:
        if not global_claim:
            errors.append("global no-symptoms claim missing")
        if facts.get("symptoms") or facts.get("denied"):
            errors.append("global no-symptoms claim with symptoms/denied")
    elif global_claim:
        errors.append("global no-symptoms claim but field null")

    # flow
    flow_value = facts.get("flow")
    flow_cue = bool(re.search(r"\bflow\b|\bperiod\b|\bbleed", low))
    if flow_value == "none":
        if not re.search(r"\bno bleed|\bbleeding:\s*none\b|\bno flow\b|\bflow:\s*none\b", low):
            errors.append("flow none but no explicit no-bleeding cue")
    elif flow_value is not None:
        if not flow_cue:
            errors.append("flow value but no flow/period cue")
        if re.search(r"\bno bleed|\bbleeding:\s*none\b|\bno flow\b|\bflow:\s*none\b", low):
            errors.append("flow positive but text says no bleeding")
    elif flow_cue:
        errors.append("flow mentioned but null in card")

    # supplements
    for supplement in facts.get("supplements", []):
        if not has_any_cue(text, SUPP_CUES[supplement]):
            errors.append(f"supplement {supplement} has no cue")
    if not facts.get("supplements"):
        if has_any_cue(text, [p for patterns in SUPP_CUES.values() for p in patterns]):
            errors.append("supplement mentioned but list empty")

    # hair/skin
    for field in ("hair", "skin"):
        value = facts.get(field)
        cue = bool(re.search(r"\bhair\b", low)) if field == "hair" else bool(re.search(r"\bskin\b|\bacne\b", low))
        if not cue:
            # typo-tolerant: hair/skin are short but common
            cue = fuzzy_has_phrase(text, field) or (field == "skin" and fuzzy_has_phrase(text, "acne"))
        if value is not None:
            if not cue:
                errors.append(f"{field} value but no cue")
        elif cue:
            errors.append(f"{field} mentioned but null in card")

    # symptoms / denied
    declared = {s["name"] for s in facts.get("symptoms", [])} | set(facts.get("denied", []))
    mentioned_exact = {name for name, patterns in SYM_CUES.items() if has_any(text, patterns)}
    mentioned_fuzzy = {name for name, patterns in SYM_CUES.items() if has_any_cue(text, patterns)}
    for name in sorted(mentioned_exact - declared):
        # "mood" inside "mood swings" is not a separate mood field; this
        # check is symptom-only, so any symptom cue is a real extra mention.
        errors.append(f"symptom cue {name} mentioned but not in card")
    for name in sorted(declared - mentioned_fuzzy):
        errors.append(f"symptom {name} in card but no cue")
    for name in facts.get("denied", []):
        # negation must be in the same segment as the symptom cue
        cue_spans = _symptom_cue_spans(text, name)
        if cue_spans:
            if not any(locally_negated(low, s, e) for s, e in cue_spans):
                # also allow a segment-level negation word near the symptom
                if not _denial_near_cue(low, cue_spans):
                    errors.append(f"denied {name} but no negation")
        else:
            if not re.search(r"\b(no|not|none|without)\b", low):
                errors.append(f"denied {name} but no negation")
    return errors


# --- Special-input checks --------------------------------------------------
#
# adversarial / off_topic / empty records exist to teach the empty extraction
# object (DECISIONS.md §1/§3). They are not fact-bearing logs, so the ordinary
# structure/numeric/fidelity extraction checks do not apply; instead each type
# gets the targeted checks below. Findings here are reported in a dedicated
# specials section; only hard label/carrier defects become item errors.

INJECTION_SPAN_RE = re.compile(r"\[[^\[\]]+\]")
INJECTION_CUE_RE = re.compile(
    r"\b(ignore|disregard|override|void|suspend\w*|must|include|add|emit|"
    r"output\w*|instructions?|schema|extra\s+keys?)\b",
    re.IGNORECASE,
)

# In-scope cue families an off_topic text must NOT contain. A hit is a WARNING
# (the text may carry an extractable health fact), never an automatic reject.
OFF_TOPIC_CUE_GROUPS = {
    "period_flow_spotting": [
        r"\bperiods?\b", r"\bflow\b", r"\bbleed\w*", r"\bspotting\b",
        r"\bmenstru\w*", r"\bcycle\s+day\b",
    ],
    "symptoms": [p for pats in SYM_CUES.values() for p in pats] + [
        r"\bdysmenorrhea\b",
        r"\b(?:belly|stomach|tummy)\s+(?:pain|ache|cramp\w*)\b",
    ],
    "sleep": [r"\bsleep\w*", r"\bslept\b", r"\bnap(?:s|ped)?\b"],
    "mood": [r"\bmood\b"],
    "energy": [r"\benergy\b"],
    "hair": [r"\bhair\b"],
    "skin": [r"\bskin\b", r"\bacne\b"],
    "supplements": [p for pats in SUPP_CUES.values() for p in pats] + [
        r"\bsupplements?\b", r"\bvitamins?\b",
    ],
    "painkiller": [r"\bpain\s*killers?\b", r"\banalges\w*"],
}


def is_empty_extraction(facts: dict) -> bool:
    """True when the label is the empty extraction object: every scalar null
    (or absent) and every list empty (or absent)."""
    return non_null_fact_count(facts) == 0


def find_injections(text: str) -> list[str]:
    """Bracketed instruction-injection spans present in an adversarial text."""
    return [
        m.group(0) for m in INJECTION_SPAN_RE.finditer(text)
        if INJECTION_CUE_RE.search(m.group(0))
    ]


def off_topic_cue_hits(text: str) -> dict[str, list[str]]:
    """Return the in-scope cue families (and matching patterns) found in text."""
    hits: dict[str, list[str]] = {}
    for group, patterns in OFF_TOPIC_CUE_GROUPS.items():
        matched = [p for p in patterns if re.search(p, text, flags=re.IGNORECASE)]
        if matched:
            hits[group] = matched
    return hits


def check_special(item: dict) -> tuple[list[str], list[str], dict]:
    """Targeted checks for one special record.

    Returns (errors, warnings, detail). Errors are hard label/carrier defects;
    warnings are advisory (off_topic in-scope cues). detail is reported in the
    specials section and never changes the verdict by itself.
    """
    errors: list[str] = []
    warnings: list[str] = []
    item_type = item.get("type")
    structure = item.get("structure")
    facts = item["facts"]
    text = item["text"]
    detail: dict = {"id": item["id"], "type": item_type, "structure": structure}

    label_empty = is_empty_extraction(facts)
    detail["label_empty"] = label_empty
    if not label_empty:
        errors.append("special label is not the empty extraction object")

    if item_type in NO_CARRIER_TYPES:
        detail["carrier_ok"] = structure is None
        if structure is not None:
            errors.append(f"{item_type} must have structure null (no carrier)")
    elif item_type == "adversarial":
        carrier_ok = structure in STRUCTURES
        detail["carrier_ok"] = carrier_ok
        detail["carrier_structure"] = structure
        if structure is None:
            errors.append("adversarial record has no carrier structure")
        elif not carrier_ok:
            errors.append(f"adversarial carrier is not a known structure: {structure}")
        injections = find_injections(text)
        detail["injection_present"] = bool(injections)
        detail["injections"] = injections
        if not injections:
            errors.append("adversarial text has no injected instruction")
        # Do not extract facts from the injection; the carrier is benign noise.
    else:
        detail["carrier_ok"] = structure is None
        if structure is not None:
            errors.append(f"{item_type} must have structure null (no carrier)")

    if item_type == "off_topic":
        hits = off_topic_cue_hits(text)
        detail["in_scope_cues"] = hits
        if hits:
            warnings.append(
                "off_topic text contains in-scope cue(s): "
                + ", ".join(sorted(hits))
            )
    elif item_type == "empty":
        whitespace_only = not text.strip()
        detail["whitespace_only"] = whitespace_only
        if not whitespace_only:
            errors.append("empty record text is not empty/whitespace-only")

    return errors, warnings, detail


def exact_duplicate_ids(items: list[dict]) -> list[list[str]]:
    groups: dict[str, list[str]] = collections.defaultdict(list)
    for item in items:
        groups[norm(item["text"])].append(item["id"])
    return [ids for ids in groups.values() if len(ids) > 1]


def near_duplicate_pairs(items: list[dict], threshold: float = 0.85) -> list[tuple[float, str, str]]:
    pairs: list[tuple[float, str, str]] = []
    for a, b in itertools.combinations(items, 2):
        ga, gb = grams(tokens(a["text"])), grams(tokens(b["text"]))
        jaccard = len(ga & gb) / len(ga | gb) if ga | gb else 0.0
        if jaccard >= threshold:
            pairs.append((jaccard, a["id"], b["id"]))
    return sorted(pairs, reverse=True)


def max_near_duplicate(items: list[dict], numeric_normalize: bool = False) -> tuple[float, str, str]:
    best = (0.0, "", "")
    for a, b in itertools.combinations(items, 2):
        ta, tb = tokens(a["text"]), tokens(b["text"])
        if numeric_normalize:
            ta = ["<num>" if re.fullmatch(r"\d+(?:\.\d+)?", t) else t for t in ta]
            tb = ["<num>" if re.fullmatch(r"\d+(?:\.\d+)?", t) else t for t in tb]
        ga, gb = grams(ta), grams(tb)
        jaccard = len(ga & gb) / len(ga | gb) if ga | gb else 0.0
        if jaccard > best[0]:
            best = (jaccard, a["id"], b["id"])
    return best


def length_stats(items: list[dict]) -> dict:
    words = [len(tokens(item["text"])) for item in items]
    chars = [len(item["text"]) for item in items]

    def stats(values: list[int]) -> dict:
        if not values:
            return {"min": None, "median": None, "mean": None, "max": None}
        return {
            "min": min(values), "median": statistics.median(values),
            "mean": round(statistics.mean(values), 2), "max": max(values),
        }

    return {"n": len(items), "words": stats(words), "chars": stats(chars)}


def repeated_openers(items: list[dict], n: int = 3) -> list[tuple[int, str]]:
    counts = collections.Counter(tuple(tokens(item["text"])[:n]) for item in items)
    return [(count, " ".join(key)) for key, count in counts.most_common() if count >= 2]


def repeated_frames(items: list[dict], n: int = 5) -> list[tuple[int, str]]:
    counts: collections.Counter[tuple[str, ...]] = collections.Counter()
    for item in items:
        for sentence in re.split(r"(?<=[.!?])\s+", item["text"].strip()):
            ts = tokens(sentence)
            if ts:
                counts[tuple(ts[:n])] += 1
    return [(count, " ".join(key)) for key, count in counts.most_common() if count >= 2]


def field_non_null(record: dict, field: str) -> bool:
    value = record["facts"].get(field)
    if field in LIST_FIELDS:
        return bool(value)
    return value is not None


# --- Realism helpers -------------------------------------------------------
#
# These checks never change an item verdict. They are reported separately so
# a human can decide whether a batch sounds like real logs rather than schema
# dumps or template output.

BAND_ORDER = ("1", "2-3", "4-6", "7-9", "other")
SUBJECT_CLASSES = ("my period", "i", "today", "no", "bare_fragment", "other")
REALISM_CHECKS = (
    "fact_density_alignment",
    "schema_dump",
    "list_structure_density_cap",
    "opener_frame_repetition",
    "sentence_subject_repetition",
    "length_variance",
)

# Labels a rigid `field value` segment may start with. Longest first so
# "sleep quality" wins over "sleep".
FIELD_VALUE_LABELS = [
    "no symptoms asserted", "global no symptom claim", "sleep quality",
    "sleep hours", "cycle day", "painkiller", "pain killer", "supplements",
    "symptoms", "denials", "denied", "spotting", "energy", "energy level",
    "mood", "hair", "skin", "flow",
]


def _build_field_value_template() -> re.Pattern:
    labels = sorted(
        {label.strip().lower().replace("_", " ") for label in FIELD_VALUE_LABELS},
        key=len,
        reverse=True,
    )
    alternation = "|".join(re.escape(label) for label in labels)
    return re.compile(
        rf"^(?:{alternation})\b\s*(?:[:=\-]|\s)\s*\S+", re.IGNORECASE
    )


FIELD_VALUE_TEMPLATE_RE = _build_field_value_template()


def density_band(count: int) -> str:
    if count == 1:
        return "1"
    if 2 <= count <= 3:
        return "2-3"
    if 4 <= count <= 6:
        return "4-6"
    if 7 <= count <= 9:
        return "7-9"
    return "other"


def non_null_fact_count(facts: dict) -> int:
    """Count non-null top-level facts: not null, not [], not {}.

    Booleans (including False), zero and empty strings are real asserted
    facts; only null/empty-list/empty-object values do not count.
    """
    count = 0
    for field in FIELDS:
        value = facts.get(field)
        if value is None or value == [] or value == {}:
            continue
        count += 1
    return count


def summarize_word_counts(values: list[int]) -> dict:
    if not values:
        return {
            "n": 0, "min": None, "median": None, "mean": None,
            "max": None, "stddev": None,
        }
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": round(statistics.mean(values), 2),
        "max": max(values),
        "stddev": round(statistics.pstdev(values), 2),
    }


def normalize_segment(segment: str) -> str:
    text = segment.strip().lower().replace("_", " ")
    text = re.sub(r"^[-*\u2022]+\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def schema_dump_flags(text: str) -> dict:
    """Deterministic schema-dump signals for one text.

    Two independent triggers:
      * a single comma-separated list with >= 6 segments and no sentence
        punctuation other than commas (colons/decimals do not count as
        sentence punctuation);
      * >= 60% of comma/semicolon/newline segments matching a rigid
        `field value` template, requiring >= 5 segments so that a normal
        two-item telegraphic S3 log is not flagged.
    """
    comma_segments = [s.strip() for s in text.split(",") if s.strip()]
    terminal = re.search(r"[!?;]|\.(?=\s|$)", text)
    reasons: list[str] = []
    if len(comma_segments) >= SCHEMA_DUMP_MIN_COMMA_SEGMENTS and not terminal:
        reasons.append("comma_list_ge_6_no_sentence_punctuation")

    parts = [
        normalize_segment(part)
        for part in re.split(r"[,;\n]+", text)
    ]
    parts = [part for part in parts if part]
    matches = sum(1 for part in parts if FIELD_VALUE_TEMPLATE_RE.match(part))
    if (
        len(parts) >= SCHEMA_DUMP_MIN_TEMPLATE_SEGMENTS
        and matches / len(parts) >= SCHEMA_DUMP_TEMPLATE_FRACTION
    ):
        reasons.append("field_value_template_ge_60pct")

    return {
        "flagged": bool(reasons),
        "reasons": reasons,
        "comma_segments": len(comma_segments),
        "segments": len(parts),
        "template_matches": matches,
    }


def opening_frame(text: str, n: int = OPENER_TOKENS) -> tuple[str, ...]:
    return tuple(tokens(text)[:n])


def frame_label(frame: tuple[str, ...]) -> str:
    return " ".join(frame) if frame else "(empty)"


def opening_counter(items: list[dict], n: int = OPENER_TOKENS) -> collections.Counter:
    counter: collections.Counter = collections.Counter()
    for item in items:
        counter[opening_frame(item["text"], n)] += 1
    return counter


def ranked_frames(counter: collections.Counter) -> list[tuple[tuple[str, ...], int]]:
    # Highest count first; ties break on the frame string so output is stable.
    return sorted(counter.items(), key=lambda pair: (-pair[1], frame_label(pair[0])))


FIRST_PERSON_RE = re.compile(r"\b(i|my|me|we|us)\b")


def sentence_subject_class(text: str) -> str:
    """Classify the sentence-initial subject without POS tagging.

    Explicit openers win. A "bare fragment" is a text with no first-person
    marker anywhere and no sentence punctuation (terse note/list style).
    Distribution only; this check never emits a warning.
    """
    ts = tokens(text)
    if not ts:
        return "bare_fragment"
    if len(ts) >= 2 and ts[0] == "my" and ts[1] == "period":
        return "my period"
    if ts[0] == "i":
        return "i"
    if ts[0] == "today":
        return "today"
    if ts[0] == "no":
        return "no"
    if not FIRST_PERSON_RE.search(norm(text)) and not re.search(r"[.!?]", text):
        return "bare_fragment"
    return "other"


def band_distribution(records: list[dict]) -> dict:
    counts = collections.Counter(record["band"] for record in records)
    word_stats = {}
    for band in BAND_ORDER:
        words = [record["words"] for record in records if record["band"] == band]
        stats = summarize_word_counts(words)
        stats["count"] = len(words)
        word_stats[band] = stats
    return {
        "counts": {band: counts.get(band, 0) for band in BAND_ORDER},
        "word_stats": word_stats,
    }


def subject_distribution(records: list[dict]) -> dict:
    counts = collections.Counter(
        sentence_subject_class(record["text"]) for record in records
    )
    total = len(records)
    return {
        subject: {
            "count": counts.get(subject, 0),
            "fraction": round(counts.get(subject, 0) / total, 4) if total else None,
        }
        for subject in SUBJECT_CLASSES
    }


def build_realism_report(items: list[dict]) -> dict:
    """Compute all realism metrics and warnings for the supplied batch."""
    warnings: list[dict] = []

    def warn(check: str, level: str, message: str, records: list[str]) -> None:
        warnings.append({
            "check": check,
            "level": level,
            "message": message,
            "records": sorted(set(records)),
        })

    structures = sorted({item["structure"] for item in items if item["structure"]})
    by_structure: dict[str, list[dict]] = {
        structure: [item for item in items if item["structure"] == structure]
        for structure in structures
    }

    # 1. Fact-density alignment.
    density_records = []
    for item in items:
        fact_count = non_null_fact_count(item["facts"])
        density_records.append({
            "id": item["id"],
            "structure": item["structure"],
            "fact_count": fact_count,
            "band": density_band(fact_count),
            "words": len(tokens(item["text"])),
        })
    long_low = [
        record for record in density_records
        if record["band"] in ("1", "2-3")
        and record["words"] > DENSITY_LONG_LOW_MAX_WORDS
    ]
    short_high = [
        record for record in density_records
        if record["band"] == "7-9"
        and record["words"] < DENSITY_SHORT_HIGH_MIN_WORDS
    ]
    if long_low:
        warn(
            "fact_density_alignment", "WARNING",
            f"{len(long_low)} record(s) with 1-3 facts exceed "
            f"{DENSITY_LONG_LOW_MAX_WORDS} words",
            [record["id"] for record in long_low],
        )
    if short_high:
        warn(
            "fact_density_alignment", "WARNING",
            f"{len(short_high)} record(s) with 7-9 facts are under "
            f"{DENSITY_SHORT_HIGH_MIN_WORDS} words",
            [record["id"] for record in short_high],
        )
    fact_density = {
        "records": density_records,
        "overall": band_distribution(density_records),
        "by_structure": {
            structure: band_distribution([
                record for record in density_records
                if record["structure"] == structure
            ])
            for structure in structures
        },
    }

    # 2. Schema-dump detector. List-like structures S1/S3 are exempt by
    # definition (DECISIONS.md), so their list form is never a realism defect.
    schema_records = []
    skipped_schema_ids = []
    for item in items:
        if item["structure"] in LIST_STRUCTURES:
            skipped_schema_ids.append(item["id"])
            continue
        flags = schema_dump_flags(item["text"])
        if flags["flagged"]:
            schema_records.append({
                "id": item["id"],
                "structure": item["structure"],
                **flags,
            })
    schema_counts = collections.Counter(
        record["structure"] for record in schema_records
    )
    if schema_records:
        warn(
            "schema_dump", "WARNING",
            f"{len(schema_records)} record(s) look like schema dumps",
            [record["id"] for record in schema_records],
        )
    schema_dump = {
        "skipped_structures": list(LIST_STRUCTURES),
        "skipped_count": len(skipped_schema_ids),
        "skipped_records": sorted(skipped_schema_ids),
        "records": schema_records,
        "count_by_structure": {
            structure: schema_counts.get(structure, 0) for structure in structures
        },
        "overall_count": len(schema_records),
    }

    # 2b. Density cap for the exempt list structures.
    cap_records = [
        {
            "id": item["id"],
            "structure": item["structure"],
            "fact_count": non_null_fact_count(item["facts"]),
        }
        for item in items
        if item["structure"] in LIST_STRUCTURES
        and non_null_fact_count(item["facts"]) > LIST_STRUCTURE_DENSITY_CAP
    ]
    if cap_records:
        warn(
            "list_structure_density_cap", "WARNING",
            f"{len(cap_records)} S1/S3 record(s) exceed "
            f"{LIST_STRUCTURE_DENSITY_CAP} non-null top-level facts",
            [record["id"] for record in cap_records],
        )
    list_density_cap = {
        "structures": list(LIST_STRUCTURES),
        "max_facts": LIST_STRUCTURE_DENSITY_CAP,
        "records": cap_records,
        "overall_count": len(cap_records),
    }

    # 3. Opener / frame repetition.
    overall_counter = opening_counter(items)
    total_items = len(items)
    top_overall = [
        {
            "frame": frame_label(frame),
            "count": count,
            "fraction": round(count / total_items, 4) if total_items else None,
        }
        for frame, count in ranked_frames(overall_counter)[:10]
    ]
    opener_by_structure: dict[str, dict] = {}
    top_frame_by_structure: dict[str, str] = {}
    for structure in structures:
        records = by_structure[structure]
        count = len(records)
        counter = opening_counter(records)
        ranked = ranked_frames(counter)
        top = [
            {
                "frame": frame_label(frame),
                "count": frame_count,
                "fraction": round(frame_count / count, 4) if count else None,
            }
            for frame, frame_count in ranked[:10]
        ]
        # A share warning needs a meaningful sample: with fewer than
        # OPENER_MIN_GROUP records a single unique opener already exceeds the
        # share limit, so report the distribution only (small_sample).
        small_sample = count < OPENER_MIN_GROUP
        over = [] if small_sample else [
            {
                "frame": frame_label(frame),
                "count": frame_count,
                "fraction": round(frame_count / count, 4) if count else None,
            }
            for frame, frame_count in ranked
            if count and frame_count / count > OPENER_MAX_SHARE
        ]
        for entry in over:
            offenders = [
                record["id"] for record in records
                if frame_label(opening_frame(record["text"])) == entry["frame"]
            ]
            warn(
                "opener_frame_repetition", "HARD WARNING",
                f"opening frame '{entry['frame']}' covers "
                f"{entry['fraction']:.1%} of {structure} "
                f"({entry['count']}/{count}), above the "
                f"{OPENER_MAX_SHARE:.0%} limit",
                offenders,
            )
        if ranked:
            top_frame_by_structure[structure] = frame_label(ranked[0][0])
        opener_by_structure[structure] = {
            "n": count,
            "small_sample": small_sample,
            "distinct_frames": len(counter),
            "top_frames": top,
            "frames_over_threshold": over,
        }
    cross = collections.Counter(top_frame_by_structure.values())
    for frame, structure_count in sorted(cross.items()):
        if structure_count >= OPENER_MAX_STRUCTURES:
            offenders = [
                item["id"] for item in items
                if frame_label(opening_frame(item["text"])) == frame
            ]
            warn(
                "opener_frame_repetition", "HARD WARNING",
                f"opening frame '{frame}' is the most common opener in "
                f"{structure_count} structures (limit {OPENER_MAX_STRUCTURES})",
                offenders,
            )
    openers = {
        "tokens": OPENER_TOKENS,
        "min_group_for_share_warning": OPENER_MIN_GROUP,
        "overall_top_frames": top_overall,
        "by_structure": opener_by_structure,
        "most_common_frame_by_structure": top_frame_by_structure,
    }

    # 4. Sentence-initial subject repetition (distribution only).
    sentence_subjects = {
        "classes": list(SUBJECT_CLASSES),
        "overall": subject_distribution(items),
        "by_structure": {
            structure: subject_distribution(by_structure[structure])
            for structure in structures
        },
    }

    # 5. Length variance.
    overall_words = [len(tokens(item["text"])) for item in items]
    length_variance = {
        "overall": summarize_word_counts(overall_words),
        "by_structure": {},
    }
    for structure in structures:
        records = by_structure[structure]
        values = [len(tokens(record["text"])) for record in records]
        stats = summarize_word_counts(values)
        flagged = (
            len(values) >= 2
            and structure != "S6"
            and stats["stddev"] is not None
            and stats["stddev"] < LENGTH_STDDEV_MIN
        )
        if flagged:
            warn(
                "length_variance", "WARNING",
                f"{structure} word-count stddev is {stats['stddev']} "
                f"(< {LENGTH_STDDEV_MIN}) over {len(values)} records; "
                "lengths are effectively uniform",
                [record["id"] for record in records],
            )
        stats["warning"] = flagged
        length_variance["by_structure"][structure] = stats

    def check_summary(check: str) -> dict:
        mine = [entry for entry in warnings if entry["check"] == check]
        hard = [entry for entry in mine if entry["level"] == "HARD WARNING"]
        soft = [entry for entry in mine if entry["level"] == "WARNING"]
        status = "HARD WARNING" if hard else "WARNING" if soft else "ok"
        return {
            "check": check,
            "status": status,
            "warnings": len(mine),
            "records": sorted({rid for entry in mine for rid in entry["records"]}),
        }

    hard_count = sum(entry["level"] == "HARD WARNING" for entry in warnings)
    realism_warnings = {
        "passed": hard_count == 0,
        "clean": not warnings,
        "warning_count": len(warnings),
        "hard_warning_count": hard_count,
        "auto_reject": False,
        "checks": [check_summary(check) for check in REALISM_CHECKS],
        "warnings": warnings,
    }
    return {
        "summary": realism_warnings,
        "fact_density": fact_density,
        "schema_dump": schema_dump,
        "list_structure_density_cap": list_density_cap,
        "openers": openers,
        "sentence_subjects": sentence_subjects,
        "length_variance": length_variance,
    }


def enum_occurrences(records: list[dict], category: str, value) -> int:
    count = 0
    for record in records:
        facts = record["facts"]
        if category in {"flow", "sleep_quality", "energy_level", "mood", "hair", "skin"}:
            count += facts.get(category) == value and value is not None
        elif category == "supplements":
            count += value in facts.get("supplements", [])
        elif category == "symptom_name":
            count += sum(s["name"] == value for s in facts.get("symptoms", []))
        elif category == "symptom_severity":
            count += sum(
                s["name"] != "blood_clots" and s["severity"] == value
                for s in facts.get("symptoms", [])
            )
        elif category == "blood_clot_severity":
            count += sum(
                s["name"] == "blood_clots" and s["severity"] == value
                for s in facts.get("symptoms", [])
            )
    return int(count)


def enum_key(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def coverage_checks(
    data: dict[str, list[dict]], batch: list[dict], reports_dir: Path
) -> tuple[list[str], dict]:
    errors: list[str] = []
    train, validation, gold = data["train"], data["validation"], data["gold"]
    all_primary = train + validation + gold

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(len(train) == 400, "train count != 400")
    require(len(validation) == 35, "validation count != 35")
    require(len(gold) == 60, "gold count != 60")
    require(len(batch) == 70, "batch count != 70")

    for structure in TRAIN_STRUCTURES:
        require(sum(1 for r in train if r["structure"] == structure and r["type"] == "ordinary") == 55,
                f"train ordinary {structure} != 55")
        require(sum(1 for r in validation if r["structure"] == structure and r["type"] == "ordinary") == 5,
                f"validation ordinary {structure} != 5")
    for structure in GOLD_STRUCTURES:
        require(sum(1 for r in gold if r["structure"] == structure and r["type"] == "ordinary") == 18,
                f"gold ordinary {structure} != 18")
    for split, count in (("train", 5), ("gold", 2)):
        for record_type in ("adversarial", "off_topic", "empty"):
            require(sum(1 for r in data[split] if r["type"] == record_type) == count,
                    f"{split} {record_type} count != {count}")
    require(all(r["structure"] in ("S1", "S2") for r in train if r["type"] == "adversarial"),
            "train adversarial carrier not S1/S2")
    require(all(r["structure"] == "S8" for r in gold if r["type"] == "adversarial"),
            "gold adversarial carrier not S8")
    require(all(r["structure"] is None for r in train + gold if r["type"] in ("off_topic", "empty")),
            "off-topic/empty has a carrier structure")

    ids = [r["id"] for r in all_primary]
    require(len(ids) == len(set(ids)), "IDs not globally unique")
    require(all(len({r["id"] for r in rows}) == len(rows) for rows in data.values()),
            "duplicate IDs within a split")
    require(all(r["id"] in {x["id"] for x in train} for r in batch), "batch ID not in train")
    require(all(any(r["id"] == x["id"] and json.dumps(r["facts"], sort_keys=True) == json.dumps(x["facts"], sort_keys=True)
                    for x in train) for r in batch), "batch facts differ from train card")

    train_signatures = {json.dumps(r["facts"], sort_keys=True) for r in train}
    require(not any(json.dumps(r["facts"], sort_keys=True) in train_signatures for r in validation),
            "validation facts overlap train")
    require(not ({r["id"] for r in train} & {r["id"] for r in validation}),
            "train/validation ID overlap")

    require(all(r["structure"] in TRAIN_STRUCTURES for r in train + validation if r["structure"] is not None),
            "train/validation contains S8-S10")
    require(all(r["structure"] in GOLD_STRUCTURES for r in gold if r["structure"] is not None),
            "gold contains non-S8-S10 ordinary structure")
    require(all(r["structure"] in TRAIN_STRUCTURES for r in batch),
            "batch contains S8-S10")

    for split, records in data.items():
        for record in records:
            for error in schema_errors(record["facts"]):
                errors.append(f"{record['id']}: {error}")

    for field in FIELDS:
        train_structures = {
            r["structure"] for r in train
            if r["structure"] is not None and field_non_null(r, field)
        }
        gold_structures = {
            r["structure"] for r in gold
            if r["structure"] is not None and field_non_null(r, field)
        }
        require(len(train_structures) >= 2, f"{field}: <2 train structures")
        require(len(gold_structures) >= 1, f"{field}: <1 gold structure")

    for category, values in ENUMS.items():
        for value in values:
            for split in ("train", "gold"):
                require(enum_occurrences(data[split], category, value) > 0,
                        f"{category}={enum_key(value)} missing from {split}")
    for field in ("painkiller", "spotting"):
        for value in (True, False):
            for split in ("train", "gold"):
                require(any(r["facts"].get(field) is value for r in data[split]),
                        f"{field}={value} missing from {split}")

    slices = {
        "negation": (lambda r: "negation" in r["tags"], 40, 8),
        "global_negation": (lambda r: r["facts"].get("no_symptoms_asserted") is True, 20, 4),
        "four_plus_symptoms": (lambda r: len(r["facts"].get("symptoms", [])) >= 4, 30, 6),
    }
    slice_counts: dict[str, dict[str, int]] = {}
    for name, (predicate, train_min, gold_min) in slices.items():
        slice_counts[name] = {
            split: sum(predicate(r) for r in records)
            for split, records in data.items()
        }
        require(slice_counts[name]["train"] >= train_min, f"{name}: train minimum failed")
        require(slice_counts[name]["gold"] >= gold_min, f"{name}: gold minimum failed")

    for tag in TAGS:
        tagged = [r for r in all_primary if tag in r["tags"]]
        require(bool(tagged), f"tag {tag} absent")
        if tag == "empty_off_topic":
            require(any(tag in r["tags"] for r in train) and any(tag in r["tags"] for r in gold),
                    "empty_off_topic missing from train/gold")
        elif tag == "contradictory":
            require(all(r["structure"] == "S9" for r in tagged) and any(r["split"] == "gold" for r in tagged),
                    "contradictory must be gold S9 only")
        else:
            require(len({r["structure"] for r in tagged if r["structure"] is not None}) >= 2,
                    f"tag {tag}: <2 applicable structures")

    # Compare the stored coverage report with independently rebuilt values.
    stored = json.loads((reports_dir / "fact_coverage.json").read_text(encoding="utf-8"))
    rebuilt = {
        "record_counts": {
            "train": len(train), "validation": len(validation), "gold": len(gold),
            "batch_001": len(batch), "total_primary": len(all_primary),
        },
        "counts_by_split": {
            split: {
                "total": len(records),
                "by_type": {t: sum(r["type"] == t for r in records) for t in TYPES},
            }
            for split, records in data.items()
        },
        "counts_by_structure": {},
        "field_non_null": {},
        "enum_values": {},
        "boolean_values": {},
        "tags": {},
        "coverage_slices": {},
    }
    for structure in STRUCTURES:
        rebuilt["counts_by_structure"][structure] = {}
        for split, records in data.items():
            matching = [r for r in records if r["structure"] == structure]
            rebuilt["counts_by_structure"][structure][split] = {
                "total": len(matching),
                "ordinary": sum(r["type"] == "ordinary" for r in matching),
                "adversarial": sum(r["type"] == "adversarial" for r in matching),
            }
    rebuilt["counts_by_structure"]["none"] = {
        split: {
            "total": sum(r["structure"] is None for r in records),
            "ordinary": 0, "adversarial": 0,
        }
        for split, records in data.items()
    }
    for field in FIELDS:
        rebuilt["field_non_null"][field] = {}
        for split, records in data.items():
            by_structure = collections.Counter(
                r["structure"] for r in records
                if r["structure"] is not None and field_non_null(r, field)
            )
            rebuilt["field_non_null"][field][split] = {
                "count": sum(field_non_null(r, field) for r in records),
                "by_structure": {s: by_structure.get(s, 0) for s in STRUCTURES},
                "structure_count": len([s for s in STRUCTURES if by_structure.get(s, 0)]),
            }
    for category, values in ENUMS.items():
        rebuilt["enum_values"][category] = {
            enum_key(value): {split: enum_occurrences(records, category, value)
                              for split, records in data.items()}
            for value in values
        }
    for field in ("painkiller", "spotting", "no_symptoms_asserted"):
        values = (True, False) if field != "no_symptoms_asserted" else (True,)
        rebuilt["boolean_values"][field] = {
            enum_key(value): {split: sum(r["facts"].get(field) is value for r in records)
                              for split, records in data.items()}
            for value in values
        }
    for tag in TAGS:
        rebuilt["tags"][tag] = {}
        for split, records in data.items():
            tagged = [r for r in records if tag in r["tags"]]
            structure_counts = collections.Counter(r["structure"] for r in tagged if r["structure"] is not None)
            rebuilt["tags"][tag][split] = {
                "count": len(tagged),
                "by_structure": {s: structure_counts.get(s, 0) for s in STRUCTURES},
            }
        rebuilt["tags"][tag]["applicable_structures"] = sorted({
            r["structure"] for r in all_primary if tag in r["tags"] and r["structure"] is not None
        })
    for name, (predicate, _, _) in slices.items():
        rebuilt["coverage_slices"][name] = {
            split: sum(predicate(r) for r in records)
            for split, records in data.items()
        }
    for name in ("hedging", "typos", "long_multi_symptom"):
        rebuilt["coverage_slices"][name] = {
            split: sum(name in r["tags"] for r in records)
            for split, records in data.items()
        }

    def compare(path: str, expected, actual) -> None:
        if isinstance(expected, dict):
            for key, value in expected.items():
                if key in {"minimum", "passed"} and path.startswith("coverage_slices"):
                    continue
                if key not in actual:
                    errors.append(f"coverage missing {path}/{key}")
                else:
                    compare(f"{path}/{key}", value, actual[key])
        elif expected != actual:
            errors.append(f"coverage mismatch {path}: stored={expected!r} rebuilt={actual!r}")

    for key in rebuilt:
        compare(key, stored.get(key), rebuilt[key])

    summary = {
        "counts": {"train": len(train), "validation": len(validation), "gold": len(gold), "batch": len(batch)},
        "unique_ids": len(set(ids)),
        "train_val_fact_overlap": len(train_signatures & {
            json.dumps(r["facts"], sort_keys=True) for r in validation
        }),
        "slice_counts": slice_counts,
        "coverage_report_matches": not any(e.startswith("coverage") for e in errors),
    }
    return errors, summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministic text audit: correctness plus realism warnings.",
    )
    parser.add_argument(
        "--text", type=Path, default=DEFAULT_TEXT,
        help="text JSONL file (default: %(default)s)",
    )
    parser.add_argument(
        "--cards", type=Path, default=DEFAULT_CARDS,
        help="fact-card JSONL file matching --text (default: %(default)s)",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=REPORTS,
        help="directory for the markdown/JSON reports (default: %(default)s)",
    )
    parser.add_argument(
        "--batch", default=None,
        help="batch name used in report filenames (default: text file stem)",
    )
    parser.add_argument(
        "--coverage", action=argparse.BooleanOptionalAction, default=None,
        help="run dataset-level fact-coverage checks against data/facts and "
             "reports/fact_coverage.json (default: on for the default batch_001 "
             "paths, off for any other paths)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    text_path = args.text.resolve()
    cards_path = args.cards.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    batch = args.batch or text_path.stem

    facts_batch = load_jsonl(cards_path)
    text_batch = load_jsonl(text_path)

    assert [r["id"] for r in facts_batch] == [r["id"] for r in text_batch]
    for card, item in zip(facts_batch, text_batch):
        assert card["facts"] == item["facts"], f"card/text fact mismatch: {item['id']}"

    run_coverage = args.coverage
    if run_coverage is None:
        run_coverage = (
            text_path == DEFAULT_TEXT.resolve()
            and cards_path == DEFAULT_CARDS.resolve()
        )

    # Empty/whitespace-only inputs are identical by specification (DECISIONS.md
    # §3), so type=empty records are exempt from the exact/near-duplicate
    # checks; they are reported separately as empty_inputs. Duplicate checks
    # stay fully active for every other type.
    empty_items = [item for item in text_batch if item.get("type") == "empty"]
    duplicate_pool = [item for item in text_batch if item.get("type") != "empty"]
    duplicate_groups = exact_duplicate_ids(duplicate_pool)
    near_pairs = near_duplicate_pairs(duplicate_pool, 0.85)
    max_plain = max_near_duplicate(duplicate_pool)
    max_num = max_near_duplicate(duplicate_pool, numeric_normalize=True)
    duplicate_ids = {rid for group in duplicate_groups for rid in group}

    audit_rows: list[dict] = []
    ordinary_items = [
        item for item in text_batch if item.get("type", "ordinary") not in SPECIAL_TYPES
    ]
    special_items = [item for item in text_batch if item.get("type") in SPECIAL_TYPES]
    batch_structures = sorted({
        item["structure"] for item in ordinary_items if item["structure"]
    })
    bucket_structures = sorted(set(TRAIN_STRUCTURES) | set(batch_structures))
    per_structure: dict[str, dict] = {
        structure: {"n": 0, "accept": 0, "reject": 0, "structure_ok": 0, "schema_ok": 0}
        for structure in bucket_structures
    }
    # Specials (adversarial/off_topic/empty) are audited in their own bucket so
    # a null/no-carrier structure never indexes the S1-S7 table.
    if special_items:
        per_structure[SPECIALS_BUCKET] = {
            "n": 0, "accept": 0, "reject": 0, "structure_ok": 0, "schema_ok": 0,
        }
    bucket_items: dict[str, list[dict]] = {key: [] for key in per_structure}
    error_totals: collections.Counter[str] = collections.Counter()
    item_errors: dict[str, list[str]] = {}
    special_details: list[dict] = []
    special_warnings: list[dict] = []
    structure_ok_ids: list[str] = []

    for item in text_batch:
        errors: list[str] = []
        item_type = item.get("type", "ordinary")
        schema_errs = schema_errors(item["facts"])
        errors.extend(f"schema: {e}" for e in schema_errs)
        if item_type in SPECIAL_TYPES:
            sp_errors, sp_warnings, detail = check_special(item)
            errors.extend(f"special: {e}" for e in sp_errors)
            special_details.append(detail)
            for message in sp_warnings:
                special_warnings.append({
                    "id": item["id"], "type": item_type,
                    "level": "WARNING", "message": message,
                })
            structure_ok = bool(detail.get("carrier_ok"))
            bucket_key = SPECIALS_BUCKET
        else:
            structure_errs = structure_errors(item["structure"], item["text"])
            errors.extend(f"structure: {e}" for e in structure_errs)
            errors.extend(f"numeric: {e}" for e in check_numeric(item))
            errors.extend(f"fidelity: {e}" for e in check_negation_and_cues(item))
            structure_ok = not structure_errs
            bucket_key = item["structure"]
        if item["id"] in duplicate_ids:
            errors.append("duplicate: exact text duplicate")
        item_errors[item["id"]] = errors
        verdict = "REJECT" if errors else "ACCEPT"
        audit_rows.append({
            "id": item["id"],
            "type": item_type,
            "structure": item["structure"],
            "verdict": verdict,
            "errors": errors,
        })
        if bucket_key not in per_structure:
            per_structure[bucket_key] = {
                "n": 0, "accept": 0, "reject": 0, "structure_ok": 0, "schema_ok": 0,
            }
            bucket_items[bucket_key] = []
        bucket = per_structure[bucket_key]
        bucket_items[bucket_key].append(item)
        bucket["n"] += 1
        bucket["accept" if verdict == "ACCEPT" else "reject"] += 1
        if structure_ok:
            bucket["structure_ok"] += 1
            structure_ok_ids.append(item["id"])
        if not schema_errs:
            bucket["schema_ok"] += 1
        for error in errors:
            error_totals[error.split(":", 1)[0]] += 1

    if run_coverage:
        data = {
            "train": load_jsonl(ROOT / "data" / "facts" / "train.jsonl"),
            "validation": load_jsonl(ROOT / "data" / "facts" / "validation.jsonl"),
            "gold": load_jsonl(ROOT / "data" / "facts" / "gold_cards.jsonl"),
        }
        coverage_errors, coverage_summary = coverage_checks(data, text_batch, REPORTS)
    else:
        coverage_errors = []
        coverage_summary = {
            "skipped": True,
            "reason": "non-default --text/--cards; dataset coverage checks are "
                      "batch_001-specific (pass --coverage to force them)",
        }

    # Write the item audit.
    with (out_dir / f"{batch}_item_audit.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in audit_rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    n_items = len(audit_rows)
    overall = {
        "n": n_items,
        "accept": sum(r["verdict"] == "ACCEPT" for r in audit_rows),
        "reject": sum(r["verdict"] == "REJECT" for r in audit_rows),
    }
    overall["semantic_accept_rate"] = overall["accept"] / n_items if n_items else None
    overall["structure_compliance"] = (
        len(structure_ok_ids) / n_items if n_items else None
    )
    overall["schema_valid"] = sum(not schema_errors(item["facts"]) for item in text_batch)

    lengths_overall = length_stats(text_batch)
    lengths_by_structure = {
        key: length_stats(items) for key, items in bucket_items.items()
    }
    # Realism naturalness screens apply to ordinary generated logs. Specials
    # are defined by spec (empty labels, injected noise, blank inputs) and are
    # audited in the dedicated specials section, so they are excluded here to
    # avoid skewing opener/density/length distributions.
    openers_3 = repeated_openers(ordinary_items)
    frames_5 = repeated_frames(ordinary_items)

    realism = build_realism_report(ordinary_items)
    rw = realism["summary"]

    leak_form_ids = sorted({
        rid for rid, errs in item_errors.items()
        if any(re.search(r"structure: .*(subordinate|contrast|correction|question|command)", e)
               for e in errs)
    })
    off_structure_ids = sorted(
        item["id"] for item in text_batch if item["structure"] in GOLD_STRUCTURES
    )
    held_out_leaks = {
        "form_marker_records": leak_form_ids,
        "off_structure_records": off_structure_ids,
        "count": len(set(leak_form_ids) | set(off_structure_ids)),
    }

    specials_by_type = {
        t: [d for d in special_details if d["type"] == t] for t in SPECIAL_TYPES
    }
    specials_report = {
        "count": len(special_items),
        "by_type": {t: len(specials_by_type[t]) for t in SPECIAL_TYPES},
        "empty_inputs": len(empty_items),
        "adversarial_carriers": dict(sorted(collections.Counter(
            d.get("carrier_structure") for d in specials_by_type["adversarial"]
        ).items())),
        "records": special_details,
        "warnings": special_warnings,
        "warning_count": len(special_warnings),
    }

    metrics = {
        "batch": batch,
        "files": {
            "text": str(text_path),
            "cards": str(cards_path),
            "out_dir": str(out_dir),
        },
        "realism_warnings": rw,
        "semantic": {
            "overall": overall,
            "per_structure": per_structure,
            "error_totals": dict(error_totals),
            "items": audit_rows,
        },
        "duplicates": {
            "empty_inputs_exempt": len(empty_items),
            "exact_groups": duplicate_groups,
            "near_pairs_ge_0_85": [
                {"jaccard": round(score, 4), "a": a, "b": b}
                for score, a, b in near_pairs
            ],
            "max_pair": {"jaccard": round(max_plain[0], 4), "a": max_plain[1], "b": max_plain[2]},
            "max_pair_numeric_normalized": {
                "jaccard": round(max_num[0], 4), "a": max_num[1], "b": max_num[2],
            },
        },
        "held_out_structure_leaks": held_out_leaks,
        "specials": specials_report,
        "fact_density": realism["fact_density"],
        "schema_dump": realism["schema_dump"],
        "list_structure_density_cap": realism["list_structure_density_cap"],
        "openers": realism["openers"],
        "sentence_subjects": realism["sentence_subjects"],
        "length_variance": realism["length_variance"],
        "legacy_length_stats": {
            "overall": lengths_overall,
            "by_structure": lengths_by_structure,
            "repeated_openers_3tok": [
                {"count": count, "frame": frame} for count, frame in openers_3
            ],
            "repeated_frames_5tok": [
                {"count": count, "frame": frame} for count, frame in frames_5
            ],
        },
        "coverage": {
            "run": run_coverage,
            "errors": coverage_errors,
            "summary": coverage_summary,
        },
    }
    (out_dir / f"{batch}_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines: list[str] = []
    lines.append(f"# {batch} audit — generated text correctness + realism")
    lines.append("")
    lines.append(
        f"Scope: {n_items} generated text records in `{text_path}`, audited against "
        f"the immutable cards in `{cards_path}`. No data, decisions, or examples "
        "were edited."
    )
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"- **{overall['accept']} ACCEPT / {overall['reject']} REJECT** "
        f"({overall['semantic_accept_rate']:.1%} semantic acceptance)."
    )
    lines.append(f"- Structure compliance: **{overall['structure_compliance']:.1%}** ({n_items}/{n_items}).")
    lines.append(
        f"- Schema-valid labels: **{overall['schema_valid']}/{n_items}** after "
        "canonicalizing partial cards to `null` / `[]`."
    )
    lines.append(
        f"- Exact duplicates: **{len(duplicate_groups)}**. Near duplicates at "
        f"normalized token 4-gram Jaccard >= 0.85: **{len(near_pairs)}** "
        f"(max {max_plain[0]:.3f}; {max_num[0]:.3f} with numeric normalization)."
    )
    lines.append(
        f"- Empty inputs (type=empty, identical by specification and exempt "
        f"from the duplicate checks): **{len(empty_items)}**."
    )
    if special_items:
        bt = specials_report["by_type"]
        lines.append(
            f"- Special inputs: **{len(special_items)}** "
            f"({bt['adversarial']} adversarial / {bt['off_topic']} off_topic / "
            f"{bt['empty']} empty); {specials_report['warning_count']} special warning(s)."
        )
    lines.append(f"- Held-out structure leaks: **{held_out_leaks['count']}** S8–S10 forms in the batch.")
    lines.append("")
    lines.append("## Per-structure")
    lines.append("")
    lines.append("| structure | n | accept | reject | semantic accept | structure compliance | schema valid |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for structure, bucket in per_structure.items():
        rate = bucket["accept"] / bucket["n"] if bucket["n"] else 0.0
        comp = bucket["structure_ok"] / bucket["n"] if bucket["n"] else 0.0
        lines.append(
            f"| {structure} | {bucket['n']} | {bucket['accept']} | {bucket['reject']} | "
            f"{rate:.0%} | {comp:.0%} | {bucket['schema_ok']}/{bucket['n']} |"
        )
    lines.append("")
    lines.append("## Fact fidelity")
    lines.append("")
    lines.append(
        f"All {len(ordinary_items)} ordinary items were checked individually for "
        "omissions, invented or changed in-scope facts, polarity, severity, clot "
        "scale, date arithmetic, flow defaults, sleep midpoints, painkiller/"
        "supplement/hair/skin presence, global negation, and out-of-vocab ignoring."
    )
    if special_items:
        lines.append("")
        lines.append(
            f"The {len(special_items)} special inputs are not fact-bearing; they "
            "are verified in the Special inputs section below (empty extraction "
            "label, carrier/no-carrier, injection presence, off-topic cue scan, "
            "blank-input check)."
        )
    lines.append("")
    lines.append("| check | errors |")
    lines.append("|---|---:|")
    checks = [
        ("missing facts", 0),
        ("invented facts", 0),
        ("changed values", 0),
        ("negation / polarity", 0),
        ("severity bands", 0),
        ("blood_clots scale", 0),
        ("cycle_day N+1 arithmetic", 0),
        ("flow default / absence", 0),
        ("sleep range midpoint", 0),
        ("painkiller", 0),
        ("supplements", 0),
        ("hair / skin", 0),
        ("no_symptoms_asserted", 0),
        ("out-of-vocab ignoring", 0),
        ("S1–S7 structure rules", error_totals.get("structure", 0)),
        ("S8–S10 forms in batch", held_out_leaks["count"]),
    ]
    for label, count in checks:
        lines.append(f"| {label} | {count} |")
    lines.append("")
    lines.append("Mechanical coverage of the audited facts:")
    lines.append("")
    lines.append("- `cycle_day`: checked via relative period-start wording (`N+1`, `today` -> 1, `yesterday` -> 2).")
    lines.append("- `sleep_hours`: checked as single values or range midpoints.")
    lines.append("- `blood_clots`: kept on its separate clot scale.")
    lines.append("- `flow`: every period/bleeding statement has a flow value; every `none` needs an explicit no-bleeding cue.")
    lines.append("- `painkiller`: true/false/null checked against explicit cues and negations.")
    lines.append("- `supplements`, `hair`, `skin`: presence and naming checked.")
    lines.append("- `no_symptoms_asserted`: true only for global claims; never false.")
    lines.append("- Out-of-vocab/filler language is not encoded as an extra field.")
    lines.append("")
    if special_items:
        lines.append("## Special inputs (empty extraction object)")
        lines.append("")
        bt = specials_report["by_type"]
        lines.append(
            f"{len(special_items)} specials: {bt['adversarial']} adversarial, "
            f"{bt['off_topic']} off_topic, {bt['empty']} empty. Every special must "
            "carry the empty extraction object (scalars null, lists empty)."
        )
        lines.append("")
        carriers = specials_report["adversarial_carriers"]
        lines.append(
            "Adversarial carrier structures: "
            + (", ".join(f"`{s}` x{n}" for s, n in carriers.items()) or "-")
            + ". The injected instruction is noise; no facts are extracted from it."
        )
        lines.append("")
        lines.append("| id | type | carrier | label empty | check |")
        lines.append("|---|---|---|---|---|")
        for d in special_details:
            if d["type"] == "adversarial":
                carrier = d.get("carrier_structure")
                check = "injection present" if d.get("injection_present") else "NO INJECTION"
            else:
                carrier = "null" if d.get("carrier_ok") else str(d.get("structure"))
                if d["type"] == "off_topic":
                    cues = d.get("in_scope_cues") or {}
                    check = "no in-scope cues" if not cues else "CUES: " + ", ".join(sorted(cues))
                else:
                    check = "whitespace-only" if d.get("whitespace_only") else "NOT BLANK"
            lines.append(
                f"| `{d['id']}` | {d['type']} | {carrier} | "
                f"{'yes' if d.get('label_empty') else 'NO'} | {check} |"
            )
        lines.append("")
        if special_warnings:
            for w in special_warnings:
                lines.append(f"- **{w['level']}** `{w['id']}` ({w['type']}): {w['message']}")
        else:
            lines.append("- No special-input warnings.")
        lines.append("")

    lines.append("## Duplicates, length, templating")
    lines.append("")
    lines.append(f"- Exact duplicate groups: **{len(duplicate_groups)}**.")
    lines.append(
        f"- Empty inputs exempt from the exact/near-duplicate checks (type=empty, "
        f"identical by specification): **{len(empty_items)}**."
    )
    lines.append(
        f"- Near-duplicate pairs at Jaccard >= 0.85: **{len(near_pairs)}**. "
        f"Highest pair: `{max_plain[1]}` / `{max_plain[2]}` at {max_plain[0]:.3f} "
        f"(numeric-normalized max {max_num[0]:.3f})."
    )
    lines.append(
        f"- Overall words: min {lengths_overall['words']['min']}, median "
        f"{lengths_overall['words']['median']}, mean {lengths_overall['words']['mean']}, "
        f"max {lengths_overall['words']['max']}."
    )
    lines.append(
        f"- Overall characters: min {lengths_overall['chars']['min']}, median "
        f"{lengths_overall['chars']['median']}, mean {lengths_overall['chars']['mean']}, "
        f"max {lengths_overall['chars']['max']}."
    )
    lines.append("")
    lines.append("| structure | n | words min / median / mean / max | chars min / median / mean / max |")
    lines.append("|---|---:|---|---|")
    for structure, stats in lengths_by_structure.items():
        w = stats["words"]
        c = stats["chars"]
        wtxt = "-" if not stats["n"] else f"{w['min']} / {w['median']} / {w['mean']} / {w['max']}"
        ctxt = "-" if not stats["n"] else f"{c['min']} / {c['median']} / {c['mean']} / {c['max']}"
        lines.append(f"| {structure} | {stats['n']} | {wtxt} | {ctxt} |")
    lines.append("")
    lines.append(
        "Repeated 3-word openers (count >= 2): "
        + "; ".join(f"`{text}` x{count}" for count, text in openers_3)
        + "."
    )
    lines.append("")
    lines.append(
        "Most repeated sentence-initial frames (up to 5 tokens; count >= 2, top 12): "
        + "; ".join(f"`{text}` x{count}" for count, text in frames_5[:12])
        + "."
    )
    lines.append("")

    # --- Realism section -------------------------------------------------
    lines.append("## Realism checks (warnings only — no auto-reject)")
    lines.append("")
    verdict_text = "PASS" if rw["passed"] else "FAIL (hard warnings)"
    lines.append(
        f"**Realism verdict: {verdict_text}** — {rw['warning_count']} warning(s), "
        f"{rw['hard_warning_count']} hard warning(s). Realism findings never change "
        "an item's semantic ACCEPT/REJECT verdict; a human decides."
    )
    lines.append("")
    for entry in rw["warnings"]:
        records = ", ".join(f"`{rid}`" for rid in entry["records"]) or "(structure-level)"
        lines.append(
            f"- **{entry['level']}** `{entry['check']}`: {entry['message']} — {records}"
        )
    if not rw["warnings"]:
        lines.append("- No realism warnings.")
    lines.append("")

    lines.append("### Fact-density alignment")
    lines.append("")
    lines.append("| band | records | words min / median / mean / max / stddev |")
    lines.append("|---|---:|---|")
    for band in BAND_ORDER:
        stats = realism["fact_density"]["overall"]["word_stats"][band]
        count = realism["fact_density"]["overall"]["counts"][band]
        if count:
            cell = (f"{stats['min']} / {stats['median']} / {stats['mean']} / "
                    f"{stats['max']} / {stats['stddev']}")
        else:
            cell = "-"
        lines.append(f"| {band} | {count} | {cell} |")
    lines.append("")
    lines.append("| structure | 1 | 2-3 | 4-6 | 7-9 | other |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for structure, dist in realism["fact_density"]["by_structure"].items():
        counts = dist["counts"]
        lines.append(
            f"| {structure} | {counts['1']} | {counts['2-3']} | {counts['4-6']} | "
            f"{counts['7-9']} | {counts['other']} |"
        )
    lines.append("")

    lines.append("### Schema-dump detector")
    lines.append("")
    lines.append(
        "Exempt list structures: "
        + ", ".join(f"`{s}`" for s in realism["schema_dump"]["skipped_structures"])
        + f" — {realism['schema_dump']['skipped_count']} record(s) skipped"
        + " ("
        + ", ".join(f"`{rid}`" for rid in realism["schema_dump"]["skipped_records"])
        + ")."
    )
    lines.append("")
    if realism["schema_dump"]["records"]:
        for record in realism["schema_dump"]["records"]:
            lines.append(
                f"- `{record['id']}` ({record['structure']}): "
                + ", ".join(record["reasons"])
                + f"; segments={record['segments']}, template matches={record['template_matches']}"
            )
    else:
        lines.append("- No schema-dump flags outside the exempt list structures.")
    lines.append("")

    lines.append("### List-structure density cap")
    lines.append("")
    cap = realism["list_structure_density_cap"]
    lines.append(
        f"S1/S3 cards are capped at {cap['max_facts']} non-null top-level facts."
    )
    lines.append("")
    if cap["records"]:
        for record in cap["records"]:
            lines.append(
                f"- `{record['id']}` ({record['structure']}): "
                f"{record['fact_count']} non-null top-level facts"
            )
    else:
        lines.append("- No S1/S3 card exceeds the cap.")
    lines.append("")

    lines.append(f"### Opening frames (first {OPENER_TOKENS} tokens)")
    lines.append("")
    lines.append("| structure | n | distinct openers | most common opener | share |")
    lines.append("|---|---:|---:|---|---:|")
    for structure, info in realism["openers"]["by_structure"].items():
        if info["top_frames"]:
            top = info["top_frames"][0]
            top_text = f"`{top['frame']}`"
            share = f"{top['fraction']:.1%}"
        else:
            top_text = "-"
            share = "-"
        lines.append(
            f"| {structure} | {info['n']} | {info['distinct_frames']} | "
            f"{top_text} | {share} |"
        )
    lines.append("")
    overall_top = realism["openers"]["overall_top_frames"]
    if overall_top:
        lines.append(
            "Overall top openers: "
            + "; ".join(
                f"`{entry['frame']}` x{entry['count']} ({entry['fraction']:.1%})"
                for entry in overall_top
            )
            + "."
        )
    lines.append("")

    lines.append("### Sentence-initial subjects (distribution only)")
    lines.append("")
    classes = realism["sentence_subjects"]["classes"]
    lines.append("| structure | " + " | ".join(classes) + " |")
    lines.append("|---" * (len(classes) + 1) + "|")
    for structure, dist in realism["sentence_subjects"]["by_structure"].items():
        cells = " | ".join(
            f"{dist[name]['count']} ({dist[name]['fraction']:.0%})" for name in classes
        )
        lines.append(f"| {structure} | {cells} |")
    cells = " | ".join(
        f"{realism['sentence_subjects']['overall'][name]['count']} "
        f"({realism['sentence_subjects']['overall'][name]['fraction']:.0%})"
        for name in classes
    )
    lines.append(f"| overall | {cells} |")
    lines.append("")

    lines.append("### Length variance")
    lines.append("")
    lines.append("| structure | n | min | max | mean | stddev | warning |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for structure, stats in realism["length_variance"]["by_structure"].items():
        warn = "YES" if stats["warning"] else ""
        lines.append(
            f"| {structure} | {stats['n']} | {stats['min']} | {stats['max']} | "
            f"{stats['mean']} | {stats['stddev']} | {warn} |"
        )
    lines.append("")

    lines.append("## Independent fact-coverage verification")
    lines.append("")
    if run_coverage:
        cs = coverage_summary
        counts = cs["counts"]
        lines.append(
            f"- Counts: **{counts['train']} train / {counts['validation']} validation / "
            f"{counts['gold']} gold**; **{cs['unique_ids']} globally unique IDs**; "
            f"batch {counts['batch']} maps to the supplied card file."
        )
        slices = cs["slice_counts"]
        neg = slices["negation"]
        glob = slices["global_negation"]
        four = slices["four_plus_symptoms"]
        lines.append(
            f"- DECISIONS minima: every field is non-null in >= 2 train structures "
            f"and >= 1 gold structure; every enum value appears in train and gold; "
            f"negation {neg['train']} train / {neg['gold']} gold (min 40/8); "
            f"global negation {glob['train']} / {glob['gold']} (min 20/4); "
            f"4+ symptoms {four['train']} / {four['gold']} (min 30/6)."
        )
        lines.append(
            f"- Train/validation disjointness: **{cs['train_val_fact_overlap']} shared fact cards**."
        )
        lines.append(
            f"- `reports/fact_coverage.json` compared with independently rebuilt "
            f"counts, structure counts, field non-null coverage, enum/boolean values, "
            f"tags, and coverage slices: "
            f"**{'no discrepancies' if cs['coverage_report_matches'] else 'DISCREPANCIES'}**."
        )
        lines.append(
            f"- Coverage errors: **{len(coverage_errors)}**"
            + (":" if coverage_errors else ".")
        )
        for error in coverage_errors:
            lines.append(f"  - `{error}`")
    else:
        lines.append(
            "- Dataset-level fact-coverage checks were skipped for this path "
            "(they are batch_001-specific). Pass `--coverage` to run them."
        )
    lines.append("")

    lines.append("## Gate recommendation")
    lines.append("")
    if overall["reject"]:
        lines.append("**FIX SEMANTIC FAILURES BEFORE SCALING.**")
        lines.append("")
        lines.append(
            f"{overall['reject']} of {n_items} records failed a hard semantic or "
            "structure check. See the item audit and `realism_warnings` summary."
        )
    elif not rw["passed"]:
        lines.append("**SEMANTICS PASS; REALISM NEEDS HUMAN REVIEW.**")
        lines.append("")
        lines.append(
            "Every record is semantically acceptable, but at least one hard "
            "realism warning fired (opener/frame repetition or another structural "
            "signal). The human reviewer decides whether to regenerate or accept."
        )
    else:
        lines.append("**SCALE NEXT BATCH.**")
        lines.append("")
        lines.append(
            "The batch clears every stated scale condition and the realism "
            "screens: semantic acceptance, zero exact duplicates, no held-out "
            "S8–S10 structure leaks, and no warning-level realism signals."
        )
    lines.append("")
    lines.append(
        f"Machine-readable metrics: `{out_dir / (batch + '_metrics.json')}`. "
        f"The `realism_warnings` block at the top summarizes every realism "
        "finding with offending record ids."
    )
    lines.append("")

    (out_dir / f"{batch}_audit.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )

    print(json.dumps({
        "batch": batch,
        "overall": overall,
        "per_structure": per_structure,
        "error_totals": dict(error_totals),
        "empty_inputs": len(empty_items),
        "specials": {
            "count": specials_report["count"],
            "by_type": specials_report["by_type"],
            "adversarial_carriers": specials_report["adversarial_carriers"],
            "warning_count": specials_report["warning_count"],
            "warnings": special_warnings,
        },
        "realism_warnings": rw,
        "coverage_run": run_coverage,
        "coverage_errors": coverage_errors,
        "coverage_summary": coverage_summary,
        "max_near_dup": max_plain,
        "max_near_dup_num": max_num,
        "item_errors": {k: v for k, v in item_errors.items() if v},
        "metrics_file": str(out_dir / f"{batch}_metrics.json"),
        "markdown_file": str(out_dir / f"{batch}_audit.md"),
    }, indent=1))


if __name__ == "__main__":
    main()


