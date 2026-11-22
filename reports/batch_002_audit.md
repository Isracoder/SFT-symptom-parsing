# batch_002 audit — generated text correctness + realism

Scope: 140 generated text records in `C:\vs code files\ML\parser project\data\text\batch_002.jsonl`, audited against the immutable cards in `C:\vs code files\ML\parser project\data\facts\batch_002.jsonl`. No data, decisions, or examples were edited.

## Verdict

- **140 ACCEPT / 0 REJECT** (100.0% semantic acceptance).
- Structure compliance: **100.0%** (140/140).
- Schema-valid labels: **140/140** after canonicalizing partial cards to `null` / `[]`.
- Exact duplicates: **0**. Near duplicates at normalized token 4-gram Jaccard >= 0.85: **0** (max 0.154; 0.154 with numeric normalization).
- Held-out structure leaks: **0** S8–S10 forms in the batch.

## Per-structure

| structure | n | accept | reject | semantic accept | structure compliance | schema valid |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 20 | 20 | 0 | 100% | 100% | 20/20 |
| S2 | 20 | 20 | 0 | 100% | 100% | 20/20 |
| S3 | 20 | 20 | 0 | 100% | 100% | 20/20 |
| S4 | 20 | 20 | 0 | 100% | 100% | 20/20 |
| S5 | 20 | 20 | 0 | 100% | 100% | 20/20 |
| S6 | 20 | 20 | 0 | 100% | 100% | 20/20 |
| S7 | 20 | 20 | 0 | 100% | 100% | 20/20 |

## Fact fidelity

All 140 items were checked individually for omissions, invented or changed in-scope facts, polarity, severity, clot scale, date arithmetic, flow defaults, sleep midpoints, painkiller/supplement/hair/skin presence, global negation, and out-of-vocab ignoring.

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
- Near-duplicate pairs at Jaccard >= 0.85: **0**. Highest pair: `train_S1_021` / `train_S2_022` at 0.154 (numeric-normalized max 0.154).
- Overall words: min 3, median 12.0, mean 13.6, max 44.
- Overall characters: min 11, median 71.5, mean 77.31, max 219.

| structure | n | words min / median / mean / max | chars min / median / mean / max |
|---|---:|---|---|
| S1 | 20 | 3 / 12.0 / 12.5 / 25 | 21 / 78.5 / 79.5 / 177 |
| S2 | 20 | 6 / 13.0 / 14.45 / 29 | 31 / 74.5 / 85.05 / 173 |
| S3 | 20 | 4 / 11.0 / 11.35 / 25 | 26 / 64.5 / 70.95 / 170 |
| S4 | 20 | 7 / 20.0 / 21.9 / 44 | 36 / 100.0 / 111.95 / 219 |
| S5 | 20 | 5 / 14.0 / 14.3 / 26 | 26 / 77.5 / 79.2 / 163 |
| S6 | 20 | 3 / 3.0 / 3.5 / 6 | 11 / 19.0 / 18.65 / 25 |
| S7 | 20 | 8 / 17.0 / 17.2 / 33 | 44 / 88.0 / 95.85 / 198 |

Repeated 3-word openers (count >= 2): `i have no` x3; `painkiller yes sleep` x2; `supps some other` x2.

Most repeated sentence-initial frames (up to 5 tokens; count >= 2, top 12): `no spotting` x7; `no painkiller` x5; `mood good` x5; `no symptoms` x4; `no bleeding` x4; `sleep poor` x4; `took painkiller` x3; `flow is medium` x3; `sleep was good` x3; `no spotting took a painkiller` x2; `took calcium` x2; `took a painkiller` x2.

## Realism checks (warnings only — no auto-reject)

**Realism verdict: PASS** — 0 warning(s), 0 hard warning(s). Realism findings never change an item's semantic ACCEPT/REJECT verdict; a human decides.

- No realism warnings.

### Fact-density alignment

| band | records | words min / median / mean / max / stddev |
|---|---:|---|
| 1 | 20 | 3 / 3.0 / 3.5 / 6 / 0.97 |
| 2-3 | 54 | 3 / 9.5 / 10.3 / 23 / 4.63 |
| 4-6 | 54 | 8 / 16.0 / 17.39 / 42 / 6.21 |
| 7-9 | 12 | 19 / 25.0 / 28.25 / 44 / 8.28 |
| other | 0 | - |

| structure | 1 | 2-3 | 4-6 | 7-9 | other |
|---|---:|---:|---:|---:|---:|
| S1 | 0 | 9 | 9 | 2 | 0 |
| S2 | 0 | 9 | 9 | 2 | 0 |
| S3 | 0 | 9 | 9 | 2 | 0 |
| S4 | 0 | 9 | 9 | 2 | 0 |
| S5 | 0 | 9 | 9 | 2 | 0 |
| S6 | 20 | 0 | 0 | 0 | 0 |
| S7 | 0 | 9 | 9 | 2 | 0 |

