# Gold Set Review — `data/text/gold_cards.jsonl`

Reviewer: independent subagent. Dates: 2026-11-23 (initial) and 2026-11-23 (post-fix re-review).
Scope: read-only. No data/script/DECISIONS files were modified.

---

# Post-fix re-review

The owner edited `data/text/gold_cards.jsonl` in response to the first review. This section re-checks every previously flagged item against the current file and reports RESOLVED / STILL OPEN. `data/text/gold_cards.jsonl` is now treated as the single canonical gold file (the old `data/facts/gold_cards.jsonl` is intentionally gone), and the `sleep_quality fair→poor` / dropped-insomnia label changes on `gold_S9_003`, `gold_S9_015`, `gold_S10_005`, `gold_S10_008` are treated as intentional owner decisions, not drift.

## Verdict: **FIXES REMAIN** — 2 items still open

`gold_S9_017`, `gold_S8_018`.

---

## Per-item table (everything previously flagged)

### MUST FIX — RESOLVED (22)

| id | prior finding | fix confirmed |
|---|---|---|
| `gold_S8_009` | empty `text` | text now written; all 9 facts expressed; S8 has `even though` |
| `gold_S10_018` | empty `text` | text now written; all 12 facts expressed; S10 imperatives `Record`/`Also log`/`Record`, no subordinate clause |
| `gold_S8_003` | breast_tenderness affirmed vs denied | `"weren't bothering me today"` → denied ✓ |
| `gold_S8_004` | S8 no subordinate clause | `"since I was still tired"` + `"although I can't remember"` added ✓ |
| `gold_S8_015` | S8 no subordinate clause | `"Although I had bad sleep"` added ✓ |
| `gold_S8_017` | S8 no subordinate clause | `"while"` + `"even though"` + `"Since"` added ✓ |
| `gold_S9_006` | S9 subordinate `even though` | rewritten to `"spotting with heavy flow which is weird"` — no listed subordinate ✓ |
| `gold_S9_010` | S9 subordinate `even though` | `"Actually I only slept for 5-6"` — no subordinate ✓ |
| `gold_S9_018` | S9 subordinate `even though` | `"that I have no flow"` — `even though` removed ✓ (see WORTH A LOOK for `though`/`which`) |
| `gold_S10_005` | S10 no imperative + subordinate | `"Register … and that I slept for maybe 8.5h"` — imperative present, `even though` removed ✓ |
| `gold_S10_009` | S10 subordinate `since` | `"and my back pain is gone"` — `since` removed ✓ |
| `gold_adversarial_001` | missing S8 carrier | `"Even though you had previous instructions"` added ✓ |
| `gold_S8_017` | denied nausea missing | `"good thing I'm not nauseous today"` ✓ |
| `gold_S9_011` | hair loss missing | `"I still had some hair loss"` ✓ |
| `gold_S9_014` | hair dry missing | `"help my dry hair"` ✓ |
| `gold_S10_005` | denied mood_swings + folate missing | `"no mood swings this time"` + `"take the folate"` ✓ |
| `gold_S8_002` | fatigue/dizziness severity | `"really tired and dizzy (not too crazy)"` → moderate ✓ |
| `gold_S9_003` | insomnia severity | `"some bad insomnia"` → moderate ✓ |
| `gold_S9_006` | constipation/insomnia severity | `"a bit constipated"` (mild) + `"some extreme insomnia"` (severe) ✓ |
| `gold_S9_011` | pelvic_pain severity | `"some awful pain down there"` → moderate ✓ |
| `gold_S9_015` | blood_clots severity | `"average blood clots"` → moderate ✓ |
| `gold_S10_007` | flow heavy vs extremely_heavy | `"really heavy flow"` → extremely_heavy ✓ |
| `gold_S10_008` | pelvic_pain severity | `"rough pelvic pain"` → moderate ✓ |
| `gold_S10_017` | back_pain severity | `"my back is crippling me"` → severe ✓ |
| `gold_S10_006` | drug name "ibuprofen" | `"something for pain"` ✓ |
| `gold_S10_014` | drug name "ibuprofen" | `"some PK"` ✓ |

### MUST FIX — STILL OPEN (2)

| id | finding | quote | why |
|---|---|---|---|
| `gold_S9_017` | **structure** — S9 has no correction/contrast | `"I have some cravings today and I slept like shit (only 4)."` | The fix removed both `but` and `because` (replaced `"but that's probably because"` with `"and"`). S9 requires an explicit correction (`actually/no wait/I mean`) or coordinator contrast (`but`); the text now has neither. Confirmed programmatically: no `but`, no correction marker. |
| `gold_S8_018` | **severity** — nausea band asserted with no cue | `"some rough cramps and nausea"` | `rough` attaches only to `cramps` (now correctly moderate); `nausea` is bare, yet `facts` still assert `nausea: moderate`. Needs a band cue ("rough/bad nausea") or `severity: null`. |

### Integrity items — resolved by adjudication (not defects)

