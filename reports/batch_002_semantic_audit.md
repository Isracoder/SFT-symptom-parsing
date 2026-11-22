# batch_002 semantic audit — independent auditor (Agent 3)

Scope: 140 generated text records in `data/text/batch_002.jsonl` audited against the immutable fact cards in `data/facts/batch_002.jsonl`. This is an independent human-style semantic audit; the deterministic audit already passed 140/140 mechanically. I read every record and every card, then verified every id and every quoted phrase programmatically (see "Audit reliability").

## Verdict summary

- **140 ACCEPT / 0 REJECT.**
- Realism: **137 ok / 3 warn / 0 bad.**
- Completeness (every affirmed symptom verbalised with its exact severity band; every `denied`, `spotting:false`, `painkiller:false`, `no_symptoms_asserted`, flow default, clot scale, sleep midpoint, and `period started N days ago → N+1` arithmetic): **0 errors across 140 records.**
- S8–S10 form leakage (subordinate clause, correction, `but`-contrast, command): **0.**

I did not find a single fact-fidelity, polarity, completeness, structure, or phantom-content error. The mechanical 140/140 is, on the factual dimension, correct after my independent read. The only genuine, script-invisible findings are three narrative-colour/realism gray-zones and a mild templating signal (detailed below). None is label-affecting.

## Per-structure accept/reject

| structure | n | accept | reject | realism ok | realism warn |
|---|---:|---:|---:|---:|---:|
| S1 | 20 | 20 | 0 | 19 | 1 |
| S2 | 20 | 20 | 0 | 19 | 1 |
| S3 | 20 | 20 | 0 | 20 | 0 |
| S4 | 20 | 20 | 0 | 20 | 0 |
| S5 | 20 | 20 | 0 | 20 | 0 |
| S6 | 20 | 20 | 0 | 20 | 0 |
| S7 | 20 | 20 | 0 | 19 | 1 |
| **total** | **140** | **140** | **0** | **137** | **3** |

## Completeness check summary

Every card was read field-by-field against its text. Specifically confirmed for all 140:

- **Affirmed symptoms**: every `symptoms[].name` is verbalised, with the exact severity band (`mild` → light/slight/mild; `moderate` → bad/awful/rough; `severe` → unbearable/crippling/worst ever). All 4+ symptom "long_multi_symptom" cards contain all 4+ symptoms — no silently dropped symptom (the batch-001 failure mode is absent here).
- **Null severity**: every `severity: null` symptom carries no severity or quantity cue (`"pelvic pain"`, `"cramps"`, `"diarrhea"`, `"cravings too"`, `"insomnia is there"`). `cravings` never receives a severity cue, per its constraint.
- **`denied`**: all present, all as explicit current denial/cessation (`"no cramps"`, `"no headache"`, `"clots: none"`), never affirmed elsewhere.
- **`spotting:false`**: 23 cards, all verbalised as `no spotting` / `spotting: no` / `spotng: no`.
- **`painkiller:false`**: 13 cards, all explicit (`no painkiller`, `painkiller: no`, `painkiller - not taken`, `no paynkiller`).
- **`no_symptoms_asserted:true`**: 13 cards, all a global claim (`no symptoms` / `symptoms: none` / `no symptoms at all`), never `false`, never co-affirming a symptom.
- **`flow`**: every period/bleeding statement has a flow value; `flow:none` always carries an explicit no-bleeding cue (`no bleeding`); `flow:medium` on a stated period day.
- **`blood_clots`** stays on its own scale: `light`→"small clots", `moderate`→"moderate clots", `large`→"large blood clots", `null`→bare "clots"/"blood clots".
- **`sleep_hours`** ranges all midpoint correctly (8–9h→8.5, 5–6h→5.5, 6.5–7h→6.75, 3.5–4h→3.75, etc.); single values unchanged.
- **`cycle_day` N+1** arithmetic correct on all 6 `implicit_dates` cards: S1_027 (18→19), S2_027 (19→20), S3_027 ("started today"→1), S4_027 ("yesterday"→2), S5_027 (2→3), S7_027 (4→5). No calendar dates.
- **`supplements`/`hair`/`skin`**: every listed value present (including `other` as "some other supplement"); `acne` never double-encoded into symptoms; no drug names or doses.
- **No phantom content**: no dates, drug names, doses, or numbers not implied by a card; no implied negatives via `just/only/nothing but` (the sole `only` — `"i only slept 4 hours"` — merely emphasises a stated quantity).

