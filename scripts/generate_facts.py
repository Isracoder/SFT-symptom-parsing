#!/usr/bin/env python3
"""Deterministically generate and validate schema-only fact cards."""

from __future__ import annotations

import json
import random
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

SEED = 20261122
ROOT = Path(__file__).resolve().parents[1]

TRAIN_STRUCTURES = [f"S{i}" for i in range(1, 8)]
GOLD_STRUCTURES = [f"S{i}" for i in range(8, 11)]
STRUCTURES = TRAIN_STRUCTURES + GOLD_STRUCTURES
SPLITS = ("train", "validation", "gold")

FIELDS = [
    "cycle_day",
    "flow",
    "spotting",
    "symptoms",
    "denied",
    "no_symptoms_asserted",
    "painkiller",
    "supplements",
    "sleep_hours",
    "sleep_quality",
    "energy_level",
    "mood",
    "hair",
    "skin",
]
LIST_FIELDS = {"symptoms", "denied", "supplements"}
FLOW = ["none", "light", "medium", "heavy", "extremely_heavy"]
SLEEP_QUALITY = ["poor", "fair", "good"]
ENERGY_LEVEL = ["low", "medium", "high"]
MOOD = ["low", "neutral", "good"]
HAIR = ["oily", "dry", "growth", "loss", "normal"]
SKIN = ["oily", "dry", "acne", "normal"]
SUPPLEMENTS = [
    "iron",
    "vitamin_d",
    "magnesium",
    "b12",
    "folate",
    "calcium",
    "omega_3",
    "probiotic",
    "other",
]
SYMPTOMS = [
    "cramps",
    "headache",
    "bloating",
    "back_pain",
    "nausea",
    "fatigue",
    "breast_tenderness",
    "dizziness",
    "mood_swings",
    "insomnia",
    "diarrhea",
    "constipation",
    "cravings",
    "blood_clots",
    "pelvic_pain",
]
SEVERITIES = [None, "mild", "moderate", "severe"]
CLOT_SEVERITIES = [None, "light", "moderate", "large"]
TAGS = [
    "implicit_dates",
    "negation",
    "hedging",
    "typos",
    "long_multi_symptom",
    "duration_ambiguity",
    "supplement_naming",
    "emotional_language",
    "empty_off_topic",
    "adversarial",
    "contradictory",
    "very_short",
]
TYPES = {"ordinary", "adversarial", "off_topic", "empty"}

STRUCTURE_CONSTRAINTS = {
    "S1": "Use only a comma-separated list; do not write a full sentence.",
    "S2": "Use two to four simple declarative sentences with no subordinate clause, contrast, correction, question, or command.",
    "S3": "Use only telegraphic label:value items; do not write full sentences.",
    "S4": "Use one spoken run-on joined with and/so and fillers, with no contrast, subordinate clause, correction, question, or command.",
    "S5": "Use broken-English simple clauses with no subordinate clause, contrast, correction, question, or command.",
    "S6": "Use one sparse fragment of two to six words expressing exactly one fact.",
    "S7": "Use one non-assertive question followed by simple assertions, with no command, subordinate clause, or contrast.",
    "S8": "Use a declarative containing a subordinate clause, with no correction, question, or command.",
    "S9": "Use an explicit correction or a coordinator contrast, with no subordinate clause, question, or command.",
    "S10": "Use an imperative or polite request, with no subordinate clause, correction, or question.",
}

ENUM_VALUES = {
    "flow": FLOW,
    "sleep_quality": SLEEP_QUALITY,
    "energy_level": ENERGY_LEVEL,
    "mood": MOOD,
    "hair": HAIR,
    "skin": SKIN,
    "supplements": SUPPLEMENTS,
    "symptom_name": SYMPTOMS,
    "symptom_severity": SEVERITIES,
    "blood_clot_severity": CLOT_SEVERITIES,
}

SPLIT_OFFSETS = {"train": 0, "validation": 1000, "gold": 0}

TRAIN_DENSITY_BLOCK = [2, 4, 3, 5, 2, 6, 3, 4, 2, 5]
TRAIN_HIGH_DENSITIES = [7, 8, 9, 7, 8]
VALIDATION_DENSITIES = [2, 4, 6, 3, 7]
GOLD_DENSITIES = [2, 4, 7, 3, 5, 8, 2, 6, 9, 3, 4, 7, 2, 5, 8, 3, 6, 9]

# List structures (S1 comma lists, S3 colon/telegraphic lists) are exempt from
# schema-dump realism warnings by definition, but their fact cards are capped at
# the list-structure density cap (DECISIONS.md, "Density and naturalness").
LIST_STRUCTURES = ("S1", "S3")
LIST_DENSITY_CAP = 7
LIST_DROP_ORDER = (
    "hair",
    "skin",
    "mood",
    "energy_level",
    "sleep_quality",
    "sleep_hours",
    "supplements",
    "flow",
    "spotting",
    "painkiller",
    "symptoms",
    "denied",
    "no_symptoms_asserted",
    "cycle_day",
)

FILL_FIELDS = [
    "symptoms",
    "flow",
    "sleep_hours",
    "mood",
    "painkiller",
    "supplements",
    "spotting",
    "denied",
    "energy_level",
    "sleep_quality",
    "hair",
    "skin",
]

FIELD_LABELS = {
    "cycle_day": "cycle day",
    "flow": "flow",
    "spotting": "spotting",
    "symptoms": "symptoms",
    "denied": "denials",
    "no_symptoms_asserted": "global no-symptom claim",
    "painkiller": "painkiller",
    "supplements": "supplements",
    "sleep_hours": "sleep hours",
    "sleep_quality": "sleep quality",
    "energy_level": "energy",
    "mood": "mood",
    "hair": "hair",
    "skin": "skin",
}

REGISTERS = [
    "terse note-like",
    "casual diary",
    "text-message",
    "spoken conversational",
    "matter-of-fact",
    "slightly flustered",
]

PUNCTUATION_OPTIONS = {
    "S1": [
        "commas only, with no terminal period",
        "lowercase comma fragments with one dash",
        "comma fragments with no colon or terminal punctuation",
    ],
    "S2": [
        "periods with varied sentence length",
        "periods and one short fragment",
        "periods with minimal capitalization",
    ],
    "S3": [
        "line breaks and colons only, with no sentence punctuation",
        "lowercase colons with one dash between items",
        "short colon items separated by line breaks",
    ],
    "S4": [
        "commas and dashes in one run-on",
        "commas and ellipses in one run-on",
        "so/and glue with one trailing dash",
    ],
    "S5": [
        "lowercase with minimal punctuation",
        "short clauses with periods and one missing article",
        "simple periods with inconsistent capitalization",
    ],
    "S6": [
        "no terminal punctuation",
        "lowercase with no punctuation",
        "one dash or no punctuation",
    ],
    "S7": [
        "one question mark followed by periods",
        "one question mark and a short unpunctuated tail",
        "question mark, then lowercase assertions with periods",
    ],
    "S8": [
        "one comma or dash around the subordinate clause",
        "a subordinate clause set off by a comma",
        "periods with one parenthetical-like dash",
    ],
    "S9": [
        "an em dash or ellipsis at the correction/contrast",
        "a comma before the coordinator and a period after",
        "an ellipsis before the replacement value",
    ],
    "S10": [
        "a period or no terminal punctuation after the request",
        "a colon before the requested facts",
        "one polite request followed by a short dash and facts",
    ],
}

