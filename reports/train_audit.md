# train audit — generated text correctness + realism

Scope: 250 generated text records in `C:\vs code files\ML\parser project\data\text\train.jsonl`, audited against the immutable cards in `C:\vs code files\ML\parser project\data\facts\train_250.jsonl`. No data, decisions, or examples were edited.

## Verdict

- **250 ACCEPT / 0 REJECT** (100.0% semantic acceptance).
- Structure compliance: **100.0%** (250/250).
- Schema-valid labels: **250/250** after canonicalizing partial cards to `null` / `[]`.
- Exact duplicates: **0**. Near duplicates at normalized token 4-gram Jaccard >= 0.85: **0** (max 0.154; 0.160 with numeric normalization).
- Empty inputs (type=empty, identical by specification and exempt from the duplicate checks): **5**.
- Special inputs: **15** (5 adversarial / 5 off_topic / 5 empty); 0 special warning(s).
- Held-out structure leaks: **0** S8–S10 forms in the batch.

## Per-structure

| structure | n | accept | reject | semantic accept | structure compliance | schema valid |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 34 | 34 | 0 | 100% | 100% | 34/34 |
| S2 | 34 | 34 | 0 | 100% | 100% | 34/34 |
| S3 | 34 | 34 | 0 | 100% | 100% | 34/34 |
| S4 | 34 | 34 | 0 | 100% | 100% | 34/34 |
| S5 | 33 | 33 | 0 | 100% | 100% | 33/33 |
| S6 | 33 | 33 | 0 | 100% | 100% | 33/33 |
| S7 | 33 | 33 | 0 | 100% | 100% | 33/33 |
| specials | 15 | 15 | 0 | 100% | 100% | 15/15 |

## Fact fidelity

All 235 ordinary items were checked individually for omissions, invented or changed in-scope facts, polarity, severity, clot scale, date arithmetic, flow defaults, sleep midpoints, painkiller/supplement/hair/skin presence, global negation, and out-of-vocab ignoring.

The 15 special inputs are not fact-bearing; they are verified in the Special inputs section below (empty extraction label, carrier/no-carrier, injection presence, off-topic cue scan, blank-input check).

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

## Special inputs (empty extraction object)

15 specials: 5 adversarial, 5 off_topic, 5 empty. Every special must carry the empty extraction object (scalars null, lists empty).

Adversarial carrier structures: `S1` x3, `S2` x2. The injected instruction is noise; no facts are extracted from it.

| id | type | carrier | label empty | check |
|---|---|---|---|---|
| `train_adversarial_001` | adversarial | S1 | yes | injection present |
| `train_adversarial_002` | adversarial | S2 | yes | injection present |
| `train_adversarial_003` | adversarial | S1 | yes | injection present |
| `train_adversarial_004` | adversarial | S2 | yes | injection present |
| `train_adversarial_005` | adversarial | S1 | yes | injection present |
| `train_off_topic_001` | off_topic | null | yes | no in-scope cues |
| `train_off_topic_002` | off_topic | null | yes | no in-scope cues |
| `train_off_topic_003` | off_topic | null | yes | no in-scope cues |
| `train_off_topic_004` | off_topic | null | yes | no in-scope cues |
| `train_off_topic_005` | off_topic | null | yes | no in-scope cues |
| `train_empty_001` | empty | null | yes | whitespace-only |
| `train_empty_002` | empty | null | yes | whitespace-only |
| `train_empty_003` | empty | null | yes | whitespace-only |
| `train_empty_004` | empty | null | yes | whitespace-only |
| `train_empty_005` | empty | null | yes | whitespace-only |

- No special-input warnings.

## Duplicates, length, templating

- Exact duplicate groups: **0**.
- Empty inputs exempt from the exact/near-duplicate checks (type=empty, identical by specification): **5**.
- Near-duplicate pairs at Jaccard >= 0.85: **0**. Highest pair: `train_S1_021` / `train_S2_022` at 0.154 (numeric-normalized max 0.160).
- Overall words: min 0, median 13.0, mean 13.84, max 44.
- Overall characters: min 0, median 77.5, mean 79.36, max 219.

