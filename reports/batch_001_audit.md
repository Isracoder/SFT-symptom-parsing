# batch_001 audit — generated text correctness + realism

Scope: 70 generated text records in `C:\vs code files\ML\parser project\data\text\batch_001.jsonl`, audited against the immutable cards in `C:\vs code files\ML\parser project\data\facts\batch_001.jsonl`. No data, decisions, or examples were edited.

## Verdict

- **70 ACCEPT / 0 REJECT** (100.0% semantic acceptance).
- Structure compliance: **100.0%** (70/70).
- Schema-valid labels: **70/70** after canonicalizing partial cards to `null` / `[]`.
- Exact duplicates: **0**. Near duplicates at normalized token 4-gram Jaccard >= 0.85: **0** (max 0.111; 0.160 with numeric normalization).
- Held-out structure leaks: **0** S8–S10 forms in the batch.

## Per-structure

| structure | n | accept | reject | semantic accept | structure compliance | schema valid |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 10 | 10 | 0 | 100% | 100% | 10/10 |
| S2 | 10 | 10 | 0 | 100% | 100% | 10/10 |
| S3 | 10 | 10 | 0 | 100% | 100% | 10/10 |
| S4 | 10 | 10 | 0 | 100% | 100% | 10/10 |
| S5 | 10 | 10 | 0 | 100% | 100% | 10/10 |
| S6 | 10 | 10 | 0 | 100% | 100% | 10/10 |
| S7 | 10 | 10 | 0 | 100% | 100% | 10/10 |

## Fact fidelity

All 70 items were checked individually for omissions, invented or changed in-scope facts, polarity, severity, clot scale, date arithmetic, flow defaults, sleep midpoints, painkiller/supplement/hair/skin presence, global negation, and out-of-vocab ignoring.

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
- Near-duplicate pairs at Jaccard >= 0.85: **0**. Highest pair: `train_S1_001` / `train_S2_010` at 0.111 (numeric-normalized max 0.160).
- Overall words: min 3, median 12.0, mean 13.31, max 31.
- Overall characters: min 13, median 66.5, mean 74.96, max 170.

| structure | n | words min / median / mean / max | chars min / median / mean / max |
|---|---:|---|---|
| S1 | 10 | 6 / 9.5 / 11.8 / 20 | 35 / 63.5 / 73.6 / 141 |
| S2 | 10 | 8 / 15.5 / 16.5 / 24 | 46 / 81.0 / 91.1 / 142 |
| S3 | 10 | 4 / 11.0 / 10.6 / 18 | 29 / 68.5 / 67.1 / 101 |
| S4 | 10 | 10 / 20.0 / 19 / 31 | 53 / 107.5 / 100.8 / 148 |
| S5 | 10 | 6 / 12.0 / 15 / 27 | 34 / 62.0 / 80.9 / 170 |
| S6 | 10 | 3 / 3.0 / 3.2 / 4 | 13 / 16.0 / 16 / 20 |
| S7 | 10 | 11 / 15.5 / 17.1 / 29 | 53 / 84.0 / 95.2 / 160 |

Repeated 3-word openers (count >= 2): .

Most repeated sentence-initial frames (up to 5 tokens; count >= 2, top 12): `no spotting` x4; `skin is normal` x3; `light flow` x3; `no symptoms at all` x3; `no painkiller` x2; `flow is heavy` x2; `mood is good` x2; `sleep is poor` x2.

## Realism checks (warnings only — no auto-reject)

**Realism verdict: PASS** — 0 warning(s), 0 hard warning(s). Realism findings never change an item's semantic ACCEPT/REJECT verdict; a human decides.

- No realism warnings.

### Fact-density alignment

| band | records | words min / median / mean / max / stddev |
|---|---:|---|
| 1 | 10 | 3 / 3.0 / 3.2 / 4 / 0.4 |
| 2-3 | 30 | 4 / 10.0 / 10.6 / 21 / 4.04 |
| 4-6 | 24 | 9 / 18.0 / 18.83 / 29 / 6.14 |
| 7-9 | 6 | 18 / 20.0 / 21.67 / 31 / 4.35 |
| other | 0 | - |

| structure | 1 | 2-3 | 4-6 | 7-9 | other |
|---|---:|---:|---:|---:|---:|
| S1 | 0 | 5 | 4 | 1 | 0 |
| S2 | 0 | 5 | 4 | 1 | 0 |
| S3 | 0 | 5 | 4 | 1 | 0 |
| S4 | 0 | 5 | 4 | 1 | 0 |
| S5 | 0 | 5 | 4 | 1 | 0 |
| S6 | 10 | 0 | 0 | 0 | 0 |
| S7 | 0 | 5 | 4 | 1 | 0 |

