# validation audit — generated text correctness + realism

Scope: 35 generated text records in `C:\vs code files\ML\parser project\data\text\validation.jsonl`, audited against the immutable cards in `C:\vs code files\ML\parser project\data\facts\validation.jsonl`. No data, decisions, or examples were edited.

## Verdict

- **35 ACCEPT / 0 REJECT** (100.0% semantic acceptance).
- Structure compliance: **100.0%** (35/35).
- Schema-valid labels: **35/35** after canonicalizing partial cards to `null` / `[]`.
- Exact duplicates: **0**. Near duplicates at normalized token 4-gram Jaccard >= 0.85: **0** (max 0.200; 0.200 with numeric normalization).
- Empty inputs (type=empty, identical by specification and exempt from the duplicate checks): **0**.
- Held-out structure leaks: **0** S8–S10 forms in the batch.

## Per-structure

| structure | n | accept | reject | semantic accept | structure compliance | schema valid |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 5 | 5 | 0 | 100% | 100% | 5/5 |
| S2 | 5 | 5 | 0 | 100% | 100% | 5/5 |
| S3 | 5 | 5 | 0 | 100% | 100% | 5/5 |
| S4 | 5 | 5 | 0 | 100% | 100% | 5/5 |
| S5 | 5 | 5 | 0 | 100% | 100% | 5/5 |
| S6 | 5 | 5 | 0 | 100% | 100% | 5/5 |
| S7 | 5 | 5 | 0 | 100% | 100% | 5/5 |

## Fact fidelity

All 35 ordinary items were checked individually for omissions, invented or changed in-scope facts, polarity, severity, clot scale, date arithmetic, flow defaults, sleep midpoints, painkiller/supplement/hair/skin presence, global negation, and out-of-vocab ignoring.

| check | errors |
|---|---:|
| missing facts | 0 |
| invented facts | 0 |
| changed values | 0 |
| negation / polarity | 0 |
| severity bands | 0 |
| blood_clots scale | 0 |
| cycle_day N+1 arithmetic | 0 |
| flow default / absence | 0 |
| sleep range midpoint | 0 |
| painkiller | 0 |
| supplements | 0 |
| hair / skin | 0 |
| no_symptoms_asserted | 0 |
| out-of-vocab ignoring | 0 |
| S1–S7 structure rules | 0 |
| S8–S10 forms in batch | 0 |

Mechanical coverage of the audited facts:

- `cycle_day`: checked via relative period-start wording (`N+1`, `today` -> 1, `yesterday` -> 2).
- `sleep_hours`: checked as single values or range midpoints.
- `blood_clots`: kept on its separate clot scale.
- `flow`: every period/bleeding statement has a flow value; every `none` needs an explicit no-bleeding cue.
- `painkiller`: true/false/null checked against explicit cues and negations.
- `supplements`, `hair`, `skin`: presence and naming checked.
- `no_symptoms_asserted`: true only for global claims; never false.
- Out-of-vocab/filler language is not encoded as an extra field.

## Duplicates, length, templating

- Exact duplicate groups: **0**.
- Empty inputs exempt from the exact/near-duplicate checks (type=empty, identical by specification): **0**.
- Near-duplicate pairs at Jaccard >= 0.85: **0**. Highest pair: `validation_S3_004` / `validation_S6_004` at 0.200 (numeric-normalized max 0.200).
- Overall words: min 3, median 18, mean 16.89, max 34.
- Overall characters: min 20, median 91, mean 94.11, max 190.

| structure | n | words min / median / mean / max | chars min / median / mean / max |
|---|---:|---|---|
| S1 | 5 | 8 / 16 / 15 / 22 | 46 / 91 / 92 / 137 |
| S2 | 5 | 12 / 21 / 21.4 / 28 | 48 / 116 / 114.6 / 167 |
| S3 | 5 | 4 / 15 / 13.2 / 21 | 28 / 88 / 82.4 / 130 |
| S4 | 5 | 12 / 29 / 24.4 / 33 | 62 / 137 / 122.2 / 176 |
| S5 | 5 | 7 / 18 / 17.2 / 30 | 33 / 94 / 97 / 161 |
| S6 | 5 | 3 / 4 / 3.8 / 4 | 20 / 22 / 21.4 / 23 |
| S7 | 5 | 12 / 24 / 23.2 / 34 | 60 / 131 / 129.2 / 190 |

Repeated 3-word openers (count >= 2): .

Most repeated sentence-initial frames (up to 5 tokens; count >= 2, top 12): `got 5 6 hours of` x2; `breasts a bit tender` x2; `i take folate` x2.

## Realism checks (warnings only — no auto-reject)

**Realism verdict: PASS** — 0 warning(s), 0 hard warning(s). Realism findings never change an item's semantic ACCEPT/REJECT verdict; a human decides.