| structure | n | words min / median / mean / max | chars min / median / mean / max |
|---|---:|---|---|
| S1 | 34 | 3 / 12.5 / 12.65 / 25 | 21 / 78.5 / 80.62 / 177 |
| S2 | 34 | 6 / 14.0 / 15.24 / 29 | 31 / 83.0 / 88.32 / 173 |
| S3 | 34 | 4 / 11.0 / 11.44 / 25 | 26 / 71.5 / 72.97 / 170 |
| S4 | 34 | 7 / 21.0 / 21.09 / 44 | 36 / 105.0 / 109.29 / 219 |
| S5 | 33 | 5 / 14 / 14.76 / 27 | 26 / 77 / 81 / 170 |
| S6 | 33 | 3 / 3 / 3.39 / 6 | 11 / 16 / 18.18 / 25 |
| S7 | 33 | 8 / 17 / 17.67 / 33 | 44 / 88 / 98.55 / 198 |
| specials | 15 | 0 / 19 / 14.87 / 32 | 0 / 110 / 91.67 / 194 |

Repeated 3-word openers (count >= 2): `i have no` x4; `late evening took` x2; `i ve got` x2; `painkiller yes sleep` x2; `supps some other` x2; `how do i` x2; `is this all` x2.

Most repeated sentence-initial frames (up to 5 tokens; count >= 2, top 12): `no spotting` x11; `no painkiller` x7; `mood good` x5; `no symptoms at all` x4; `took painkiller` x4; `mood is good` x4; `no symptoms` x4; `no bleeding` x4; `sleep poor` x4; `skin is normal` x3; `light flow` x3; `sleep is fair` x3.

## Realism checks (warnings only — no auto-reject)

**Realism verdict: PASS** — 0 warning(s), 0 hard warning(s). Realism findings never change an item's semantic ACCEPT/REJECT verdict; a human decides.

- No realism warnings.

### Fact-density alignment

| band | records | words min / median / mean / max / stddev |
|---|---:|---|
| 1 | 33 | 3 / 3 / 3.39 / 6 / 0.81 |
| 2-3 | 94 | 3 / 10.0 / 10.88 / 23 / 4.61 |
| 4-6 | 90 | 8 / 17.0 / 18.13 / 42 / 6.06 |
| 7-9 | 18 | 18 / 24.5 / 26.06 / 44 / 7.85 |
| other | 0 | - |

| structure | 1 | 2-3 | 4-6 | 7-9 | other |
|---|---:|---:|---:|---:|---:|
| S1 | 0 | 16 | 15 | 3 | 0 |
| S2 | 0 | 16 | 15 | 3 | 0 |
| S3 | 0 | 16 | 15 | 3 | 0 |
| S4 | 0 | 16 | 15 | 3 | 0 |
| S5 | 0 | 15 | 15 | 3 | 0 |
| S6 | 33 | 0 | 0 | 0 | 0 |
| S7 | 0 | 15 | 15 | 3 | 0 |

### Schema-dump detector

Exempt list structures: `S1`, `S3` — 68 record(s) skipped (`train_S1_001`, `train_S1_002`, `train_S1_003`, `train_S1_004`, `train_S1_005`, `train_S1_006`, `train_S1_007`, `train_S1_008`, `train_S1_009`, `train_S1_010`, `train_S1_011`, `train_S1_012`, `train_S1_013`, `train_S1_014`, `train_S1_015`, `train_S1_016`, `train_S1_017`, `train_S1_018`, `train_S1_019`, `train_S1_020`, `train_S1_021`, `train_S1_022`, `train_S1_023`, `train_S1_024`, `train_S1_025`, `train_S1_026`, `train_S1_027`, `train_S1_028`, `train_S1_029`, `train_S1_030`, `train_S1_034`, `train_S1_038`, `train_S1_042`, `train_S1_045`, `train_S3_001`, `train_S3_002`, `train_S3_003`, `train_S3_004`, `train_S3_005`, `train_S3_006`, `train_S3_007`, `train_S3_008`, `train_S3_009`, `train_S3_010`, `train_S3_011`, `train_S3_012`, `train_S3_013`, `train_S3_014`, `train_S3_015`, `train_S3_016`, `train_S3_017`, `train_S3_018`, `train_S3_019`, `train_S3_020`, `train_S3_021`, `train_S3_022`, `train_S3_023`, `train_S3_024`, `train_S3_025`, `train_S3_026`, `train_S3_027`, `train_S3_028`, `train_S3_029`, `train_S3_030`, `train_S3_034`, `train_S3_035`, `train_S3_042`, `train_S3_050`).