## Duplication / templating findings (ids and quotes verified)

**Whole-record duplicates:** none. Exact duplicates 0; near-duplicates at token-Jaccard ≥ 0.85 are 0. No two records are paraphrases of each other.

**Recycled multi-word frames (verified):**

1. `"neutral whatever"` — mood=neutral rendered identically in three records:
   - `train_S1_014` → `"mood neutral whatever"`
   - `train_S2_020` → `"mood neutral, whatever"`
   - `train_S3_020` → `"mood: neutral whatever"`
2. `"meh honestly"` — mood=neutral rendered identically in two records:
   - `train_S4_014` → `"mood is meh honestly"`
   - `train_S5_020` → `"mood is meh honestly"`
3. `"X is there"` — null-severity symptom presence marker reused four times (S4_012, S4_014, S4_018, S4_022).

**Overused field-level phrases** (largely inherent to the closed vocabulary, but thin phrasing variety for the most common fields): `no spotting` in 19 records, `took a painkiller` in 15, `no symptoms` in 11, `mood good` in 10, `no bleeding` in 7. Openers themselves are not overused — every structure shows 20 distinct opening frames.

These are mild signals, not defects: the closed symptom/flow vocab necessarily recycles `no spotting` / `no bleeding` / `took a painkiller`. Worth tightening in batch_003 is the reuse of the exact multi-word emotional frames `neutral whatever` and `meh honestly`, which a fine-tune could memorise as a mood=neutral template.

## Narrative-colour neutrality (the 3 realism warns)

| id | quote (verified) | issue |
|---|---|---|
| `train_S2_030` | `"oh come on. bad dizziness. poor sleep, no spotting."` | Reaction opener `"oh come on"` expresses frustration (negative affect) on a card with **no mood fact**. |
| `train_S1_023` | `"nah, folate - cravings, diarrhea"` | Reaction opener `"nah"` is dismissive/negative-valence on a card with **no mood fact**. |
| `train_S7_014` | `"hair normal for once"` | `"for once"` implies hair is *usually not* normal — a phantom habitual implication; card carries only `hair: normal`. |

These three are `realism: warn`, not rejects: none changes the gold label, and all three openers are prompted by the card's own "reaction/opener" constraint. The remaining reaction openers on mood-less cards (`"yikes"` S1_027, `"no way"` S2_026, `"oh boy"` S4_025) are generic surprise/exclamation markers that do not assert a mood value and are left `ok`. The `meh` openers (S4_014, S5_014, S5_020) are fine because those cards carry `mood: neutral`.

## Audit reliability

Before writing this report I ran a Node verification script over both files: it confirmed the two id sets are identical (140/140), that every text record's `structure` matches its fact card's `structure` (0 mismatches), and that **every id and every quoted phrase in this report exists and is a substring of the referenced record's `text` (0 quote failures)**. No claims were made from memory; the three realism quotes and all duplication quotes were machine-checked as substrings.

## Gate verdict

**SCALE NEXT BATCH.**

The batch is factually and structurally clean: all 140 records verbalise every affirmed and denied fact with correct severity bands, polarity, flow/clot/sleep/cycle-day conventions, and none leak S8–S10 forms. The only findings my independent read surfaces are three label-neutral narrative-colour gray-zones (two mood-implying reaction openers on mood-less cards, one `"for once"` phantom implication) and mild templating (`neutral whatever`, `meh honestly`, and heavy `no spotting`/`took a painkiller` reuse). These are forward-looking polish items, not errors that poison the training labels, so a re-audit or regeneration is not warranted. Batch_003 should vary reaction openers so they assert nothing about the body when the card has no mood/energy fact, and diversify the mood=neutral and spotting=false phrasings rather than repeating the exact frames flagged above.

Files written:
- `reports/batch_002_item_audit.jsonl` (140 lines)
- `reports/batch_002_semantic_audit.md` (this file)