OPENERS = {
    "S1": [
        "Start directly on the leading fact.",
        "Start with a brief time-of-day cue before the leading fact.",
        "Start with a one-word reaction before the leading fact.",
        "Start with a short state filler before the leading fact.",
    ],
    "S2": [
        "Open with a first-person sentence about the leading fact.",
        "Open with a short time-of-day sentence, then the leading fact.",
        "Open with a brief reaction sentence, then the leading fact.",
        "Open with a context sentence that adds no in-scope fact.",
    ],
    "S3": [
        "Start with the leading label:value pair and no narrative filler.",
        "Start with the shortest label:value pair, then the remaining items.",
        "Start with a time-of-day label if it adds no fact.",
        "Start with a lowercase label:value item and keep every line telegraphic.",
    ],
    "S4": [
        "Open mid-thought with a casual filler.",
        "Open with a spoken filler, then run the facts together.",
        "Open with a time-of-day aside before the run-on.",
        "Open with a short reaction and immediately continue the run-on.",
    ],
    "S5": [
        "Open with a simple subject-verb clause.",
        "Open with a short time word, then simple clauses.",
        "Open with a state clause before the remaining simple clauses.",
        "Open with a direct object-first clause.",
    ],
    "S6": [
        "Start directly on the single fact.",
        "Start with a short modifier before the single fact.",
        "Start with a lowercase fragment, not a sentence frame.",
        "Start with the most specific word in the fragment.",
    ],
    "S7": [
        "Vary the question frame with a yes/no question.",
        "Vary the question frame with a wh-question.",
        "Vary the question frame with a scale-seeking question.",
        "Vary the question frame with a brief clarification question.",
    ],
    "S8": [
        "Lead with the subordinate clause.",
        "Lead with the main clause, then attach the subordinate clause.",
        "Lead with a time context before the subordinate clause.",
        "Lead with a first-person state and place the subordinate clause mid-sentence.",
    ],
    "S9": [
        "Lead with the first half of the contrast.",
        "Lead with the corrected fact and place the correction marker after it.",
        "Lead with the discarded value, then correct it.",
        "Lead with a short contrast setup, then the coordinator.",
    ],
    "S10": [
        "Lead with the request verb.",
        "Lead with a brief polite lead-in, then the request.",
        "Lead with the requested output and keep the request imperative.",
        "Lead with a short context phrase, then the request.",
    ],
}


