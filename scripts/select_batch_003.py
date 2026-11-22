#!/usr/bin/env python3
"""Select batch_003 (25 ordinary + 15 train specials) and prove the 250-card
training set (batch_001 + batch_002 + batch_003) meets every coverage minimum.

Stdlib only, deterministic (explicit id list, no RNG). Does NOT modify
generate_facts.py, audit_batch_001.py, train.jsonl, validation.jsonl,
gold_cards.jsonl, DECISIONS.md or anything under data/text/.

Selection rationale (see reports/coverage_250.json -> selection_notes):
  * Hard gap at 210 was 4+ affirmed symptoms (18 < 30). Exactly 18 long cards
    remain unselected (3 each in S1,S2,S3,S4,S5,S7). We take 12 of them under
    the exact +4/+4/+4/+4/+3/+3/+3 split -> 18 + 12 = 30 (meets the minimum).
  * Both zero symptom/severity cells at 210 are filled: pelvic_pain/moderate
    (train_S2_048, the only pool carrier) and nausea/moderate (train_S4_034).
  * Thin cells recovered via longs: back_pain/severe, breast_tenderness/severe,
    headache/mild, mood_swings/mild, insomnia/severe, constipation/severe,
    cramps/null, fatigue/null, headache/null, diarrhea/mild.
  * Named weak slices: duration_ambiguity lifted in S1 (2->3) and S6 (1->2);
    emotional_language lifted in S7 (1->3), S1 (2->3), S5 (3->4).
  * Rare enums boosted: folate, magnesium, hair dry/oily, energy high,
    extremely_heavy, painkiller:false, blood_clots/null, sleep 3.75.
  * Density increments keep the ~45/45/9 band proportions: S1-S4 add 2 low +
    2 mid, S5/S7 add 1 low + 2 mid, S6 adds 3 one-fact cards. No 7-9 card is
    added, so the S1/S3 <=7 cap is trivially preserved (max selected = 5).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "data" / "facts"
REPORTS = ROOT / "reports"

STRUCTURES = [f"S{i}" for i in range(1, 8)]
FIELDS = [
    "cycle_day", "flow", "spotting", "symptoms", "denied", "no_symptoms_asserted",
    "painkiller", "supplements", "sleep_hours", "sleep_quality", "energy_level",
    "mood", "hair", "skin",
]
LIST_FIELDS = {"symptoms", "denied", "supplements"}
TAGS = [
    "implicit_dates", "negation", "hedging", "typos", "long_multi_symptom",
    "duration_ambiguity", "supplement_naming", "emotional_language",
    "empty_off_topic", "adversarial", "contradictory", "very_short",
]
ENUM_VALUES = {
    "flow": ["none", "light", "medium", "heavy", "extremely_heavy"],
    "sleep_quality": ["poor", "fair", "good"],
    "energy_level": ["low", "medium", "high"],
    "mood": ["low", "neutral", "good"],
    "hair": ["oily", "dry", "growth", "loss", "normal"],
    "skin": ["oily", "dry", "acne", "normal"],
    "supplements": ["iron", "vitamin_d", "magnesium", "b12", "folate", "calcium",
                    "omega_3", "probiotic", "other"],
    "symptom_name": ["cramps", "headache", "bloating", "back_pain", "nausea",
                     "fatigue", "breast_tenderness", "dizziness", "mood_swings",
                     "insomnia", "diarrhea", "constipation", "cravings",
                     "blood_clots", "pelvic_pain"],
    "symptom_severity": [None, "mild", "moderate", "severe"],
    "blood_clot_severity": [None, "light", "moderate", "large"],
}
LIST_DENSITY_CAP = 7
LIST_STRUCTURES = ("S1", "S3")

# --- The 25 ordinary batch_003 cards (Plan W). L = 4+ affirmed symptoms. ---
SELECTED_ORDINARY = {
    "S1": ["train_S1_034", "train_S1_042", "train_S1_045", "train_S1_038"],
    "S2": ["train_S2_034", "train_S2_042", "train_S2_048", "train_S2_055"],
    "S3": ["train_S3_034", "train_S3_042", "train_S3_050", "train_S3_035"],
    "S4": ["train_S4_034", "train_S4_042", "train_S4_050", "train_S4_035"],
    "S5": ["train_S5_042", "train_S5_052", "train_S5_044"],
    "S6": ["train_S6_045", "train_S6_047", "train_S6_048"],
    "S7": ["train_S7_034", "train_S7_038", "train_S7_044"],
}
EXPECTED_INCREMENT = {"S1": 4, "S2": 4, "S3": 4, "S4": 4, "S5": 3, "S6": 3, "S7": 3}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_lines(path: Path) -> dict[str, str]:
    """Map id -> original raw line, so copies are byte-verbatim."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out[json.loads(line)["id"]] = line
    return out