### Schema-dump detector

Exempt list structures: `S1`, `S3` — 20 record(s) skipped (`train_S1_001`, `train_S1_002`, `train_S1_003`, `train_S1_004`, `train_S1_005`, `train_S1_006`, `train_S1_007`, `train_S1_008`, `train_S1_009`, `train_S1_010`, `train_S3_001`, `train_S3_002`, `train_S3_003`, `train_S3_004`, `train_S3_005`, `train_S3_006`, `train_S3_007`, `train_S3_008`, `train_S3_009`, `train_S3_010`).

- No schema-dump flags outside the exempt list structures.

### List-structure density cap

S1/S3 cards are capped at 7 non-null top-level facts.

- No S1/S3 card exceeds the cap.

### Opening frames (first 4 tokens)

| structure | n | distinct openers | most common opener | share |
|---|---:|---:|---|---:|
| S1 | 10 | 10 | `evening mood neutral no` | 10.0% |
| S2 | 10 | 10 | `i took my iron` | 10.0% |
| S3 | 10 | 10 | `clots light i think` | 10.0% |
| S4 | 10 | 10 | `anyway hair is normal` | 10.0% |
| S5 | 10 | 10 | `big blood clots i` | 10.0% |
| S6 | 10 | 10 | `barely 3 5 hours` | 10.0% |
| S7 | 10 | 10 | `am i doing okay` | 10.0% |

Overall top openers: `am i doing okay` x1 (1.4%); `anyway hair is normal` x1 (1.4%); `barely 3 5 hours` x1 (1.4%); `big blood clots i` x1 (1.4%); `clots light i think` x1 (1.4%); `cramps or just pressure` x1 (1.4%); `cycle started today flow` x1 (1.4%); `did my period start` x1 (1.4%); `energy on a scale` x1 (1.4%); `evening cravings all day` x1 (1.4%).

### Sentence-initial subjects (distribution only)

| structure | my period | i | today | no | bare_fragment | other |
|---|---|---|---|---|---|---|
| S1 | 0 (0%) | 0 (0%) | 0 (0%) | 1 (10%) | 9 (90%) | 0 (0%) |
| S2 | 0 (0%) | 2 (20%) | 0 (0%) | 0 (0%) | 0 (0%) | 8 (80%) |
| S3 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 9 (90%) | 1 (10%) |
| S4 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 7 (70%) | 3 (30%) |
| S5 | 0 (0%) | 2 (20%) | 1 (10%) | 0 (0%) | 0 (0%) | 7 (70%) |
| S6 | 0 (0%) | 0 (0%) | 0 (0%) | 1 (10%) | 8 (80%) | 1 (10%) |
| S7 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 10 (100%) |
| overall | 0 (0%) | 4 (6%) | 1 (1%) | 2 (3%) | 33 (47%) | 30 (43%) |

### Length variance

| structure | n | min | max | mean | stddev | warning |
|---|---:|---:|---:|---:|---:|---|
| S1 | 10 | 6 | 20 | 11.8 | 4.71 |  |
| S2 | 10 | 8 | 24 | 16.5 | 6.02 |  |
| S3 | 10 | 4 | 18 | 10.6 | 4.41 |  |
| S4 | 10 | 10 | 31 | 19 | 7.04 |  |
| S5 | 10 | 6 | 27 | 15 | 7.66 |  |
| S6 | 10 | 3 | 4 | 3.2 | 0.4 |  |
| S7 | 10 | 11 | 29 | 17.1 | 5.7 |  |

## Independent fact-coverage verification

- Counts: **400 train / 35 validation / 60 gold**; **495 globally unique IDs**; batch 70 maps to the supplied card file.
- DECISIONS minima: every field is non-null in >= 2 train structures and >= 1 gold structure; every enum value appears in train and gold; negation 185 train / 35 gold (min 40/8); global negation 47 / 6 (min 20/4); 4+ symptoms 36 / 6 (min 30/6).
- Train/validation disjointness: **0 shared fact cards**.
- `reports/fact_coverage.json` compared with independently rebuilt counts, structure counts, field non-null coverage, enum/boolean values, tags, and coverage slices: **no discrepancies**.
- Coverage errors: **0**.

## Gate recommendation

**SCALE NEXT BATCH.**

The batch clears every stated scale condition and the realism screens: semantic acceptance, zero exact duplicates, no held-out S8–S10 structure leaks, and no warning-level realism signals.

Machine-readable metrics: `C:\vs code files\ML\parser project\reports\batch_001_metrics.json`. The `realism_warnings` block at the top summarizes every realism finding with offending record ids.