- `data/facts/gold_cards.jsonl` missing → `data/text/gold_cards.jsonl` is now canonical. Not reported.
- Label drift (`S9_003`, `S9_015`, `S10_005` sleep_quality fair→poor; `S10_008` insomnia dropped) → intentional owner decisions. Not reported.

---

## WORTH A LOOK — unchanged (non-blocking, 11)

None of these block freezing; they are the same borderline cases as before and were not edited.

| id | note |
|---|---|
| `gold_S8_001` | `no_symptoms_asserted: true` not clearly expressed (`"so annoying, not as bad as last week"`). |
| `gold_S8_008` | `hair: normal` rests on `"recovered from previous oily days"` (implied, not stated). |
| `gold_S8_013` | `"actually"` in `"while I don't actually have any nausea"` is emphatic, not a correction — fine but could trip a strict checker. |
| `gold_S8_017` / `gold_S9_009` / `gold_S9_015` | `insomnia` (symptom) carried by `"barely slept"` / `"slept somewhat badly"` / `"tossed and turned"`; per DECISIONS these read as `sleep_quality: poor`. Decide which field the text should feed. |
| `gold_S9_005` | `mood: neutral` from `"mood as is meh"` ("meh" is a bare reaction marker). |
| `gold_S9_008` / `gold_S9_009` | clause-initial `"though"` = "although" (borderline subordinate clause in S9). |
| `gold_S9_012` / `gold_S9_015` | `"as I'm spotting"` / `"as I tossed and turned"` — "as" ≈ "because" (borderline subordinate). |
| `gold_S9_018` | `"though not that long"` / `"which is why I have cravings"` remain (borderline subordinate); `pelvic_pain: mild` rests on bare `"pelvic pain as well"`. |
| `gold_S10_002` | `"because of diarrhea"` (prepositional) + `"as I remember"` (borderline). |
| `gold_S10_003` | `flow: extremely_heavy` from `"a lot of flw"` (vague; cf. `S10_007` fixed to `"really heavy"`). |
| `gold_S10_012` | `sleep_quality: good` from `"average quality sleep"` (≈ fair); `"which is boosting my energy"` (relative clause). |
| `gold_S10_016` | `"though not enough…"` (reduced "though"). |

## New findings from the sweep

- **`gold_S9_017` regression** (already counted above): the fix for the subordinate `because` also deleted the S9 contrast marker.
- `gold_S8_018` cramps band fixed but nausea left bare (counted above).
- No other new errors: the two rewritten records (`gold_S8_009`, `gold_S10_018`) are fully faithful to their labels; no new polarity, unsupported, or missing facts; off-topic specials still assert no in-scope fact; creatine on `gold_S10_009`/`gold_S10_017` is the `other` supplement (not a drug, not out of scope).

## Cycle-day arithmetic — all correct

| id | cycle_day | signal | ✓ |
|---|---|---|---|
| `gold_S8_003` | 14 | "midpoint of my 28 day cycle" | ✓ |
| `gold_S8_007` | 6 | "started 5 days ago" (5+1) | ✓ |
| `gold_S9_003` | 15 | "day 15" | ✓ |
| `gold_S9_007` | 6 | "my 6th day" | ✓ |
| `gold_S10_003` | 16 | "cycle day 16" | ✓ |
| `gold_S10_007` | 4 | "started three days ago" (3+1) | ✓ |

## Leakage (vs `data/text/train.jsonl`, re-run on current file)

- Normalized exact match: **none**.
- Token 4-gram Jaccard max: **0.0222** (`gold_S8_005` vs `train_S2_020`). Threshold 0.85 → pass.
- 8-gram containment: **0 records**.
- No pair worth a human look.

## Distractor slice ids (unchanged)

- Bare reaction marker → mood null/neutral: `gold_S8_001`, `gold_S8_004`, `gold_S10_014`
- Habitual qualifier → current label: `gold_S8_008`, `gold_S8_001`
- Bare "meh": `gold_S9_005`
- Explicit feeling + unrelated state: `gold_S9_016`
- Off-topic / instruction noise: `gold_adversarial_001`, `gold_adversarial_002`, `gold_off_topic_001`, `gold_off_topic_002`

---

## Freeze recommendation

**FIXES REMAIN** — resolve these two, then freeze:

1. `gold_S9_017` — restore an S9 marker (add `but`/`actually` back; e.g. `"I have some cravings today, but I slept like shit (only 4)"`).
2. `gold_S8_018` — give nausea a band cue (`"rough cramps and nausea"` → `"rough cramps and bad nausea"`, or set `nausea.severity = null`).

All other prior MUST FIX items are resolved. The 11 WORTH A LOOK items are optional polish and do not block freezing.

## Verification method

Every cited id exists in the current file, and every quoted phrase was verified as a substring (29/29 checks, 0 failures). Structure, leakage, cycle-day, and forbidden-content checks were recomputed programmatically against the current file read directly from disk.