- No realism warnings.

### Fact-density alignment

| band | records | words min / median / mean / max / stddev |
|---|---:|---|
| 1 | 5 | 3 / 4 / 3.8 / 4 / 0.4 |
| 2-3 | 12 | 4 / 10.5 / 11.33 / 20 / 4.68 |
| 4-6 | 12 | 15 / 21.5 / 22.33 / 32 / 5.12 |
| 7-9 | 6 | 21 / 29.0 / 28 / 34 / 5.0 |
| other | 0 | - |

| structure | 1 | 2-3 | 4-6 | 7-9 | other |
|---|---:|---:|---:|---:|---:|
| S1 | 0 | 2 | 2 | 1 | 0 |
| S2 | 0 | 2 | 2 | 1 | 0 |
| S3 | 0 | 2 | 2 | 1 | 0 |
| S4 | 0 | 2 | 2 | 1 | 0 |
| S5 | 0 | 2 | 2 | 1 | 0 |
| S6 | 5 | 0 | 0 | 0 | 0 |
| S7 | 0 | 2 | 2 | 1 | 0 |

### Schema-dump detector

Exempt list structures: `S1`, `S3` — 10 record(s) skipped (`validation_S1_001`, `validation_S1_002`, `validation_S1_003`, `validation_S1_004`, `validation_S1_005`, `validation_S3_001`, `validation_S3_002`, `validation_S3_003`, `validation_S3_004`, `validation_S3_005`).

- No schema-dump flags outside the exempt list structures.

### List-structure density cap

S1/S3 cards are capped at 7 non-null top-level facts.

- No S1/S3 card exceeds the cap.

### Opening frames (first 4 tokens)

| structure | n | distinct openers | most common opener | share |
|---|---:|---:|---|---:|
| S1 | 5 | 5 | `hmm enrgy high no` | 20.0% |
| S2 | 5 | 5 | `busy day at work` | 20.0% |
| S3 | 5 | 5 | `evening calcium sleep poor` | 20.0% |
| S4 | 5 | 5 | `anyway slept good and` | 20.0% |
| S5 | 5 | 5 | `i have no pelvic` | 20.0% |
| S6 | 5 | 5 | `bleeding none today` | 20.0% |
| S7 | 5 | 5 | `did i do this` | 20.0% |

Overall top openers: `anyway slept good and` x1 (2.9%); `bleeding none today` x1 (2.9%); `breasts a bit tender` x1 (2.9%); `busy day at work` x1 (2.9%); `did i do this` x1 (2.9%); `evening calcium sleep poor` x1 (2.9%); `fatigue crippling headache slight` x1 (2.9%); `hair oily mood meh` x1 (2.9%); `hmm enrgy high no` x1 (2.9%); `how much folate is` x1 (2.9%).

### Sentence-initial subjects (distribution only)

| structure | my period | i | today | no | bare_fragment | other |
|---|---|---|---|---|---|---|
| S1 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 5 (100%) | 0 (0%) |
| S2 | 0 (0%) | 1 (20%) | 0 (0%) | 0 (0%) | 0 (0%) | 4 (80%) |
| S3 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 5 (100%) | 0 (0%) |
| S4 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 1 (20%) | 4 (80%) |
| S5 | 0 (0%) | 3 (60%) | 1 (20%) | 0 (0%) | 0 (0%) | 1 (20%) |
| S6 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 5 (100%) | 0 (0%) |
| S7 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 5 (100%) |
| overall | 0 (0%) | 4 (11%) | 1 (3%) | 0 (0%) | 16 (46%) | 14 (40%) |

### Length variance

| structure | n | min | max | mean | stddev | warning |
|---|---:|---:|---:|---:|---:|---|
| S1 | 5 | 8 | 22 | 15 | 5.66 |  |
| S2 | 5 | 12 | 28 | 21.4 | 5.57 |  |
| S3 | 5 | 4 | 21 | 13.2 | 6.31 |  |
| S4 | 5 | 12 | 33 | 24.4 | 8.69 |  |
| S5 | 5 | 7 | 30 | 17.2 | 8.47 |  |
| S6 | 5 | 3 | 4 | 3.8 | 0.4 |  |
| S7 | 5 | 12 | 34 | 23.2 | 7.41 |  |

## Independent fact-coverage verification

- Dataset-level fact-coverage checks were skipped for this path (they are batch_001-specific). Pass `--coverage` to run them.

## Gate recommendation

**SCALE NEXT BATCH.**

The batch clears every stated scale condition and the realism screens: semantic acceptance, zero exact duplicates, no held-out S8–S10 structure leaks, and no warning-level realism signals.

Machine-readable metrics: `C:\vs code files\ML\parser project\reports\validation_metrics.json`. The `realism_warnings` block at the top summarizes every realism finding with offending record ids.