def enum_key(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def fact_signature(facts: dict[str, Any]) -> str:
    return json.dumps(facts, sort_keys=True, separators=(",", ":"))


def density_for(split: str, structure: str, index: int) -> int:
    if structure == "S6":
        return 1
    if split == "train":
        block, position = divmod(index, 11)
        if position == 2:
            return TRAIN_HIGH_DENSITIES[block]
        adjusted = position if position < 2 else position - 1
        return TRAIN_DENSITY_BLOCK[adjusted]
    if split == "validation":
        return VALIDATION_DENSITIES[index]
    if split == "gold":
        return GOLD_DENSITIES[index]
    raise ValueError(f"Unknown split/structure for density: {split}/{structure}")


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


def ordered_facts(values: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in FIELDS:
        value = values.get(field)
        if field in LIST_FIELDS:
            if value:
                result[field] = value
        elif value is not None:
            result[field] = value
    return result


def symptom_pool(rng: random.Random) -> list[str]:
    pool = list(SYMPTOMS)
    rng.shuffle(pool)
    return pool


def choose_fields(
    structure: str, k: int, target: int, rng: random.Random, attempt: int
) -> tuple[list[str], str]:
    global_card = k % 9 == 0
    long_card = not global_card and k % 8 == 1
    clot_card = not global_card and not long_card and k % 11 == 3
    supplement_card = (
        not global_card and not long_card and not clot_card and k % 6 == 4
    )
    cycle_card = (
        not global_card
        and not long_card
        and not clot_card
        and not supplement_card
        and k % 4 == 2
    )
    denied_card = not global_card and k % 5 == 2

    required: list[str] = []
    forbidden: set[str] = set()
    role = "regular"
    if global_card:
        role = "global"
        required = ["no_symptoms_asserted"]
        forbidden = {"symptoms", "denied"}
    elif long_card:
        role = "long"
        required = ["symptoms"]
    elif clot_card:
        role = "clot"
        required = ["symptoms", "flow"]
    elif supplement_card:
        role = "supplement"
        required = ["supplements"]
    elif cycle_card:
        role = "cycle"
        required = ["cycle_day", "flow"]
    elif denied_card:
        role = "denied"
        required = ["denied"]

    candidates = [field for field in FILL_FIELDS if field not in forbidden]
    rng.shuffle(candidates)
    shift = (k * 3 + STRUCTURES.index(structure) * 5 + attempt * 7) % len(candidates)
    candidates = candidates[shift:] + candidates[:shift]

    selected = list(required)
    for field in candidates:
        if len(selected) >= target:
            break
        if field not in selected:
            selected.append(field)
    if len(selected) != target:
        raise ValueError(f"Cannot select {target} fields for {structure} k={k}")
    return selected, role


def sparse_facts(structure: str, k: int, rng: random.Random) -> dict[str, Any]:
    sidx = STRUCTURES.index(structure)
    pool = symptom_pool(rng)
    kind = (k + sidx) % 12
    block = (k + sidx) // 12
    values: dict[str, Any] = {}

    if kind == 0:
        values["flow"] = FLOW[block % len(FLOW)]
    elif kind == 1:
        name = next(name for name in pool if name != "blood_clots")
        if name == "cravings":
            severity = None
        else:
            severity = SEVERITIES[block % len(SEVERITIES)]
        values["symptoms"] = [{"name": name, "severity": severity}]
    elif kind == 2:
        values["denied"] = [pool[block % len(pool)]]
    elif kind == 3:
        values["painkiller"] = bool(block % 2)
    elif kind == 4:
        values["supplements"] = [SUPPLEMENTS[block % len(SUPPLEMENTS)]]
    elif kind == 5:
        values["sleep_hours"] = 3.5 + (k % 40) * 0.25
    elif kind == 6:
        values["sleep_quality"] = SLEEP_QUALITY[block % len(SLEEP_QUALITY)]
    elif kind == 7:
        values["energy_level"] = ENERGY_LEVEL[block % len(ENERGY_LEVEL)]
    elif kind == 8:
        values["mood"] = MOOD[block % len(MOOD)]
    elif kind == 9:
        values["hair"] = HAIR[block % len(HAIR)]
    elif kind == 10:
        values["skin"] = SKIN[block % len(SKIN)]
    else:
        values["no_symptoms_asserted"] = True
    return ordered_facts(values)


def dense_facts(
    structure: str,
    k: int,
    target: int,
    rng: random.Random,
    attempt: int,
) -> tuple[dict[str, Any], list[str], str]:
    sidx = STRUCTURES.index(structure)
    fields, role = choose_fields(structure, k, target, rng, attempt)
    pool = symptom_pool(rng)
    values: dict[str, Any] = {}
    affirmed: list[str] = []

    def regular_names(count: int) -> list[str]:
        names: list[str] = []
        start = (k * 3 + sidx * 5 + attempt * 2) % len(pool)
        cursor = 0
        while len(names) < count:
            name = pool[(start + cursor) % len(pool)]
            cursor += 1
            if name == "blood_clots" or name in names:
                continue
            names.append(name)
        return names

    if "symptoms" in fields:
        if role == "clot":
            names = ["blood_clots"]
            if (k + sidx) % 2 == 0:
                names.extend(regular_names(1))
        elif role == "long":
            names = regular_names(4)
        else:
            names = regular_names(1 + (k + sidx) % 3)
        for j, name in enumerate(names):
            if name == "cravings":
                severity = None
            elif name == "blood_clots":
                severity = CLOT_SEVERITIES[(k + sidx) % len(CLOT_SEVERITIES)]
            else:
                severity = SEVERITIES[(k + 2 * j + sidx) % len(SEVERITIES)]
            values.setdefault("symptoms", []).append(
                {"name": name, "severity": severity}
            )
            affirmed.append(name)

    if "flow" in fields:
        if role == "clot":
            values["flow"] = "medium"
        elif role == "cycle":
            values["flow"] = ["light", "medium", "heavy", "extremely_heavy"][
                (k + sidx) % 4
            ]
        else:
            values["flow"] = FLOW[(k + sidx) % len(FLOW)]

    if "cycle_day" in fields:
        values["cycle_day"] = 1 + (k * 3 + sidx) % 20

    if "spotting" in fields:
        values["spotting"] = bool((k + sidx) % 2)

    if "denied" in fields:
        available = [name for name in pool if name not in affirmed]
        start = (k * 2 + sidx + attempt) % len(available)
        count = 1 + k % 2
        values["denied"] = [
            available[(start + j) % len(available)] for j in range(count)
        ]

    if "no_symptoms_asserted" in fields:
        values["no_symptoms_asserted"] = True

    if "painkiller" in fields:
        values["painkiller"] = (k + sidx) % 3 != 0

    if "supplements" in fields:
        primary = SUPPLEMENTS[(k + 2 * sidx) % len(SUPPLEMENTS)]
        supplements = [primary]
        if (k + sidx) % 5 == 0:
            second = SUPPLEMENTS[
                (SUPPLEMENTS.index(primary) + 1) % len(SUPPLEMENTS)
            ]
            if second not in supplements:
                supplements.append(second)
        values["supplements"] = supplements

    if "sleep_hours" in fields:
        sleep_options = [4.0, 5.5, 6.0, 6.75, 7.0, 8.5, 9.0, 3.75]
        values["sleep_hours"] = sleep_options[(k + sidx + attempt) % len(sleep_options)]

    if "sleep_quality" in fields:
        values["sleep_quality"] = SLEEP_QUALITY[(k + sidx) % len(SLEEP_QUALITY)]
    if "energy_level" in fields:
        values["energy_level"] = ENERGY_LEVEL[(k + 2 * sidx) % len(ENERGY_LEVEL)]
    if "mood" in fields:
        values["mood"] = MOOD[(k + 3 * sidx) % len(MOOD)]
    if "hair" in fields:
        values["hair"] = HAIR[(k + sidx) % len(HAIR)]
    if "skin" in fields:
        values["skin"] = SKIN[(k + 2 * sidx) % len(SKIN)]

    facts = ordered_facts(values)
    if len(facts) != target:
        raise ValueError(
            f"Density mismatch for {structure} k={k}: {len(facts)} != {target}"
        )
    return facts, fields, role


def has_negation(facts: dict[str, Any]) -> bool:
    return bool(
        facts.get("denied")
        or facts.get("no_symptoms_asserted") is True
        or facts.get("painkiller") is False
        or facts.get("spotting") is False
    )


def top_level_fact_count(facts: dict[str, Any]) -> int:
    """Count non-null top-level facts: not null, not [], not {}."""
    count = 0
    for field in FIELDS:
        value = facts.get(field)
        if value is None or value == [] or value == {}:
            continue
        count += 1
    return count


def effective_list_density(split: str, structure: str, index: int) -> int:
    """Expected density after the S1/S3 list-structure cap is applied.

    Sampling still proposes the raw density band; list structures are capped at
    LIST_DENSITY_CAP, so an S1/S3 high-band proposal may land on the cap instead
    of above it.
    """
    expected = density_for(split, structure, index)
    if structure in LIST_STRUCTURES:
        return min(expected, LIST_DENSITY_CAP)
    return expected


def rewrite_fact_order_constraint(constraint: str, dropped_labels: set[str]) -> str:
    """Rewrite a "Fact order:" constraint so it no longer names dropped facts."""
    body = constraint.strip()
    mirror = "Do not mirror schema order."
    if body.endswith(mirror):
        body = body[: -len(mirror)]
    body = body.strip().rstrip().rstrip(".").rstrip()
    prefix = "Fact order:"
    if body.lower().startswith(prefix.lower()):
        body = body[len(prefix) :].strip()
        body = body.rstrip().rstrip(".").rstrip()
    if "; then mention " in body:
        lead, mention = body.split("; then mention ", 1)
        lead_label = lead.strip()
        if lead_label.lower().startswith("lead with"):
            lead_label = lead_label[len("lead with") :].strip().rstrip(";").strip()
        labels = [lead_label] + [part.strip() for part in mention.split(",") if part.strip()]
    elif body.lower().startswith("state only"):
        labels = [body[len("state only") :].strip().rstrip(".").strip()]
    else:
        labels = [body.strip().rstrip(".").strip()]
    kept_labels = [label for label in labels if label and label not in dropped_labels]
    if len(kept_labels) == 1:
        return f"Fact order: state only {kept_labels[0]}."
    return (
        f"Fact order: lead with {kept_labels[0]}; then mention "
        + ", ".join(kept_labels[1:])
        + ". Do not mirror schema order."
    )


TAG_CONSTRAINT_HINTS: tuple[tuple[str | None, str], ...] = (
    ("implicit_dates", "Express cycle_day through relative period-start wording"),
    ("negation", "Include an explicit global no-symptoms claim"),
    ("negation", "Express every denied symptom as a current explicit denial"),
    ("negation", "State explicitly that no painkiller was taken"),
    ("negation", "State explicitly that spotting is absent"),
    ("hedging", "Hedge one affirmed fact with about/maybe/roughly"),
    ("typos", "Include one or two realistic surface typos"),
    ("long_multi_symptom", "Include at least four affirmed symptoms"),
    ("duration_ambiguity", "Add an ambiguous duration to a current symptom"),
    ("supplement_naming", "Use natural supplement wording"),
    ("emotional_language", "Use emotional wording for the mood or fatigue"),
    ("contradictory", "Use an explicit same-slot self-correction"),
    ("very_short", "Keep the entire item to two to six words"),
)


def trim_list_structure_card(record: dict[str, Any]) -> bool:
    """Post-sampling trim enforcing the S1/S3 list-structure density cap.

    S1 and S3 are list-like by definition, so auditors exempt them from
    schema-dump realism warnings; to keep those cards plausible as quick notes,
    their fact cards are capped at LIST_DENSITY_CAP non-null top-level facts.

    This runs after all sampling is complete and only drops surplus facts, so
    sampling probabilities, RNG call order and the seed are untouched. Facts that
    required by the card's own tags/constraints (global negation, clotting
    context, 4+ symptom floors, explicit denials) are never dropped.
    """
    if record.get("type") != "ordinary" or record.get("structure") not in LIST_STRUCTURES:
        return False
    facts = record.get("facts") or {}
    if top_level_fact_count(facts) <= LIST_DENSITY_CAP:
        return False

    tags = list(record.get("tags") or [])
    keep: set[str] = set()
    symptoms = facts.get("symptoms") or []
    if any(isinstance(s, dict) and s.get("name") == "blood_clots" for s in symptoms):
        keep.add("flow")
    if facts.get("no_symptoms_asserted") is True:
        keep.add("no_symptoms_asserted")
    if "long_multi_symptom" in tags and len(symptoms) >= 4:
        keep.add("symptoms")
    if "negation" in tags:
        for field in ("denied", "no_symptoms_asserted", "painkiller", "spotting"):
            if facts.get(field):
                keep.add(field)

    dropped: set[str] = set()
    for field in LIST_DROP_ORDER:
        if top_level_fact_count(facts) <= LIST_DENSITY_CAP:
            break
        if field in keep or field not in facts:
            continue
        candidate = {k: v for k, v in facts.items() if k != field}
        candidate_symptoms = candidate.get("symptoms") or []
        long_ok = not (
            "long_multi_symptom" in tags and len(candidate_symptoms) >= 4
        )
        bleeding_ok = not (
            candidate.get("no_symptoms_asserted") is True
            or any(
                isinstance(s, dict) and s.get("name") == "blood_clots"
                for s in candidate_symptoms
            )
        )
        negation_ok = not ("negation" in tags and not has_negation(candidate))
        if not (long_ok and bleeding_ok and negation_ok):
            continue
        facts = candidate
        dropped.add(field)

    trimmed = ordered_facts(facts)
    if top_level_fact_count(trimmed) > LIST_DENSITY_CAP:
        raise ValueError(
            f"{record.get('id')}: cannot trim to the {LIST_DENSITY_CAP} fact cap"
        )
    if not dropped:
        return False

    record["facts"] = trimmed
    new_tags = list(tags)
    if "long_multi_symptom" in new_tags and len(trimmed.get("symptoms") or []) < 4:
        new_tags.remove("long_multi_symptom")
    if "supplement_naming" in new_tags and not trimmed.get("supplements"):
        new_tags.remove("supplement_naming")
    if "negation" in new_tags and not has_negation(trimmed):
        new_tags.remove("negation")
    record["tags"] = new_tags

    dropped_labels = {FIELD_LABELS[f] for f in dropped if f in FIELD_LABELS}
    pruned: list[str] = []
    for constraint in record.get("constraints") or []:
        if constraint.startswith("Fact order:"):
            pruned.append(rewrite_fact_order_constraint(constraint, dropped_labels))
            continue
        skip = False
        for tag, hint in TAG_CONSTRAINT_HINTS:
            if tag is not None and tag not in new_tags and hint in constraint:
                skip = True
        if (
            not skip
            and "Express sleep_hours as a range whose midpoint equals" in constraint
            and trimmed.get("sleep_hours") is None
        ):
            skip = True
        if (
            not skip
            and "Do not attach a severity cue to cravings" in constraint
            and not (trimmed.get("symptoms") or [])
        ):
            skip = True
        if (
            not skip
            and "Keep blood_clots on its separate clot scale" in constraint
            and not any(
                isinstance(s, dict) and s.get("name") == "blood_clots"
                for s in trimmed.get("symptoms") or []
            )
        ):
            skip = True
        if not skip:
            pruned.append(constraint)
    record["constraints"] = pruned
    return True


def ordinary_constraints(
    structure: str,
    facts: dict[str, Any],
    tags: list[str],
    sparse: bool,
    fields: list[str],
    k: int,
    attempt: int,
) -> list[str]:
    sidx = STRUCTURES.index(structure)
    constraints = [
        STRUCTURE_CONSTRAINTS[structure],
        "Express all and only the supplied facts; do not add current in-scope assertions.",
    ]
    lead = (k * 2 + sidx * 3 + attempt) % len(fields)
    ordered_fields = fields[lead:] + fields[:lead]
    ordered_labels = [FIELD_LABELS[field] for field in ordered_fields]
    if len(ordered_labels) == 1:
        order_text = f"Fact order: state only {ordered_labels[0]}."
    else:
        order_text = (
            f"Fact order: lead with {ordered_labels[0]}; then mention "
            + ", ".join(ordered_labels[1:])
            + ". Do not mirror schema order."
        )
    constraints.append(order_text)

    opener = OPENERS[structure][(k + sidx + attempt * 3) % len(OPENERS[structure])]
    constraints.append(
        f"Opener: {opener} Use a different opening frame from the preceding item."
    )
    register = REGISTERS[(k * 2 + sidx + attempt) % len(REGISTERS)]
    punctuation = PUNCTUATION_OPTIONS[structure][
        (k + sidx * 2 + attempt) % len(PUNCTUATION_OPTIONS[structure])
    ]
    constraints.append(
        f"Register/punctuation: use a {register} register; punctuate with {punctuation}."
    )
    if "implicit_dates" in tags:
        constraints.append(
            "Express cycle_day through relative period-start wording, counting the first bleeding day as day 1; do not use a calendar date."
        )
    if "negation" in tags:
        if facts.get("no_symptoms_asserted") is True:
            constraints.append(
                "Include an explicit global no-symptoms claim and do not affirm or separately deny any symptom."
            )
        if facts.get("denied"):
            constraints.append(
                "Express every denied symptom as a current explicit denial or cessation, without affirming it elsewhere."
            )
        if facts.get("painkiller") is False:
            constraints.append("State explicitly that no painkiller was taken.")
        if facts.get("spotting") is False:
            constraints.append("State explicitly that spotting is absent.")
    if "hedging" in tags:
        constraints.append(
            "Hedge one affirmed fact with about/maybe/roughly wording without changing its value or weakening any denial."
        )
    if "typos" in tags:
        constraints.append(
            "Include one or two realistic surface typos while keeping every in-scope fact recoverable."
        )
    if "long_multi_symptom" in tags:
        constraints.append(
            "Include at least four affirmed symptoms and preserve each symptom's severity band exactly."
        )
    if "duration_ambiguity" in tags:
        constraints.append(
            "Add an ambiguous duration to a current symptom or sleep reference without asserting a cycle day or changing the label."
        )
    if "supplement_naming" in tags:
        constraints.append(
            "Use natural supplement wording and preserve every listed supplement, including other when present; absence is not a skipped dose."
        )
    if "emotional_language" in tags:
        constraints.append(
            "Use emotional wording for the mood or fatigue fact without adding another in-scope state."
        )
    if "contradictory" in tags:
        constraints.append(
            "Use an explicit same-slot self-correction; the later value must be the supplied fact and the earlier value must be discarded."
        )
    elif structure == "S9":
        constraints.append(
            "Use a coordinator contrast between different dimensions, not incompatible values in one slot."
        )
    if "very_short" in tags:
        if structure == "S6":
            constraints.append(
                "Keep the entire item to two to six words and exactly one asserted fact."
            )
        else:
            constraints.append(
                "Keep the entire item to two to six words using only the supplied telegraphic label:value items."
            )
    if not sparse and facts.get("sleep_hours") is not None:
        hours = facts["sleep_hours"]
        if float(hours) != int(hours):
            constraints.append(
                "Express sleep_hours as a range whose midpoint equals the supplied value."
            )
    if any(s["name"] == "cravings" for s in facts.get("symptoms", [])):
        constraints.append("Do not attach a severity cue to cravings.")
    if any(s["name"] == "blood_clots" for s in facts.get("symptoms", [])):
        constraints.append(
            "Keep blood_clots on its separate clot scale and retain medium menstrual flow."
        )
    return constraints


def make_ordinary(
    split: str,
    structure: str,
    index: int,
    rng: random.Random,
    attempt: int = 0,
) -> dict[str, Any]:
    k = SPLIT_OFFSETS[split] + index + attempt * 13
    target = density_for(split, structure, index)
    sparse = structure == "S6"
    if sparse:
        facts = sparse_facts(structure, k, rng)
        fields = list(facts)
        role = "sparse"
    else:
        facts, fields, role = dense_facts(structure, k, target, rng, attempt)
    if len(facts) != target:
        raise ValueError(f"Wrong density for {split}/{structure}/{index}")

    selected: set[str] = set()
    if facts.get("cycle_day") is not None:
        selected.add("implicit_dates")
    if has_negation(facts):
        selected.add("negation")
    hedgeable = bool(facts.get("symptoms")) or any(
        facts.get(field) is not None
        for field in (
            "cycle_day",
            "flow",
            "sleep_hours",
            "sleep_quality",
            "energy_level",
            "mood",
            "hair",
            "skin",
        )
    )
    if k % 7 == 3 and hedgeable:
        selected.add("hedging")
    if k % 8 == 2:
        selected.add("typos")
    if len(facts.get("symptoms", [])) >= 4:
        selected.add("long_multi_symptom")
    if k % 10 == 4 and (
        facts.get("symptoms")
        or facts.get("sleep_hours") is not None
        or facts.get("sleep_quality") is not None
    ):
        selected.add("duration_ambiguity")
    if facts.get("supplements"):
        selected.add("supplement_naming")
    if k % 6 == 1 and (
        facts.get("mood") is not None
        or any(s["name"] == "fatigue" for s in facts.get("symptoms", []))
    ):
        selected.add("emotional_language")
    if structure == "S9" and not sparse and k % 3 == 0:
        selected.add("contradictory")
    very_short_s3 = (
        structure == "S3"
        and len(facts) == 2
        and "cycle_day" not in facts
        and all(
            len(facts.get(field, [])) <= 1
            for field in ("symptoms", "denied", "supplements")
        )
    )
    if sparse or very_short_s3:
        selected.add("very_short")

    tags = [tag for tag in TAGS if tag in selected]
    return {
        "id": f"{split}_{structure}_{index + 1:03d}",
        "split": split,
        "structure": structure,
        "type": "ordinary",
        "tags": tags,
        "facts": facts,
        "constraints": ordinary_constraints(
            structure, facts, tags, sparse, fields, k, attempt
        ),
    }


def make_specials(split: str) -> list[dict[str, Any]]:
    counts = {"adversarial": 5, "off_topic": 5, "empty": 5} if split == "train" else {
        "adversarial": 2,
        "off_topic": 2,
        "empty": 2,
    }
    records: list[dict[str, Any]] = []
    for special_type in ("adversarial", "off_topic", "empty"):
        for i in range(counts[special_type]):
            if special_type == "adversarial":
                structure = ("S1" if i % 2 == 0 else "S2") if split == "train" else "S8"
                tags = ["adversarial"]
                constraints = [
                    f"Keep the benign carrier portion in {structure} form: {STRUCTURE_CONSTRAINTS[structure]}",
                    "Add instruction-injection noise outside the carrier portion asking for schema violation or extra keys.",
                    "Keep health mentions non-assertive, habitual, or about another person; make no current first-person in-scope assertion.",
                ]
            else:
                structure = None
                tags = ["empty_off_topic"]
                if special_type == "off_topic":
                    constraints = [
                        "Write only about an unrelated everyday topic and assert no in-scope health field."
                    ]
                else:
                    constraints = [
                        "Produce an empty input containing no characters other than optional whitespace."
                    ]
            records.append(
                {
                    "id": f"{split}_{special_type}_{i + 1:03d}",
                    "split": split,
                    "structure": structure,
                    "type": special_type,
                    "tags": tags,
                    "facts": {},
                    "constraints": constraints,
                }
            )
    return records


def generate() -> tuple[list[dict[str, Any]], ...]:
    rng = random.Random(SEED)
    train = [
        make_ordinary("train", structure, i, rng)
        for structure in TRAIN_STRUCTURES
        for i in range(55)
    ]
    train.extend(make_specials("train"))

    train_signatures = {fact_signature(r["facts"]) for r in train}
    validation: list[dict[str, Any]] = []
    validation_signatures: set[str] = set()
    for structure in TRAIN_STRUCTURES:
        for i in range(5):
            for attempt in range(1000):
                card = make_ordinary("validation", structure, i, rng, attempt)
                signature = fact_signature(card["facts"])
                if signature not in train_signatures and signature not in validation_signatures:
                    validation.append(card)
                    validation_signatures.add(signature)
                    break
            else:
                raise ValueError(f"Could not make validation card disjoint for {structure} index {i}")

    gold = [
        make_ordinary("gold", structure, i, rng)
        for structure in GOLD_STRUCTURES
        for i in range(18)
    ]
    gold.extend(make_specials("gold"))

    # Post-sampling trim: enforce the S1/S3 list-structure density cap now that
    # every card has been sampled, so sampling itself stays untouched.
    for record in (*train, *validation, *gold):
        trim_list_structure_card(record)

    batch = [
        deepcopy(card)
        for structure in TRAIN_STRUCTURES
        for card in [
            r
            for r in train
            if r["type"] == "ordinary" and r["structure"] == structure
        ][:10]
    ]
    return train, validation, gold, batch


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_record(record: dict[str, Any], expected_split: str, errors: list[str]) -> None:
    rid = record.get("id", "<missing>")
    require(
        set(record) == {"id", "split", "structure", "type", "tags", "facts", "constraints"},
        f"{rid}: wrong record keys",
        errors,
    )
    require(isinstance(rid, str) and bool(rid), f"{rid}: invalid ID", errors)
    require(record.get("split") == expected_split, f"{rid}: wrong split", errors)
    rtype = record.get("type")
    structure = record.get("structure")
    require(rtype in TYPES, f"{rid}: invalid type", errors)
    require(
        structure in STRUCTURES or (structure is None and rtype in {"off_topic", "empty"}),
        f"{rid}: invalid structure/carrier",
        errors,
    )
    tags = record.get("tags")
    require(
        isinstance(tags, list)
        and len(tags) == len(set(tags))
        and all(tag in TAGS for tag in tags),
        f"{rid}: invalid tags",
        errors,
    )
    constraints = record.get("constraints")
    require(
        isinstance(constraints, list)
        and bool(constraints)
        and all(isinstance(c, str) and c.strip() for c in constraints),
        f"{rid}: invalid constraints",
        errors,
    )
    facts = record.get("facts")
    require(isinstance(facts, dict), f"{rid}: facts is not an object", errors)
    if not isinstance(facts, dict):
        return
    require(set(facts) <= set(FIELDS), f"{rid}: unknown fact field", errors)

    if rtype == "ordinary":
        expected_structures = TRAIN_STRUCTURES if expected_split in {"train", "validation"} else GOLD_STRUCTURES
        require(structure in expected_structures, f"{rid}: ordinary card in wrong structure split", errors)
    else:
        require(facts == {}, f"{rid}: special card must have an empty partial fact object", errors)
        if rtype == "adversarial":
            expected_carriers = {"S1", "S2"} if expected_split == "train" else {"S8"}
            require(structure in expected_carriers, f"{rid}: wrong adversarial carrier", errors)
            require(tags == ["adversarial"], f"{rid}: adversarial tags", errors)
        else:
            require(structure is None, f"{rid}: special without carrier has a structure", errors)
            require(tags == ["empty_off_topic"], f"{rid}: empty/off-topic tags", errors)

    if "contradictory" in tags:
        require(structure == "S9", f"{rid}: contradictory tag outside S9", errors)
    if structure == "S6" and rtype == "ordinary":
        require(len(facts) == 1, f"{rid}: S6 must contain exactly one fact", errors)
        require("very_short" in tags, f"{rid}: S6 missing very_short", errors)
    if "very_short" in tags:
        require(
            structure in {"S3", "S6"},
            f"{rid}: very_short outside S3/S6",
            errors,
        )
    if rtype == "ordinary" and isinstance(constraints, list):
        for marker in ("Fact order:", "Opener:", "Register/punctuation:"):
            require(
                any(isinstance(c, str) and c.startswith(marker) for c in constraints),
                f"{rid}: missing naturalness constraint {marker}",
                errors,
            )

    scalar_enums = {
        "flow": FLOW,
        "sleep_quality": SLEEP_QUALITY,
        "energy_level": ENERGY_LEVEL,
        "mood": MOOD,
        "hair": HAIR,
        "skin": SKIN,
    }
    for field, allowed in scalar_enums.items():
        if field in facts:
            require(facts[field] is None or facts[field] in allowed, f"{rid}: invalid {field}", errors)
    if "cycle_day" in facts:
        value = facts["cycle_day"]
        require(
            value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 1),
            f"{rid}: invalid cycle_day",
            errors,
        )
        if value is not None:
            require(facts.get("flow") not in (None, "none"), f"{rid}: cycle day lacks implied bleeding flow", errors)
    for field in ("spotting", "painkiller"):
        if field in facts:
            require(facts[field] is None or isinstance(facts[field], bool), f"{rid}: invalid {field}", errors)
    if "no_symptoms_asserted" in facts:
        require(facts["no_symptoms_asserted"] in (None, True), f"{rid}: no_symptoms_asserted must be true/null", errors)
    if "sleep_hours" in facts:
        value = facts["sleep_hours"]
        require(
            value is None
            or (isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 24),
            f"{rid}: invalid sleep_hours",
            errors,
        )
    for field in LIST_FIELDS:
        if field in facts:
            require(isinstance(facts[field], list), f"{rid}: {field} must be a list", errors)

    symptoms = facts.get("symptoms", [])
    denied = facts.get("denied", [])
    supplements = facts.get("supplements", [])
    if not isinstance(symptoms, list) or not isinstance(denied, list) or not isinstance(supplements, list):
        return
    affirmed_names: list[str] = []
    for symptom in symptoms:
        require(
            isinstance(symptom, dict) and set(symptom) == {"name", "severity"},
            f"{rid}: malformed symptom",
            errors,
        )
        if not isinstance(symptom, dict):
            continue
        name = symptom.get("name")
        severity = symptom.get("severity")
        affirmed_names.append(name)
        require(name in SYMPTOMS and name not in {"acne", "other"}, f"{rid}: invalid symptom name", errors)
        if name == "blood_clots":
            require(severity in CLOT_SEVERITIES, f"{rid}: invalid blood_clots severity", errors)
        elif name == "cravings":
            require(severity is None, f"{rid}: cravings severity must be null", errors)
        else:
            require(severity in SEVERITIES, f"{rid}: invalid symptom severity", errors)
    require(len(affirmed_names) == len(set(affirmed_names)), f"{rid}: duplicate affirmed symptom", errors)
    require(
        all(isinstance(name, str) and name in SYMPTOMS and name not in {"acne", "other"} for name in denied),
        f"{rid}: invalid denied symptom",
        errors,
    )
    require(len(denied) == len(set(denied)), f"{rid}: duplicate denied symptom", errors)
    require(set(affirmed_names).isdisjoint(denied), f"{rid}: affirmed/denied overlap", errors)
    require(
        all(value in SUPPLEMENTS for value in supplements) and len(supplements) == len(set(supplements)),
        f"{rid}: invalid supplements",
        errors,
    )
    if facts.get("no_symptoms_asserted") is True:
        require(not symptoms and not denied, f"{rid}: global negation has symptoms/denials", errors)
    if "blood_clots" in affirmed_names:
        require(facts.get("flow") == "medium", f"{rid}: blood clots require medium flow", errors)
    require(("negation" in tags) == has_negation(facts), f"{rid}: negation tag mismatch", errors)
    require(
        ("long_multi_symptom" in tags) == (len(symptoms) >= 4),
        f"{rid}: long_multi_symptom tag mismatch",
        errors,
    )


def validate_counts(
    train: list[dict[str, Any]],
    validation: list[dict[str, Any]],
    gold: list[dict[str, Any]],
    batch: list[dict[str, Any]],
    errors: list[str],
) -> None:
    require(len(train) == 400, "train count is not 400", errors)
    require(len(validation) == 35, "validation count is not 35", errors)
    require(len(gold) == 60, "gold count is not 60", errors)
    require(len(batch) == 70, "batch count is not 70", errors)
    for structure in TRAIN_STRUCTURES:
        require(
            sum(r["type"] == "ordinary" and r["structure"] == structure for r in train) == 55,
            f"train {structure} count is not 55",
            errors,
        )
        require(
            sum(r["type"] == "ordinary" and r["structure"] == structure for r in validation) == 5,
            f"validation {structure} count is not 5",
            errors,
        )
    for structure in GOLD_STRUCTURES:
        require(
            sum(r["type"] == "ordinary" and r["structure"] == structure for r in gold) == 18,
            f"gold {structure} count is not 18",
            errors,
        )

    for records, split in (
        (train, "train"),
        (validation, "validation"),
        (gold, "gold"),
    ):
        for record in records:
            if record["type"] != "ordinary":
                continue
            index = int(record["id"].rsplit("_", 1)[1]) - 1
            expected = effective_list_density(split, record["structure"], index)
            require(
                len(record["facts"]) == expected,
                f"{record['id']}: density {len(record['facts'])} != {expected}",
                errors,
            )

    for structure in TRAIN_STRUCTURES:
        counts = Counter(
            density_band(len(r["facts"]))
            for r in train
            if r["type"] == "ordinary" and r["structure"] == structure
        )
        if structure == "S6":
            require(counts.get("1") == 55, "S6 must have 55 one-fact cards", errors)
        else:
            require(
                counts.get("2-3") == 25
                and counts.get("4-6") == 25
                and counts.get("7-9") == 5,
                f"train {structure}: wrong density bands {dict(counts)}",
                errors,
            )
        validation_counts = Counter(
            density_band(len(r["facts"]))
            for r in validation
            if r["structure"] == structure
        )
        if structure == "S6":
            require(
                validation_counts.get("1") == 5,
                "validation S6 must have five one-fact cards",
                errors,
            )
        else:
            require(
                validation_counts.get("2-3") == 2
                and validation_counts.get("4-6") == 2
                and validation_counts.get("7-9") == 1,
                f"validation {structure}: wrong density bands {dict(validation_counts)}",
                errors,
            )
    for structure in GOLD_STRUCTURES:
        counts = Counter(
            density_band(len(r["facts"]))
            for r in gold
            if r["type"] == "ordinary" and r["structure"] == structure
        )
        require(
            counts.get("2-3") == 6
            and counts.get("4-6") == 6
            and counts.get("7-9") == 6,
            f"gold {structure}: wrong density bands {dict(counts)}",
            errors,
        )

    for records, split in ((train, "train"), (gold, "gold")):
        expected_specials = 5 if split == "train" else 2
        for special_type in ("adversarial", "off_topic", "empty"):
            require(
                sum(r["type"] == special_type for r in records) == expected_specials,
                f"{split} {special_type} count mismatch",
                errors,
            )
    expected_batch = [
        card
        for structure in TRAIN_STRUCTURES
        for card in [r for r in train if r["type"] == "ordinary" and r["structure"] == structure][:10]
    ]
    require(batch == expected_batch, "batch is not the first 10 ordinary train cards per structure", errors)


def field_non_null(record: dict[str, Any], field: str) -> bool:
    value = record["facts"].get(field)
    if field in LIST_FIELDS:
        return bool(value)
    return value is not None


def enum_occurrences(records: list[dict[str, Any]], category: str, value: Any) -> int:
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


def validate_coverage(records_by_split: dict[str, list[dict[str, Any]]], errors: list[str]) -> None:
    for field in FIELDS:
        train_structures = {
            r["structure"]
            for r in records_by_split["train"]
            if r["structure"] is not None and field_non_null(r, field)
        }
        gold_structures = {
            r["structure"]
            for r in records_by_split["gold"]
            if r["structure"] is not None and field_non_null(r, field)
        }
        require(len(train_structures) >= 2, f"{field}: fewer than 2 train structures", errors)
        require(len(gold_structures) >= 1, f"{field}: missing non-null gold structure", errors)

    for category, values in ENUM_VALUES.items():
        for value in values:
            for split in ("train", "gold"):
                require(
                    enum_occurrences(records_by_split[split], category, value) > 0,
                    f"{category}={enum_key(value)} missing from {split}",
                    errors,
                )
    for field in ("painkiller", "spotting"):
        for value in (True, False):
            for split in ("train", "gold"):
                require(
                    any(r["facts"].get(field) is value for r in records_by_split[split]),
                    f"{field}={enum_key(value)} missing from {split}",
                    errors,
                )

    slices = {
        "negation": lambda r: "negation" in r["tags"],
        "global_negation": lambda r: r["facts"].get("no_symptoms_asserted") is True,
        "four_plus_symptoms": lambda r: len(r["facts"].get("symptoms", [])) >= 4,
    }
    minima = {
        "negation": (40, 8),
        "global_negation": (20, 4),
        "four_plus_symptoms": (30, 6),
    }
    for name, predicate in slices.items():
        train_min, gold_min = minima[name]
        require(sum(predicate(r) for r in records_by_split["train"]) >= train_min, f"{name}: train minimum failed", errors)
        require(sum(predicate(r) for r in records_by_split["gold"]) >= gold_min, f"{name}: gold minimum failed", errors)

    all_records = records_by_split["train"] + records_by_split["validation"] + records_by_split["gold"]
    for tag in TAGS:
        tagged = [r for r in all_records if tag in r["tags"]]
        require(bool(tagged), f"tag {tag} has no records", errors)
        if tag == "empty_off_topic":
            require(
                any(tag in r["tags"] for r in records_by_split["train"])
                and any(tag in r["tags"] for r in records_by_split["gold"]),
                "empty_off_topic missing from train/gold",
                errors,
            )
        elif tag == "contradictory":
            require(
                all(r["structure"] == "S9" for r in tagged)
                and any(r["split"] == "gold" for r in tagged),
                "contradictory must occur in gold S9 only",
                errors,
            )
        else:
            structures = {r["structure"] for r in tagged if r["structure"] is not None}
            require(len(structures) >= 2, f"tag {tag}: fewer than 2 applicable structures", errors)


def validate_naturalness(
    records_by_split: dict[str, list[dict[str, Any]]], errors: list[str]
) -> None:
    for split, records in records_by_split.items():
        for structure in STRUCTURES:
            ordinary = [
                r
                for r in records
                if r["type"] == "ordinary" and r["structure"] == structure
            ]
            if not ordinary:
                continue
            for marker in ("Fact order:", "Opener:", "Register/punctuation:"):
                variants = {
                    constraint
                    for record in ordinary
                    for constraint in record["constraints"]
                    if constraint.startswith(marker)
                }
                require(
                    len(variants) >= 3,
                    f"{split}/{structure}: fewer than 3 {marker} variants",
                    errors,
                )


def validate_all(
    train: list[dict[str, Any]],
    validation: list[dict[str, Any]],
    gold: list[dict[str, Any]],
    batch: list[dict[str, Any]],
) -> None:
    errors: list[str] = []
    records_by_split = {"train": train, "validation": validation, "gold": gold}
    validate_counts(train, validation, gold, batch, errors)
    for split, records in records_by_split.items():
        for record in records:
            validate_record(record, split, errors)
    for record in batch:
        validate_record(record, "train", errors)

    primary = train + validation + gold
    ids = [r["id"] for r in primary]
    require(len(ids) == len(set(ids)), "IDs are not globally unique across primary splits", errors)
    for name, records in (*records_by_split.items(), ("batch", batch)):
        file_ids = [r["id"] for r in records]
        require(len(file_ids) == len(set(file_ids)), f"{name}: duplicate IDs", errors)

    train_signatures = {fact_signature(r["facts"]) for r in train}
    overlap = [
        r["id"] for r in validation if fact_signature(r["facts"]) in train_signatures
    ]
    require(not overlap, f"validation facts overlap train: {overlap}", errors)
    validate_coverage(records_by_split, errors)
    validate_naturalness(records_by_split, errors)
    if errors:
        raise ValueError("Fact-card validation failed:\n" + "\n".join(f"- {e}" for e in errors))


def build_coverage(
    train: list[dict[str, Any]],
    validation: list[dict[str, Any]],
    gold: list[dict[str, Any]],
    batch: list[dict[str, Any]],
) -> dict[str, Any]:
    records_by_split = {"train": train, "validation": validation, "gold": gold}
    all_primary = train + validation + gold
    report: dict[str, Any] = {
        "seed": SEED,
        "record_counts": {
            "train": len(train),
            "validation": len(validation),
            "gold": len(gold),
            "batch_001": len(batch),
            "total_primary": len(all_primary),
        },
        "counts_by_split": {},
        "counts_by_structure": {},
        "field_non_null": {},
        "enum_values": {},
        "boolean_values": {},
        "tags": {},
        "coverage_slices": {},
        "density_histogram": {},
        "validation": {"status": "passed", "errors": []},
    }
    for split, records in records_by_split.items():
        type_counts = Counter(r["type"] for r in records)
        report["counts_by_split"][split] = {
            "total": len(records),
            "by_type": {key: type_counts.get(key, 0) for key in sorted(TYPES)},
        }
    for structure in STRUCTURES:
        report["counts_by_structure"][structure] = {}
        for split, records in records_by_split.items():
            matching = [r for r in records if r["structure"] == structure]
            report["counts_by_structure"][structure][split] = {
                "total": len(matching),
                "ordinary": sum(r["type"] == "ordinary" for r in matching),
                "adversarial": sum(r["type"] == "adversarial" for r in matching),
            }
    report["counts_by_structure"]["none"] = {
        split: {
            "total": sum(r["structure"] is None for r in records),
            "ordinary": 0,
            "adversarial": 0,
        }
        for split, records in records_by_split.items()
    }

    for split, records in records_by_split.items():
        report["density_histogram"][split] = {}
        for structure in STRUCTURES:
            ordinary = [
                r
                for r in records
                if r["type"] == "ordinary" and r["structure"] == structure
            ]
            if not ordinary:
                continue
            by_count = Counter(len(r["facts"]) for r in ordinary)
            by_band = Counter(density_band(len(r["facts"])) for r in ordinary)
            report["density_histogram"][split][structure] = {
                "records": len(ordinary),
                "by_fact_count": {
                    str(count): by_count.get(count, 0) for count in range(1, 10)
                },
                "bands": {
                    band: by_band.get(band, 0)
                    for band in ("1", "2-3", "4-6", "7-9")
                },
            }
    report["density_histogram"]["batch_001"] = {}
    for structure in TRAIN_STRUCTURES:
        ordinary = [
            r
            for r in batch
            if r["type"] == "ordinary" and r["structure"] == structure
        ]
        by_count = Counter(len(r["facts"]) for r in ordinary)
        by_band = Counter(density_band(len(r["facts"])) for r in ordinary)
        report["density_histogram"]["batch_001"][structure] = {
            "records": len(ordinary),
            "by_fact_count": {
                str(count): by_count.get(count, 0) for count in range(1, 10)
            },
            "bands": {
                band: by_band.get(band, 0)
                for band in ("1", "2-3", "4-6", "7-9")
            },
        }

    for field in FIELDS:
        field_report: dict[str, Any] = {}
        for split, records in records_by_split.items():
            by_structure = Counter(
                r["structure"] for r in records if r["structure"] is not None and field_non_null(r, field)
            )
            field_report[split] = {
                "count": sum(field_non_null(r, field) for r in records),
                "by_structure": {s: by_structure.get(s, 0) for s in STRUCTURES},
                "structure_count": len([s for s in STRUCTURES if by_structure.get(s, 0)]),
            }
        report["field_non_null"][field] = field_report

    for category, values in ENUM_VALUES.items():
        report["enum_values"][category] = {
            enum_key(value): {
                split: enum_occurrences(records, category, value)
                for split, records in records_by_split.items()
            }
            for value in values
        }
    for field in ("painkiller", "spotting", "no_symptoms_asserted"):
        values = (True, False) if field != "no_symptoms_asserted" else (True,)
        report["boolean_values"][field] = {
            enum_key(value): {
                split: sum(r["facts"].get(field) is value for r in records)
                for split, records in records_by_split.items()
            }
            for value in values
        }

    for tag in TAGS:
        tag_report: dict[str, Any] = {}
        for split, records in records_by_split.items():
            tagged = [r for r in records if tag in r["tags"]]
            structure_counts = Counter(r["structure"] for r in tagged if r["structure"] is not None)
            tag_report[split] = {
                "count": len(tagged),
                "by_structure": {s: structure_counts.get(s, 0) for s in STRUCTURES},
            }
        tag_report["applicable_structures"] = sorted(
            {r["structure"] for r in all_primary if tag in r["tags"] and r["structure"] is not None}
        )
        report["tags"][tag] = tag_report

    predicates = {
        "negation": lambda r: "negation" in r["tags"],
        "global_negation": lambda r: r["facts"].get("no_symptoms_asserted") is True,
        "four_plus_symptoms": lambda r: len(r["facts"].get("symptoms", [])) >= 4,
        "hedging": lambda r: "hedging" in r["tags"],
        "typos": lambda r: "typos" in r["tags"],
        "long_multi_symptom": lambda r: "long_multi_symptom" in r["tags"],
    }
    minima = {
        "negation": {"train": 40, "gold": 8},
        "global_negation": {"train": 20, "gold": 4},
        "four_plus_symptoms": {"train": 30, "gold": 6},
    }
    for name, predicate in predicates.items():
        report["coverage_slices"][name] = {
            split: sum(predicate(r) for r in records)
            for split, records in records_by_split.items()
        }
        if name in minima:
            report["coverage_slices"][name]["minimum"] = minima[name]
            report["coverage_slices"][name]["passed"] = all(
                report["coverage_slices"][name][split] >= minimum
                for split, minimum in minima[name].items()
            )
    return report


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    train, validation, gold, batch = generate()
    validate_all(train, validation, gold, batch)
    coverage = build_coverage(train, validation, gold, batch)

    write_jsonl(ROOT / "data" / "facts" / "train.jsonl", train)
    write_jsonl(ROOT / "data" / "facts" / "validation.jsonl", validation)
    write_jsonl(ROOT / "data" / "facts" / "gold_cards.jsonl", gold)
    write_jsonl(ROOT / "data" / "facts" / "batch_001.jsonl", batch)
    report_path = ROOT / "reports" / "fact_coverage.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(coverage, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "validation": "passed",
                "train": len(train),
                "validation_records": len(validation),
                "gold_cards": len(gold),
                "batch_001": len(batch),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
