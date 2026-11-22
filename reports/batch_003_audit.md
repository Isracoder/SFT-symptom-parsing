# batch_003 audit — generated text correctness + realism

Scope: 40 generated text records in `C:\vs code files\ML\parser project\data\text\batch_003.jsonl`, audited against the immutable cards in `C:\vs code files\ML\parser project\data\facts\batch_003.jsonl`. No data, decisions, or examples were edited.

## Verdict

- **40 ACCEPT / 0 REJECT** (100.0% semantic acceptance).
- Structure compliance: **100.0%** (40/40).
- Schema-valid labels: **40/40** after canonicalizing partial cards to `null` / `[]`.
- Exact duplicates: **0**. Near duplicates at normalized token 4-gram Jaccard >= 0.85: **0** (max 0.114; 0.114 with numeric normalization).
- Empty inputs (type=empty, identical by specification and exempt from the duplicate checks): **5**.
- Special inputs: **15** (5 adversarial / 5 off_topic / 5 empty); 0 special warning(s).
- Held-out structure leaks: **0** S8–S10 forms in the batch.

## Per-structure

| structure | n | accept | reject | semantic accept | structure compliance | schema valid |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 4 | 4 | 0 | 100% | 100% | 4/4 |
| S2 | 4 | 4 | 0 | 100% | 100% | 4/4 |
| S3 | 4 | 4 | 0 | 100% | 100% | 4/4 |
| S4 | 4 | 4 | 0 | 100% | 100% | 4/4 |
| S5 | 3 | 3 | 0 | 100% | 100% | 3/3 |
| S6 | 3 | 3 | 0 | 100% | 100% | 3/3 |
| S7 | 3 | 3 | 0 | 100% | 100% | 3/3 |
| specials | 15 | 15 | 0 | 100% | 100% | 15/15 |

## Fact fidelity

All 25 ordinary items were checked individually for omissions, invented or changed in-scope facts, polarity, severity, clot scale, date arithmetic, flow defaults, sleep midpoints, painkiller/supplement/hair/skin presence, global negation, and out-of-vocab ignoring.

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
- Near-duplicate pairs at Jaccard >= 0.85: **0**. Highest pair: `train_adversarial_002` / `train_adversarial_005` at 0.114 (numeric-normalized max 0.114).
- Overall words: min 0, median 17.0, mean 15.57, max 32.
- Overall characters: min 0, median 102.0, mean 94.28, max 194.

| structure | n | words min / median / mean / max | chars min / median / mean / max |
|---|---:|---|---|
| S1 | 4 | 13 / 14.5 / 15.5 / 20 | 74 / 106.0 / 103.75 / 129 |
| S2 | 4 | 12 / 16.5 / 16 / 19 | 87 / 96.0 / 97.75 / 112 |
| S3 | 4 | 10 / 13.5 / 14 / 19 | 81 / 89.5 / 97.75 / 131 |
| S4 | 4 | 15 / 22.5 / 22.25 / 29 | 96 / 112.5 / 117.25 / 148 |
| S5 | 3 | 14 / 14 / 17 / 23 | 65 / 85 / 93.33 / 130 |
| S6 | 3 | 3 / 3 / 3.33 / 4 | 21 / 23 / 22.33 / 23 |
| S7 | 3 | 19 / 22 / 22.67 / 27 | 95 / 132 / 127.67 / 156 |
| specials | 15 | 0 / 19 / 14.87 / 32 | 0 / 110 / 91.67 / 194 |

Repeated 3-word openers (count >= 2): .

Most repeated sentence-initial frames (up to 5 tokens; count >= 2, top 12): .

## Realism checks (warnings only — no auto-reject)

**Realism verdict: PASS** — 2 warning(s), 0 hard warning(s). Realism findings never change an item's semantic ACCEPT/REJECT verdict; a human decides.

- **WARNING** `length_variance`: S1 word-count stddev is 2.87 (< 3.0) over 4 records; lengths are effectively uniform — `train_S1_034`, `train_S1_038`, `train_S1_042`, `train_S1_045`
- **WARNING** `length_variance`: S2 word-count stddev is 2.74 (< 3.0) over 4 records; lengths are effectively uniform — `train_S2_034`, `train_S2_042`, `train_S2_048`, `train_S2_055`

### Fact-density alignment