- No schema-dump flags outside the exempt list structures.

### List-structure density cap

S1/S3 cards are capped at 7 non-null top-level facts.

- No S1/S3 card exceeds the cap.

### Opening frames (first 4 tokens)

| structure | n | distinct openers | most common opener | share |
|---|---:|---:|---|---:|
| S1 | 34 | 34 | `after dark 8 9h` | 2.9% |
| S2 | 34 | 34 | `afternoon already spotting today` | 2.9% |
| S3 | 34 | 34 | `breast tenderness worst ever` | 2.9% |
| S4 | 34 | 34 | `after lunch diarrhea is` | 2.9% |
| S5 | 33 | 32 | `i have no symptoms` | 6.1% |
| S6 | 33 | 33 | `acne acting up` | 3.0% |
| S7 | 33 | 33 | `am i doing okay` | 3.0% |

Overall top openers: `i have no symptoms` x2 (0.9%); `3 5 4 hours` x1 (0.4%); `acne acting up` x1 (0.4%); `after dark 8 9h` x1 (0.4%); `after lunch diarrhea is` x1 (0.4%); `after work took a` x1 (0.4%); `afternoon already spotting today` x1 (0.4%); `ah no headache and` x1 (0.4%); `alright medium flow mood` x1 (0.4%); `am i doing okay` x1 (0.4%).

### Sentence-initial subjects (distribution only)

| structure | my period | i | today | no | bare_fragment | other |
|---|---|---|---|---|---|---|
| S1 | 0 (0%) | 0 (0%) | 0 (0%) | 3 (9%) | 28 (82%) | 3 (9%) |
| S2 | 0 (0%) | 8 (24%) | 0 (0%) | 1 (3%) | 0 (0%) | 25 (74%) |
| S3 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 27 (79%) | 7 (21%) |
| S4 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 15 (44%) | 19 (56%) |
| S5 | 0 (0%) | 9 (27%) | 3 (9%) | 2 (6%) | 0 (0%) | 19 (58%) |
| S6 | 0 (0%) | 0 (0%) | 0 (0%) | 3 (9%) | 27 (82%) | 3 (9%) |
| S7 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 33 (100%) |
| overall | 0 (0%) | 17 (7%) | 3 (1%) | 9 (4%) | 97 (41%) | 109 (46%) |

### Length variance

| structure | n | min | max | mean | stddev | warning |
|---|---:|---:|---:|---:|---:|---|
| S1 | 34 | 3 | 25 | 12.65 | 5.21 |  |
| S2 | 34 | 6 | 29 | 15.24 | 5.97 |  |
| S3 | 34 | 4 | 25 | 11.44 | 5.36 |  |
| S4 | 34 | 7 | 44 | 21.09 | 9.28 |  |
| S5 | 33 | 5 | 27 | 14.76 | 6.45 |  |
| S6 | 33 | 3 | 6 | 3.39 | 0.81 |  |
| S7 | 33 | 8 | 33 | 17.67 | 6.85 |  |

## Independent fact-coverage verification

- Dataset-level fact-coverage checks were skipped for this path (they are batch_001-specific). Pass `--coverage` to run them.

## Gate recommendation

**SCALE NEXT BATCH.**

The batch clears every stated scale condition and the realism screens: semantic acceptance, zero exact duplicates, no held-out S8–S10 structure leaks, and no warning-level realism signals.

Machine-readable metrics: `C:\vs code files\ML\parser project\reports\train_metrics.json`. The `realism_warnings` block at the top summarizes every realism finding with offending record ids.
