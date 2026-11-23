# Gold changelog

Single canonical gold file: `data/text/gold_cards.jsonl` (60 records, labels + handwritten text).
Frozen SHA-256: `a67471793cc27a810b5092bc8d843cc04819c0a45dcf3adf05b90479906c317c` (2026-11-23).

Gold text was **handwritten by the project owner**, never LLM-generated or paraphrased. Gold is used only for final evaluation, never for training or model/checkpoint selection. Any further edit requires a new hash, an entry here, and a full re-run of all four evaluation cells.

## File layout decision
The earlier `data/facts/gold_cards.jsonl` was retired: the owner moved gold into `data/text/` and the single file now holds both labels and text. A separate card file is redundant, so nothing was restored. `reports/dataset_manifest.json` points at the canonical file.

## Intentional label decisions by the owner
- `sleep_quality` changed `fair` -> `poor` on `gold_S9_003`, `gold_S9_015`, `gold_S10_005`, because the owner judged `fair` inconsistent with the stated insomnia.
- `gold_S10_008`: an `insomnia` symptom was dropped from the label.
- **Convention recorded for the write-up:** when insomnia is reported, `poor` is considered a more defensible `sleep_quality` than `fair`. This is a soft convention, not a logical implication — the two fields are independent, and a model outputting `fair` beside insomnia is a *convention* mismatch, not a factual extraction error. Do not present it as a hard rule.

## Review and corrections (reports/gold_review.md)
Initial independent review: 24 MUST FIX, 11 WORTH A LOOK, 25 OK. Post-fix re-review: 22 resolved, 2 open; the final 2 (`gold_S9_017` missing S9 correction/contrast marker, `gold_S8_018` unsupported `nausea: moderate`) were then corrected and verified by the orchestrator (`actually` restored; `bad nausea` added).

Corrections made by the owner included: filling two empty texts (`gold_S8_009`, `gold_S10_018`); removing drug names (`ibuprofen` on `gold_S10_006`, `gold_S10_014`); resolving the denied-vs-affirmed breast tenderness contradiction on `gold_S8_003`; restoring S8 subordinate clauses and removing them from S9/S10 records (`gold_S10_002`, `gold_S10_005`, `gold_S10_009`); adding missing label content (`gold_S8_017`, `gold_S9_011`, `gold_S9_014`, `gold_S10_005`); aligning severity/flow bands with wording (`gold_S10_007` now `extremely_heavy` with matching text, among others); restoring the S8 carrier on `gold_adversarial_001`.

`B9` on `gold_S8_018` is a correct natural alias for `folate` and is intentional.

## Verification at freeze
- 60 records, unique ids, no empty text on non-`empty` types.
- All six cycle-day computations correct (including the two de-mirrored cards: `gold_S9_007` = 6, `gold_S10_007` = 4).
- Leakage vs `data/text/train.jsonl`: exact matches 0; max token 4-gram Jaccard 0.0222; 8-gram containment 0.
- Card-level `(cycle_day, flow)` collisions with the 250 train cards: 0 (see `reports/leakage_fix.json`).

## Distractor slice (report separately in evaluation)
- Bare reaction marker with mood null/neutral: `gold_S8_001`, `gold_S8_004`, `gold_S10_014`
- Habitual qualifier with current-entry label: `gold_S8_008`, `gold_S8_001`
- Bare "meh": `gold_S9_005`
- Explicit feeling plus unrelated state: `gold_S9_016`
- Off-topic / instruction noise: `gold_adversarial_001`, `gold_adversarial_002`, `gold_off_topic_001`, `gold_off_topic_002`

This slice tests whether conservative generation taught the model to over-extract from tone, and whether instruction-like noise is ignored. It is the main robustness probe for the labeling boundary in `DECISIONS.md`.