def non_null(record: dict, field: str) -> bool:
    value = record["facts"].get(field)
    return bool(value) if field in LIST_FIELDS else value is not None


def fact_count(record: dict) -> int:
    return sum(non_null(record, f) for f in FIELDS)


def density_band(n: int) -> str:
    if n == 1:
        return "1"
    if 2 <= n <= 3:
        return "2-3"
    if 4 <= n <= 6:
        return "4-6"
    if 7 <= n <= 9:
        return "7-9"
    return "other"


def symptom_count(record: dict) -> int:
    return len(record["facts"].get("symptoms") or [])


def enum_key(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def enum_occurrences(records: list[dict], category: str, value) -> int:
    count = 0
    for r in records:
        facts = r["facts"]
        if category in {"flow", "sleep_quality", "energy_level", "mood", "hair", "skin"}:
            count += facts.get(category) == value and value is not None
        elif category == "supplements":
            count += value in facts.get("supplements", [])
        elif category == "symptom_name":
            count += sum(s["name"] == value for s in facts.get("symptoms", []))
        elif category == "symptom_severity":
            count += sum(s["name"] != "blood_clots" and s["severity"] == value
                         for s in facts.get("symptoms", []))
        elif category == "blood_clot_severity":
            count += sum(s["name"] == "blood_clots" and s["severity"] == value
                         for s in facts.get("symptoms", []))
    return int(count)


def main() -> None:
    train = load_jsonl(FACTS / "train.jsonl")
    train_lines = load_lines(FACTS / "train.jsonl")
    b1 = load_jsonl(FACTS / "batch_001.jsonl")
    b2 = load_jsonl(FACTS / "batch_002.jsonl")
    train_by_id = {r["id"]: r for r in train}
    selected_ids = {r["id"] for r in b1 + b2}

    errors: list[str] = []
    checks: dict[str, dict] = {}

    def check(name: str, passed: bool, detail: dict) -> None:
        checks[name] = {"passed": bool(passed), **detail}
        if not passed:
            errors.append(name)

    # ---- assemble batch_003 ----
    ordinary_ids = [rid for s in STRUCTURES for rid in SELECTED_ORDINARY[s]]
    specials = [r for r in train if r["type"] != "ordinary"]
    special_ids = [r["id"] for r in specials]

    # uniqueness / disjointness
    check("batch_003_unique_ids", len(ordinary_ids + special_ids) == len(set(ordinary_ids + special_ids)),
          {"count": len(ordinary_ids + special_ids)})
    check("batch_003_disjoint_from_001_002", not (set(ordinary_ids + special_ids) & selected_ids),
          {"overlap": sorted(set(ordinary_ids + special_ids) & selected_ids)})
    check("batch_003_count_40", len(ordinary_ids) + len(special_ids) == 40,
          {"ordinary": len(ordinary_ids), "specials": len(special_ids)})
    check("batch_003_ordinary_25", len(ordinary_ids) == 25, {"count": len(ordinary_ids)})
    check("batch_003_specials_15", len(specials) == 15,
          {"by_type": dict(Counter(r["type"] for r in specials))})

    # all selected ids exist in train and are ordinary / correct structure
    for s in STRUCTURES:
        for rid in SELECTED_ORDINARY[s]:
            r = train_by_id.get(rid)
            if r is None:
                errors.append(f"{rid}: not in train.jsonl")
            elif r["type"] != "ordinary" or r["structure"] != s:
                errors.append(f"{rid}: wrong type/structure")
            elif rid in selected_ids:
                errors.append(f"{rid}: already selected in batch_001/002")

    # per-structure increment
    inc = {s: len(SELECTED_ORDINARY[s]) for s in STRUCTURES}
    check("per_structure_increment", inc == EXPECTED_INCREMENT,
          {"increment": inc, "expected": EXPECTED_INCREMENT})

    # 4+ symptom requirement on the 25
    long_ids = [rid for rid in ordinary_ids if symptom_count(train_by_id[rid]) >= 4]
    check("batch_003_long_multi_symptom_ge_12", len(long_ids) >= 12,
          {"count": len(long_ids), "minimum": 12, "ids": long_ids,
           "shortfall": max(0, 12 - len(long_ids))})

    # S1/S3 cap on selected (and on whole 250 later)
    cap_violations = [rid for rid in ordinary_ids
                      if train_by_id[rid]["structure"] in LIST_STRUCTURES
                      and fact_count(train_by_id[rid]) > LIST_DENSITY_CAP]
    check("batch_003_S1_S3_cap", not cap_violations,
          {"cap": LIST_DENSITY_CAP, "violations": cap_violations})

    # S6 single fact
    s6_bad = [rid for rid in SELECTED_ORDINARY["S6"] if fact_count(train_by_id[rid]) != 1]
    check("batch_003_S6_single_fact", not s6_bad, {"violations": s6_bad})

    # density increment bands
    inc_bands = {}
    for s in STRUCTURES:
        c = Counter(density_band(fact_count(train_by_id[rid])) for rid in SELECTED_ORDINARY[s])
        inc_bands[s] = {b: c.get(b, 0) for b in ("1", "2-3", "4-6", "7-9")}
    check("batch_003_no_high_band_added",
          all(inc_bands[s]["7-9"] == 0 for s in STRUCTURES if s != "S6"),
          {"increment_bands": inc_bands})

    # ---- write batch_003.jsonl (verbatim lines) ----
    ordered_ids = ordinary_ids + special_ids
    batch_path = FACTS / "batch_003.jsonl"
    batch_path.write_text("".join(train_lines[rid] + "\n" for rid in ordered_ids),
                          encoding="utf-8", newline="\n")
    b3 = load_jsonl(batch_path)
    # verify verbatim: re-parsed equals train record
    verbatim_ok = all(b3[i] == train_by_id[rid] for i, rid in enumerate(ordered_ids))
    check("batch_003_verbatim_copy", verbatim_ok, {"records": len(b3)})

    # ---- the 250 training set ----
    train250 = b1 + b2 + b3
    check("train250_count", len(train250) == 250, {"count": len(train250)})
    check("train250_unique_ids", len({r["id"] for r in train250}) == 250,
          {"unique": len({r["id"] for r in train250})})

    ordinary250 = [r for r in train250 if r["type"] == "ordinary"]
    per_struct = {s: sum(r["structure"] == s for r in ordinary250) for s in STRUCTURES}
    check("train250_per_structure_counts",
          per_struct == {"S1": 34, "S2": 34, "S3": 34, "S4": 34, "S5": 33, "S6": 33, "S7": 33},
          {"counts": per_struct})

    # ---- coverage report ----
    report: dict = {
        "dataset": "batch_001 + batch_002 + batch_003 (active 250 train)",
        "source_superset": "data/facts/train.jsonl (400, unchanged)",
        "record_counts": {
            "total": len(train250),
            "by_batch": {"batch_001": len(b1), "batch_002": len(b2), "batch_003": len(b3)},
            "by_type": dict(sorted(Counter(r["type"] for r in train250).items())),
            "ordinary_by_structure": per_struct,
            "specials_by_type": dict(sorted(Counter(r["type"] for r in train250 if r["type"] != "ordinary").items())),
            "specials_by_carrier": dict(sorted(Counter(
                (r["structure"] or "none") for r in train250 if r["type"] != "ordinary").items())),
        },
        "density_bands": {},
        "field_non_null": {},
        "enum_values": {},
        "boolean_values": {},
        "tags": {},
        "coverage_slices": {},
        "checks": checks,
        "selection_notes": {
            "split": "exact +4/+4/+4/+4/+3/+3/+3 (no card moved between structures)",
            "long_cards_taken": len(long_ids),
            "long_cards_remaining_unselected": 18 - len(long_ids),
            "zero_cells_filled": ["pelvic_pain/moderate (train_S2_048)", "nausea/moderate (train_S4_034)"],
            "compromises": [],
        },
        "failures": [],
        "overall_passed": True,
    }

    # density bands per structure (final 250)
    for s in STRUCTURES:
        rs = [r for r in ordinary250 if r["structure"] == s]
        bc = Counter(density_band(fact_count(r)) for r in rs)
        fc = Counter(fact_count(r) for r in rs)
        bands = {b: bc.get(b, 0) for b in ("1", "2-3", "4-6", "7-9")}
        report["density_bands"][s] = {
            "records": len(rs),
            "bands": bands,
            "by_fact_count": {str(n): fc.get(n, 0) for n in range(1, 10)},
            "band_proportions": {b: round(bands[b] / len(rs), 4) for b in bands},
            "max_fact_count": max(fc) if fc else 0,
        }
    # cap + S6 checks over the whole 250
    cap250 = [r["id"] for r in ordinary250
              if r["structure"] in LIST_STRUCTURES and fact_count(r) > LIST_DENSITY_CAP]
    check("train250_S1_S3_cap_le_7", not cap250, {"cap": LIST_DENSITY_CAP, "violations": cap250})
    s6_250 = [r["id"] for r in ordinary250 if r["structure"] == "S6" and fact_count(r) != 1]
    check("train250_S6_single_fact", not s6_250, {"violations": s6_250})
    # proportion sanity: each non-S6 structure within ~0.10 of 25/55,25/55,5/55
    target = {"2-3": 25 / 55, "4-6": 25 / 55, "7-9": 5 / 55}
    prop_ok = True
    prop_detail = {}
    for s in STRUCTURES:
        if s == "S6":
            continue
        bp = report["density_bands"][s]["band_proportions"]
        dev = {b: round(abs(bp[b] - target[b]), 4) for b in target}
        prop_detail[s] = dev
        if any(d > 0.10 for d in dev.values()):
            prop_ok = False
    check("train250_density_proportions_rough", prop_ok,
          {"target": {k: round(v, 4) for k, v in target.items()}, "abs_deviation": prop_detail})

    # field non-null structure counts (min >= 2 train structures)
    for f in FIELDS:
        by_s = Counter(r["structure"] for r in train250 if r["structure"] and non_null(r, f))
        sc = len([s for s in STRUCTURES if by_s.get(s, 0)])
        report["field_non_null"][f] = {
            "count": sum(non_null(r, f) for r in train250),
            "by_structure": {s: by_s.get(s, 0) for s in STRUCTURES},
            "structure_count": sc,
            "minimum_structures": 2,
            "passed": sc >= 2,
            "shortfall": max(0, 2 - sc),
        }
        check(f"field_{f}_ge_2_structures", sc >= 2,
              {"structure_count": sc, "minimum": 2, "shortfall": max(0, 2 - sc)})

    # enum values train counts (presence minimum >= 1)
    for category, values in ENUM_VALUES.items():
        report["enum_values"][category] = {}
        for v in values:
            n = enum_occurrences(train250, category, v)
            report["enum_values"][category][enum_key(v)] = {
                "train_count": n, "minimum": 1, "passed": n >= 1, "shortfall": max(0, 1 - n),
            }
            check(f"enum_{category}_{enum_key(v)}_present", n >= 1,
                  {"train_count": n, "minimum": 1, "shortfall": max(0, 1 - n)})
    # forced rare values presence
    for label, cat, val in [("extremely_heavy", "flow", "extremely_heavy"),
                            ("severe", "symptom_severity", "severe"),
                            ("painkiller_false", "painkiller", False)]:
        if cat == "painkiller":
            n = sum(r["facts"].get("painkiller") is False for r in train250)
        else:
            n = enum_occurrences(train250, cat, val)
        check(f"forced_rare_{label}_present", n >= 1, {"train_count": n, "minimum": 1})

    # boolean values
    for f in ("painkiller", "spotting", "no_symptoms_asserted"):
        vals = (True, False) if f != "no_symptoms_asserted" else (True,)
        report["boolean_values"][f] = {
            enum_key(v): {"train_count": sum(r["facts"].get(f) is v for r in train250)} for v in vals
        }

    # tags with >= 2 applicable structures check
    for t in TAGS:
        tagged = [r for r in train250 if t in r["tags"]]
        by_s = Counter(r["structure"] for r in tagged if r["structure"])
        applicable = sorted(s for s in STRUCTURES if by_s.get(s, 0))
        entry = {
            "count": len(tagged),
            "by_structure": {s: by_s.get(s, 0) for s in STRUCTURES},
            "applicable_structures": applicable,
            "structure_count": len(applicable),
        }
        if t == "empty_off_topic":
            # no carrier structure; requirement is presence among train specials
            entry["minimum_structures"] = 0
            entry["check"] = "present_in_train_specials (no carrier structure)"
            entry["passed"] = len(tagged) > 0
            entry["shortfall"] = 0 if len(tagged) > 0 else 1
            check("tag_empty_off_topic_present", len(tagged) > 0, {"count": len(tagged)})
        elif t == "contradictory":
            # S9-only (held-out gold); not applicable to train S1-S7
            entry["minimum_structures"] = 0
            entry["check"] = "not_applicable_in_train (S9/gold-only tag)"
            entry["passed"] = True
            entry["shortfall"] = 0
            check("tag_contradictory_not_applicable_in_train", True,
                  {"count": len(tagged), "note": "S9/gold-only; train has no S9"})
        else:
            entry["minimum_structures"] = 2
            entry["check"] = ">=2 applicable train structures"
            entry["passed"] = len(applicable) >= 2
            entry["shortfall"] = max(0, 2 - len(applicable))
            check(f"tag_{t}_ge_2_structures", len(applicable) >= 2,
                  {"structure_count": len(applicable), "minimum": 2,
                   "shortfall": max(0, 2 - len(applicable))})
        report["tags"][t] = entry

    # three slices
    slices = {
        "negation": (lambda r: "negation" in r["tags"], 40),
        "global_negation": (lambda r: r["facts"].get("no_symptoms_asserted") is True, 20),
        "four_plus_symptoms": (lambda r: symptom_count(r) >= 4, 30),
    }
    for name, (pred, minimum) in slices.items():
        n = sum(pred(r) for r in train250)
        by_s = Counter(r["structure"] for r in train250 if r["structure"] and pred(r))
        report["coverage_slices"][name] = {
            "train_count": n, "minimum": minimum, "passed": n >= minimum,
            "shortfall": max(0, minimum - n),
            "by_structure": {s: by_s.get(s, 0) for s in STRUCTURES},
        }
        check(f"slice_{name}_ge_{minimum}", n >= minimum,
              {"train_count": n, "minimum": minimum, "shortfall": max(0, minimum - n)})

    # informational slices (no minimum): hedging, typos, long_multi_symptom tag
    for name, pred in [("hedging", lambda r: "hedging" in r["tags"]),
                       ("typos", lambda r: "typos" in r["tags"]),
                       ("long_multi_symptom_tag", lambda r: "long_multi_symptom" in r["tags"]),
                       ("duration_ambiguity", lambda r: "duration_ambiguity" in r["tags"]),
                       ("emotional_language", lambda r: "emotional_language" in r["tags"])]:
        n = sum(pred(r) for r in train250)
        by_s = Counter(r["structure"] for r in train250 if r["structure"] and pred(r))
        report["coverage_slices"][name] = {
            "train_count": n, "by_structure": {s: by_s.get(s, 0) for s in STRUCTURES},
            "indicative_only": True,
        }

    # symptom x severity matrix (informational, shows zero/thin cells closed)
    matrix = {}
    for nm in ENUM_VALUES["symptom_name"]:
        if nm == "blood_clots":
            continue
        row = {}
        for sev in [None, "mild", "moderate", "severe"]:
            row[enum_key(sev)] = sum(
                s["name"] == nm and s["severity"] == sev
                for r in train250 for s in r["facts"].get("symptoms", []))
        matrix[nm] = row
    report["symptom_severity_matrix"] = matrix

    # ---- finalize ----
    report["failures"] = [
        {"check": name, **{k: v for k, v in c.items() if k != "passed"}}
        for name, c in checks.items() if not c["passed"]
    ]
    report["overall_passed"] = not errors
    report["checks_passed"] = sum(c["passed"] for c in checks.values())
    report["checks_total"] = len(checks)

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "coverage_250.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")

    # ---- console summary ----
    print("batch_003 ordinary ids by structure (L = 4+ affirmed symptoms):")
    for s in STRUCTURES:
        marks = [f"{rid}{' (L)' if symptom_count(train_by_id[rid]) >= 4 else ''}"
                 for rid in SELECTED_ORDINARY[s]]
        print(f"  {s}: " + ", ".join(marks))
    print(f"\nlong cards in batch_003: {len(long_ids)} (need >=12)")
    print(f"train250 four_plus_symptoms: {report['coverage_slices']['four_plus_symptoms']['train_count']} (min 30)")
    print(f"train250 negation: {report['coverage_slices']['negation']['train_count']} (min 40)")
    print(f"train250 global_negation: {report['coverage_slices']['global_negation']['train_count']} (min 20)")
    print(f"\nchecks: {report['checks_passed']}/{report['checks_total']} passed")
    if errors:
        print("FAILURES:")
        for e in errors:
            print("  -", e)
    else:
        print("ALL CHECKS PASSED")
    print(f"\nwrote {batch_path}")
    print(f"wrote {REPORTS / 'coverage_250.json'}")


if __name__ == "__main__":
    main()