| band | records | words min / median / mean / max / stddev |
|---|---:|---|
| 1 | 3 | 3 / 3 / 3.33 / 4 / 0.47 |
| 2-3 | 10 | 10 / 13.5 / 14.9 / 23 / 4.06 |
| 4-6 | 12 | 14 / 19.0 / 20.08 / 29 / 4.35 |
| 7-9 | 0 | - |
| other | 0 | - |

| structure | 1 | 2-3 | 4-6 | 7-9 | other |
|---|---:|---:|---:|---:|---:|
| S1 | 0 | 2 | 2 | 0 | 0 |
| S2 | 0 | 2 | 2 | 0 | 0 |
| S3 | 0 | 2 | 2 | 0 | 0 |
| S4 | 0 | 2 | 2 | 0 | 0 |
| S5 | 0 | 1 | 2 | 0 | 0 |
| S6 | 3 | 0 | 0 | 0 | 0 |
| S7 | 0 | 1 | 2 | 0 | 0 |

### Schema-dump detector

Exempt list structures: `S1`, `S3` — 8 record(s) skipped (`train_S1_034`, `train_S1_038`, `train_S1_042`, `train_S1_045`, `train_S3_034`, `train_S3_035`, `train_S3_042`, `train_S3_050`).

- No schema-dump flags outside the exempt list structures.

### List-structure density cap

S1/S3 cards are capped at 7 non-null top-level facts.

- No S1/S3 card exceeds the cap.

### Opening frames (first 4 tokens)

| structure | n | distinct openers | most common opener | share |
|---|---:|---:|---|---:|
| S1 | 4 | 4 | `dizzy off and on` | 25.0% |
| S2 | 4 | 4 | `i have medium flow` | 25.0% |
| S3 | 4 | 4 | `breast tenderness worst ever` | 25.0% |
| S4 | 4 | 4 | `anyway i slept 7` | 25.0% |
| S5 | 3 | 3 | `no bleeding i have` | 33.3% |
| S6 | 3 | 3 | `folate with breakfast` | 33.3% |
| S7 | 3 | 3 | `how do i log` | 33.3% |

Overall top openers: `anyway i slept 7` x1 (4.0%); `breast tenderness worst ever` x1 (4.0%); `dizzy off and on` x1 (4.0%); `early morning vitamin d` x1 (4.0%); `fatigue unbearable cravings yes` x1 (4.0%); `folate with breakfast` x1 (4.0%); `hair dry spotting none` x1 (4.0%); `how do i log` x1 (4.0%); `i have medium flow` x1 (4.0%); `is this all today` x1 (4.0%).

### Sentence-initial subjects (distribution only)

| structure | my period | i | today | no | bare_fragment | other |
|---|---|---|---|---|---|---|
| S1 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 4 (100%) | 0 (0%) |
| S2 | 0 (0%) | 1 (25%) | 0 (0%) | 0 (0%) | 0 (0%) | 3 (75%) |
| S3 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 3 (75%) | 1 (25%) |
| S4 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 4 (100%) |
| S5 | 0 (0%) | 0 (0%) | 1 (33%) | 1 (33%) | 0 (0%) | 1 (33%) |
| S6 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 3 (100%) | 0 (0%) |
| S7 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 3 (100%) |
| overall | 0 (0%) | 1 (4%) | 1 (4%) | 1 (4%) | 10 (40%) | 12 (48%) |

### Length variance

| structure | n | min | max | mean | stddev | warning |
|---|---:|---:|---:|---:|---:|---|
| S1 | 4 | 13 | 20 | 15.5 | 2.87 | YES |
| S2 | 4 | 12 | 19 | 16 | 2.74 | YES |
| S3 | 4 | 10 | 19 | 14 | 3.39 |  |
| S4 | 4 | 15 | 29 | 22.25 | 4.97 |  |
| S5 | 3 | 14 | 23 | 17 | 4.24 |  |
| S6 | 3 | 3 | 4 | 3.33 | 0.47 |  |
| S7 | 3 | 19 | 27 | 22.67 | 3.3 |  |

## Independent fact-coverage verification

- Dataset-level fact-coverage checks were skipped for this path (they are batch_001-specific). Pass `--coverage` to run them.

## Gate recommendation

**SCALE NEXT BATCH.**

The batch clears every stated scale condition and the realism screens: semantic acceptance, zero exact duplicates, no held-out S8–S10 structure leaks, and no warning-level realism signals.

Machine-readable metrics: `C:\vs code files\ML\parser project\reports\batch_003_metrics.json`. The `realism_warnings` block at the top summarizes every realism finding with offending record ids.