### Schema-dump detector

Exempt list structures: `S1`, `S3` — 40 record(s) skipped (`train_S1_011`, `train_S1_012`, `train_S1_013`, `train_S1_014`, `train_S1_015`, `train_S1_016`, `train_S1_017`, `train_S1_018`, `train_S1_019`, `train_S1_020`, `train_S1_021`, `train_S1_022`, `train_S1_023`, `train_S1_024`, `train_S1_025`, `train_S1_026`, `train_S1_027`, `train_S1_028`, `train_S1_029`, `train_S1_030`, `train_S3_011`, `train_S3_012`, `train_S3_013`, `train_S3_014`, `train_S3_015`, `train_S3_016`, `train_S3_017`, `train_S3_018`, `train_S3_019`, `train_S3_020`, `train_S3_021`, `train_S3_022`, `train_S3_023`, `train_S3_024`, `train_S3_025`, `train_S3_026`, `train_S3_027`, `train_S3_028`, `train_S3_029`, `train_S3_030`).

- No schema-dump flags outside the exempt list structures.

### List-structure density cap

S1/S3 cards are capped at 7 non-null top-level facts.

- No S1/S3 card exceeds the cap.

### Opening frames (first 4 tokens)

| structure | n | distinct openers | most common opener | share |
|---|---:|---:|---|---:|
| S1 | 20 | 20 | `after dark 8 9h` | 5.0% |
| S2 | 20 | 20 | `afternoon already spotting today` | 5.0% |
| S3 | 20 | 20 | `energy low hair normal` | 5.0% |
| S4 | 20 | 20 | `after lunch diarrhea is` | 5.0% |
| S5 | 20 | 20 | `3 5 4 hours` | 5.0% |
| S6 | 20 | 20 | `acne acting up` | 5.0% |
| S7 | 20 | 20 | `am i overthinkng this` | 5.0% |

Overall top openers: `3 5 4 hours` x1 (0.7%); `acne acting up` x1 (0.7%); `after dark 8 9h` x1 (0.7%); `after lunch diarrhea is` x1 (0.7%); `after work took a` x1 (0.7%); `afternoon already spotting today` x1 (0.7%); `ah no headache and` x1 (0.7%); `alright medium flow mood` x1 (0.7%); `am i overthinkng this` x1 (0.7%); `amazing sleep honestly` x1 (0.7%).

### Sentence-initial subjects (distribution only)

| structure | my period | i | today | no | bare_fragment | other |
|---|---|---|---|---|---|---|
| S1 | 0 (0%) | 0 (0%) | 0 (0%) | 2 (10%) | 15 (75%) | 3 (15%) |
| S2 | 0 (0%) | 5 (25%) | 0 (0%) | 1 (5%) | 0 (0%) | 14 (70%) |
| S3 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 15 (75%) | 5 (25%) |
| S4 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 8 (40%) | 12 (60%) |
| S5 | 0 (0%) | 7 (35%) | 1 (5%) | 1 (5%) | 0 (0%) | 11 (55%) |
| S6 | 0 (0%) | 0 (0%) | 0 (0%) | 2 (10%) | 16 (80%) | 2 (10%) |
| S7 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 20 (100%) |
| overall | 0 (0%) | 12 (9%) | 1 (1%) | 6 (4%) | 54 (39%) | 67 (48%) |

### Length variance

| structure | n | min | max | mean | stddev | warning |
|---|---:|---:|---:|---:|---:|---|
| S1 | 20 | 3 | 25 | 12.5 | 5.61 |  |
| S2 | 20 | 6 | 29 | 14.45 | 6.28 |  |
| S3 | 20 | 4 | 25 | 11.35 | 5.94 |  |
| S4 | 20 | 7 | 44 | 21.9 | 10.65 |  |
| S5 | 20 | 5 | 26 | 14.3 | 5.97 |  |
| S6 | 20 | 3 | 6 | 3.5 | 0.97 |  |
| S7 | 20 | 8 | 33 | 17.2 | 7.45 |  |

## Independent fact-coverage verification

- Dataset-level fact-coverage checks were skipped for this path (they are batch_001-specific). Pass `--coverage` to run them.

## Gate recommendation

**SCALE NEXT BATCH.**

The batch clears every stated scale condition and the realism screens: semantic acceptance, zero exact duplicates, no held-out S8–S10 structure leaks, and no warning-level realism signals.

Machine-readable metrics: `C:\vs code files\ML\parser project\reports\batch_002_metrics.json`. The `realism_warnings` block at the top summarizes every realism finding with offending record ids.
