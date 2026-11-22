# validation semantic audit — final re-audit after leakage repair (Agent 3)

Scope: 35 records in `data/text/validation.jsonl` vs `data/facts/validation.jsonl`, re-audited after the leakage fix described in `reports/leakage_fix.json`. 7 cards were replaced from the unused superset pool with 7 regenerated texts; the other 28 are unchanged.

## Final verdict

- **35 ACCEPT / 0 REJECT.**
- Realism: **35 ok / 0 warn / 0 bad.**
- Leakage re-check (independent, against `data/facts/train_250.jsonl` and `data/text/train.jsonl`): **0 cycle_day/flow collisions, 0 exact full-fact duplicates, 0 near-paraphrases (max token 4-gram Jaccard 0.1364, far below 0.85).**

## Leakage repair — what changed

The prior `FIX AND RE-AUDIT` verdict was for card-level train/validation leakage; labels were already clean. The repair (per `reports/leakage_fix.json`):

- **7 validation cards replaced** from the unused 400-card superset pool, with 7 regenerated texts: `validation_S1_001`, `S1_003`, `S2_003`, `S3_003`, `S4_003`, `S5_003`, `S7_003`.
- **2 gold cards de-mirrored** (text still owner-handwritten, none written here): `gold_S9_007` cycle_day 7→6 (heavy), `gold_S10_007` cycle_day 8→4 (extremely_heavy).
- **Documented deviations:** `validation_S1_003` and `validation_S3_003` cycle_day nudged (11→12, 13→14) because no collision-free verbatim donor existed; `validation_S3_003` lost `negation`, `validation_S7_003` lost `negation`+`supplement_naming` (no donor carried them). Net tag slice: negation 15→14 (no collapse); `implicit_dates` stays 6.

## The 7 re-audited records (ACCEPT, with reasons)

| id | cycle_day / flow | reason |
|---|---|---|
| `validation_S1_001` | — | supplements folate+calcium, mood neutral (`"mood mid"`), hair oily all present; fact order hair→supplements→mood; S1 list; clean. |
| `validation_S1_003` | 12 / heavy | `"period started 11 days ago"`→12 ✓; energy high, denied insomnia, sleep_quality good, mood good all present with typos `enrgy`/`modo`; order energy→denials→cycle→flow→sleep→mood. |
| `validation_S2_003` | 12 / extremely_heavy | `"period started 11 days ago"`→12 ✓; flow, mood good, energy mid, hair dry, painkiller false (`"took no painkiller"`) present; typos `extremly`/`enrgy`; 4 declarative sentences. |
| `validation_S3_003` | 14 / light | `"cyle: started 13 days ago"`→14 ✓; painkiller, mood good, skin acne, hair growth (`gorwth`) present; telegraphic; `negation` correctly absent from card+text. |
| `validation_S4_003` | 14 / medium | `"period started 13 days ago"`→14 ✓; flow medium, denied breast_tenderness, mood good, sleep 8.5 (`8-9 hours`), hair loss present; typos `adn`/`teh`; run-on. |
| `validation_S5_003` | 15 / heavy | `"period start 14 days ago"`→15 ✓; sleep 9, hair normal, denied headache, folate present; typos `slep`/`nromal`; broken English. |
| `validation_S7_003` | 17 / light | `"period started 16 days ago"`→17 ✓; bloating null, insomnia moderate, cravings null (no severity cue), sleep 4, mood good, hair dry present; one question + assertions; typos `cravnig`/`slep`. |

All seven: every affirmed symptom present with exact severity band, null severities carry no cue, denials/polarity correct, cycle_day N+1 arithmetic correct, fact order matches each card's constraints, no S8–S10 forms, no phantom content, no implied negatives.

## Independent leakage re-check (results)

Run against the 250 train cards in `data/facts/train_250.jsonl` (235 ordinary + 15 specials) and 250 texts in `data/text/train.jsonl`:

- **(a) cycle_day/flow pairs**: no validation or gold ordinary card shares a `(cycle_day, flow)` pair with any train ordinary card — **0 collisions**. (Gold `gold_S9_007`=6/heavy and `gold_S10_007`=4/extremely_heavy are now collision-free; their handwritten texts must read "started 5 days ago" / "started 3 days ago" respectively.)
- **(b) exact full-fact duplicates**: **0** between validation/gold ordinary and train ordinary (canonicalised facts, array order ignored).
- **(c) near-paraphrase**: **0** validation text vs any train text at token 4-gram Jaccard ≥ 0.85; max observed 0.1364 (`validation_S2_001` vs `train_S4_015`, a benign shared `"5-6 hours of sleep"` bigram overlap).

The six prior mirror pairs are all resolved: the repaired validation `implicit_dates` cycle_day values (12, 12, 14, 14, 15, 17) no longer collide with any train `(cycle_day, flow)` pair, and their regenerated texts no longer share the old `"period started N days ago" + flow` phrasing with train.

## Untouched 28 records

Confirmed still 28 (ids listed in the item audit), with facts and text unchanged from the pre-repair audit; the 7 changed ids match `leakage_fix.json`'s `text_validation_changed` exactly. Validation remains 35 records, 5 per structure (S1–S7), with 6 `implicit_dates` records.

## Remaining concern (non-blocking)

The two documented tag-profile deviations — `validation_S3_003` (no `negation`) and `validation_S7_003` (no `negation`/`supplement_naming`) — slightly reduce the validation split's negation-tag slice (15→14) but do not collapse any coverage minimum, and the cards/texts are internally consistent with the reduced tag sets. This is accepted and recorded in `leakage_fix.json`. The de-mirrored gold cards still have no text; the owner must respect the new cycle_day (6, 4) when handwriting them.

## Audit reliability

A Node script verified: validation fact/text id sets are identical (35/35); train_250 fact and train text id sets are identical (250/250); every id and quoted phrase in this report is a substring of the referenced record's text (10/10 quote checks, 0 failures); the 7 changed ids and the 2 gold ids exist and carry the expected new cycle_day; and the (a)/(b)/(c) leakage checks were computed programmatically (set-based 4-gram Jaccard for near-paraphrase). No claim was made from memory.

## Gate verdict

**SCALE NEXT BATCH.**

The prior `FIX AND RE-AUDIT` was for card-level train/validation leakage, and that is now closed: the repaired validation split has no `(cycle_day, flow)` collision, no full-fact duplicate, and no near-paraphrase against the 250 train records. All 35 labels remain factually clean (the seven replacements re-audited fully, the 28 untouched confirmed unchanged), so the validation split is once again trustworthy for model selection. The only open item is the owner's still-pending handwritten gold text, which must respect the de-mirrored cycle_day values; that is a forward task, not a reason to hold this batch.

Files written:
- `reports/validation_item_audit.jsonl` (35 lines, overwritten)
- `reports/validation_semantic_audit.md` (this file, overwritten)
