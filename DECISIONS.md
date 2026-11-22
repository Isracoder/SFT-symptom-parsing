# Orba log parser — decisions record

Goal: fine-tune Qwen3-1.7B to turn messy health logs into strict JSON, and honestly compare it against prompting + grammar-constrained decoding.
Status: pre-build. Nothing coded yet.

---

## 1. Schema (model output)

| field | type | rule |
|---|---|---|
| `cycle_day` | int \| null | day 1 = first bleeding day of current cycle. `null` if not asserted |
| `flow` | enum \| null | `none` / `light` / `medium` / `heavy` / `extremely_heavy`. Period day with no magnitude → `medium`; `null` only if bleeding is not implied; `none` = asserted absence |
| `spotting` | bool \| null | independent of `flow`; both may be set in one log |
| `symptoms` | `[{name, severity}]` | affirmed symptoms only; `severity` is `mild\|moderate\|severe\|null` |
| `denied` | `[name]` | explicitly negated ("no cramps") |
| `no_symptoms_asserted` | bool \| null | `true` only for a global claim; otherwise `null`, never `false` |
| `painkiller` | bool \| null | `true` / `false` (explicitly didn't take) / `null` |
| `supplements` | `[enum]` | closed vocab + `other` |
| `sleep_hours` | float \| null | range → midpoint (§2) |
| `sleep_quality` | enum \| null | `poor` / `fair` / `good` |
| `energy_level` | enum \| null | `low` / `medium` / `high` |
| `mood` | enum \| null | `low` / `neutral` / `good` |
| `hair` | enum \| null | `oily` / `dry` / `growth` / `loss` / `normal` |
| `skin` | enum \| null | `oily` / `dry` / `acne` / `normal` |

Rules
- Always emit every top-level key. `null` = unknown. Missing key = malformed → canonicalized to `null` + counted.
- **Empty extraction object** = every scalar `null`, `symptoms: []`, `denied: []`, `supplements: []`, `no_symptoms_asserted: null`. Use this for adversarial/off-topic/empty input; arrays are never `null`.
- Three states per symptom: affirmed (`symptoms`), negated (`denied`), unmentioned (neither).
- `spotting` is its own signal, not a flow level. "Just spotting" → `spotting: true`, `flow: none`. Spotting with no flow info → `spotting: true`, `flow: null`.
- Extra keys → `additionalProperties: false` → invalid JSON.
- Dropped from output: `date` (app stamps `logged_at`; model must never invent it).
- Scope cut: no drug names, no doses, no temperature, sex, discharge, exercise, water. Say so in README.

**Symptom vocab** (closed, 15): `cramps, headache, bloating, back_pain, nausea, fatigue, breast_tenderness, dizziness, mood_swings, insomnia, diarrhea, constipation, cravings, blood_clots, pelvic_pain`. `acne` moved to `skin`; never encode it twice. Out-of-vocab symptoms are ignored rather than mapped to `other`.

**Supplement vocab** (closed): `iron, vitamin_d, magnesium, b12, folate, calcium, omega_3, probiotic, other`. `other` counts as a **miss**; report how often it fires.

**Severity**: `mild` / `moderate` / `severe` / `null`. No `none` (denial covers it). Unmarked → `null`, never a default.
**Exception**: `blood_clots` uses `null` / `light` / `moderate` / `large`.

---

## 2. Labeling guide (training and gold alike)

**Severity bands** (mechanical):
- mild: light, slight, a bit, some, mild
- moderate: bad, awful, rough, really bad, killing me
- severe: unbearable, crippling, can't move, can't function, worst ever
- range (`mod-sev`) → the **lower** stated band (moderate). If severe were meant, it would be stated.
- no cue at all → `null`. Never default to moderate; that asserts what the text didn't.
- symptoms not mapped downstream (e.g. cravings) → `null`

**Assertion, not mention.** Extract only claims about the user's current state or today's actions.
- "cramps are bad" → extract
- "no cramps" → `denied`
- "should I log cramps or spotting?" → nothing (question)
- "my friend says cramps are the worst" → nothing (other person)
- "I usually get cramps" → nothing for today (habit)

**cycle_day** — set on explicit cycle language (`CD3`, "cycle day 3", "day 3 of my period"), or a bare ordinal in an item that also mentions bleeding/cramps. "Period started N days ago" → **N+1** (started today = 1, yesterday = 2); in menstrual-log context, "started N days ago" refers to the period unless another event is specified. A relative sequence with an identifiable first flow day also counts inclusively (flow before yesterday, then yesterday, then today → day 3). Otherwise `null`. Ambiguity goes to `label_notes`, never the output.

**flow** — never `null` when the text says it is a period day or that there was flow. Magnitude stated → that level; period day with no magnitude → `medium`; menstrual blood clots also imply bleeding and default to `medium` when no magnitude is stated; "no bleeding" → `none`; "just spotting" → `none` + `spotting: true`.
**spotting** — `true` only on the word; `false` only on explicit negation; else `null`.

**painkiller** — `true` for any painkiller/analgesia, including unnamed medicine in a pain context ("medicine no know name", "medicine help pain"); `false` only on explicit negation; else `null`.
**supplements** — absence = unknown, not skipped. "as usual" is filler; the supplement still counts.

**Symptom naming** — lay/clinical terms map to the vocab: dysmenorrhea → cramps; belly/stomach/tummy pain → cramps; literal "pelvic pain" and "private area" pain → pelvic_pain. Out-of-vocab symptoms and irrelevant chatter are ignored; only in-scope facts need to match the card.

**sleep_hours** — any stated quantity counts regardless of relative-time wording ("the night before" counts). Range → midpoint. "about"/"maybe" don't null it. In sleep context, `5-6`, `5-6h`, and `5-6 hours` all mean 5.5; unitless shorthand is valid.
**sleep_quality** — "barely slept", "slept badly", "woke up a lot" → `poor`; "slept well" → `good`; unstated → `null`. `insomnia` only on explicit sleep-disorder wording.

**mood / energy** — "mid" → `medium` (energy) / `neutral` (mood). Anaphora ("same on mood") → `neutral` when the antecedent is mid, else `null`. "Tired" → `fatigue` symptom; "no energy" → `energy_level: low`; "feel like shit" → `mood: low`.
**blood_clots** — "big/large blood clot(s)" → `large`.
**hair / skin** — direct mentions only; otherwise `null`. One value per field per log for this pilot; concurrent attributes (e.g. oily hair + hair loss) are out of scope. `normal` requires an explicit statement.
**emoji** — filler only, never a field.

**contradiction** — statements about different dimensions are not contradictory: "slept 8h but barely slept" → `sleep_hours: 8`, `sleep_quality: poor`. Explicit correction ("actually", "no wait") → later value wins. Genuinely incompatible values in the same slot → `null`.

**cessation** ("cramps gone") → `denied`.
**global negation** ("nothing today", "feeling fine") → `no_symptoms_asserted: true`, empty `symptoms`/`denied`. The field is `true` or `null`; `false` is never produced.
**blank keys** in schema-shaped input → `null`, never `false`/`none`.
**adversarial** → do not comply; the empty extraction object is the gold label.
**empty / off-topic** → empty extraction object.

**label_notes** column in the gold file for genuine ambiguity — separates model error from labeler coin-flips. Not in the schema.

---

## 3. Data — fixed 4-hour plan

**Hierarchy:** an ordinary example has one **structure** (sentence shape), optional **difficulty tags**, and a **fact card** (facts that become its JSON label). Special inputs are a separate type, not structures.

**Exactly 10 structures, with exclusive boundaries:**
1. S1 comma list only; no full sentences.
2. S2 two–four simple declarative sentences; no subordinate clause, contrast, correction, question or command.
3. S3 telegraphic `label: value` items only.
4. S4 one spoken run-on using `and/so` and fillers; no `but/because/although`, correction, question or command.
5. S5 broken-English simple clauses; same exclusions as S2.
6. S6 sparse fragment: one fact, 2–6 words.
7. S7 one question followed by simple assertions; no command, subordinate clause or contrast.
8. S8 declarative with a subordinate clause (`because/although/even though/since/while`); no correction, question or command.
9. S9 explicit correction (`actually/no wait/I mean`) or coordinator contrast (`but`); no subordinate clause, question or command.
10. S10 imperative/request (`Log...`, `Please record...`); no subordinate clause, correction or question.

If an item violates its structure's exclusions, reject or reassign it. S1–S7 must never contain S8–S10 forms.

**Split:** S1–S7 train/validation; S8–S10 held out for gold.
- Train: 55 per S1–S7 = 385, plus 15 specials = **400** (validated card superset; see scope revision below).
- Validation: 5 per S1–S7 = **35**.
- Gold: 18 hand-written items per S8–S10 = 54, plus 6 specials = **60**.
- Specials have `type=adversarial/off_topic/empty`. Adversarial items also have a carrier structure: train uses only S1/S2; gold uses only S8. The injected instruction is noise and never determines the carrier. Off-topic/empty items have no carrier.
- Train specials: 5 adversarial + 5 off-topic + 5 empty. Gold specials: 2 of each.

**Scope revision (2026-11-22, owner decision): the active training target is 250, not 400.** Dataset generation is time-boxed and the deliverable is the base/fine-tuned × free/constrained comparison, which 250 well-audited items answers. The validated 400-card superset in `data/facts/train.jsonl` is retained **unchanged** so the dataset can be scaled later without redesign. The active 250 is defined by the accepted text batches, not by a new card file:
- batch_001: 70 ordinary (10 per S1–S7) — human-accepted.
- batch_002: 140 ordinary (20 per S1–S7) → 30 per structure, 210 cumulative.
- batch_003: 25 ordinary + all 15 train specials = 40 → **250 train**.
- batch_004: 35 validation (unchanged). Gold unchanged at 60 handwritten.
Batch 003's 25 ordinary cards are selected to close coverage gaps in the 210 already selected, so every minimum above (negation ≥40 train, global negation ≥20 train, 4+ symptoms ≥30 train, every field in ≥2 train structures, every enum value, every tag in ≥2 applicable structures) still holds at 250. If a minimum cannot be met by selection, record the shortfall explicitly in the coverage report rather than silently weakening it. Per-structure ordinary counts at 250 are ~33–34 rather than 55; density-band proportions and the S1/S3 cap are preserved.

**Closed tag list:** `implicit_dates`, `negation`, `hedging`, `typos`, `long_multi_symptom`, `duration_ambiguity`, `supplement_naming`, `emotional_language`, `empty_off_topic`, `adversarial`, `contradictory`, `very_short`.

**Required coverage:**
- Every field non-null in ≥2 training structures and ≥1 held-out gold structure.
- Every enum value appears in train and gold; force rare values (`extremely_heavy`, `severe`, `painkiller:false`).
- Negation ≥40 train / 8 gold; global negation ≥20 train / 4 gold; 4+ symptoms ≥30 train / 6 gold.
- Every tag appears in ≥2 structures where applicable. With 60 gold, report only indicative slices for negation, hedging, typos and long multi-symptom.

**Generation:** sample the fact card first; it is the label. Cards may be partial: unspecified scalars become `null`; unspecified lists become `[]`. LLM writes only text and must not add/remove/change in-scope facts. Generate 10–20 items per call. Gold text and labels are hand-written; never LLM-generated or paraphrased.

**Narrative colour must be in-scope-neutral.** Openers and filler about work, family, weather, pets or time of day are welcome and make logs feel real, but they must not imply any in-scope fact the card does not contain. `the neighbors were loud all night` implies disturbed sleep and is a violation on a card with no sleep fact; `the meeting ran long` is neutral and fine. The same bar applies to implied negatives (`just`, `only`, `nothing but`) and to emotional framing that implies an unstated mood, energy or pain state. When in doubt, use colour that asserts nothing about the body. This is a **generation-side conservatism**: because labels come from fact cards rather than from human reading, generated text avoids anything whose correct label cannot be guaranteed. It is deliberately stricter than the labeling rule for real or handwritten inputs below.

**Labeling boundary: self-reported feeling vs. bare reaction marker.** `mood` is extracted from an **explicit self-reported affective state**, not from tone. `feel like shit`, `I feel down`, `feeling really good`, `I'm in a weird mood` all state how the person feels, so they map to `mood` (`low` / `low` / `good` / as applicable) — the person directly told us their state, so this is extraction, not inference. By contrast, **bare discourse markers and reaction fillers do not set `mood` on their own**: `oh come on.`, `nah`, `ugh`, `meh`, `wow`, `okay.`, `whatever` are conversational noise unless accompanied by an explicit feeling statement, and `mood` stays `null`. Emotional wording attached to a symptom expresses **severity**, not mood (`unbearable bloating ugh` → `bloating: severe`, `mood: null`). The same separation applies to `energy_level`: `no energy` / `exhausted` state it, while `phew` or `finally` do not.

**Habitual and temporal qualifiers never change the current-entry label.** The schema describes this log entry only. `hair normal for once` → `hair: normal`; `usually my cramps are worse` → extract today's severity only; `lately I've been tired` with nothing about today contributes no `energy_level` value. The habitual claim itself is out of scope, like weather or work narrative, so it is neither extracted nor treated as a contradiction.

**Gold-set suggestion (owner, handwritten S8–S10):** include a handful of deliberate **distractor** items that probe this boundary, since the generated training data intentionally avoids it — e.g. `oh come on. cramps are awful` with `mood: null` and `cramps: severe`; `hair normal for once` with `hair: normal`; `ugh, no energy at all` with `energy_level: low` and `mood: null`; one item pairing an explicit feeling statement with an unrelated reaction marker to confirm the two are not conflated. These measure whether the fine-tuned model over-extracts from tone, which is the main robustness risk introduced by conservative generation. Keep them a minority of gold (roughly 4–6 of 60) and record their ids in the gold changelog so the slice can be reported separately.

**Density and naturalness:** most real logs are short. Among the 55 ordinary items per training structure, allocate approximately 25 with 2–3 non-null top-level facts, 25 with 4–6, and 5 with 7–9. S6 remains one fact only; 7–9 fact cards are reserved for genuinely long logs, not the default. Apply similar variation to validation and gold. Every structure must vary its opening, fact order, punctuation and length; repeated sentence-initial frames are a rejection signal. A fact card must be verbalized as a plausible human log, not a schema dump.

**List structures are exempt from schema-dump realism warnings, with a density cap.** S1 (comma-separated list) and S3 (colon-separated items) are list-like *by definition*; a list form is their structure, not a realism defect, so auditors must not flag them as schema dumps. To keep them plausible as quick notes, S1 and S3 fact cards are capped at **7 non-null top-level facts** (their 7–9 density band is therefore realised entirely as 7). Prose structures S2, S4, S5 and S7 keep full realism scrutiny, and S6 remains one fact. All other realism checks (phantom facts, severity cues, fact-order constraints, opener repetition) still apply to S1 and S3.

**Quality gates:** pilot 20 items; stop if >2 have semantic mismatches. Critic gives every item an individual accept/reject verdict. No batch auto-accept: you skim and accept every train item, and author/accept every gold item. Zero exact duplicates and zero shared 8-grams between train and gold. Freeze and hash gold before training.

---

## 4. Arms and eval protocol

Four arms = 2×2 (same prompt, same schema, same runtime, same `max_new_tokens`):

|  | free decoding | grammar-constrained |
|---|---|---|
| base 1.7B | strawman baseline | **honest baseline** |
| fine-tuned | format learning alone | **production candidate** |

- Prompt contains schema + enum definitions, **not** an exhaustive synonym list (that would leak the labeling guide).
- **Primary metric**: macro field-level F1 on gold. Secondary: micro F1, invalid-JSON %, schema-valid-but-wrong %, per-category F1 (with `n`), latency p50/p95, cost/1k.
- Array matching: align by `name`; unmatched → 1 FP/FN; matched → compare `severity` separately.
- **Bootstrap** 1,000 resamples at the **record** level → 95% CI on every headline number. n=100 ⇒ expect ±8–10 points. No claim without non-overlapping CIs.
- Categories with `n < 10` labelled "indicative only".
- Latency: batch 1, discard 5 warm-ups, p50/p95 over gold. Same stack for all arms, or the numbers are meaningless.
- Freeze: hash the gold file, put the hash in README. Harness committed **before** first training run.

---

## 5. Canonicalization (decided before any number is computed)

- Parse → normalize → compare structurally. Never string-compare JSON.
- Lowercase enums; map synonyms to the closed vocabs.
- Numeric equality: `5` = `5.0` = `5.00`. Round to 2dp for display only.
- Lists are unordered → sort alphabetically by name before comparing; **dedupe duplicates**.
- Absent key → `null`.
- Extra key → invalid JSON (strict schema).
- `[]` + `no_symptoms_asserted:null` (nothing said) ≠ `[]` + `true` (asserted none).

---

## 6. Training

- Qwen3-1.7B. **Not 4B** (out of scope unless finish early).
- QLoRA via Unsloth: r=16, alpha=32, dropout 0.05, LR 2e-4, 2–3 epochs, max_seq_len 1024.
- **Loss masked to completion tokens only.**
- Early stopping on val loss, patience 1.
- Qwen3 gotcha: disable thinking (`enable_thinking=False`), strip ` thinking` from targets, or JSON parsing breaks.
- Be able to justify every hyperparameter in one sentence.

---

## 7. Infrastructure

- Primary: **Kaggle** (2×T4, 30h/wk, no random disconnects). Fallback: Colab free T4. Rental only if needed (prebuilt Unsloth image, ~€2–4 total).
- Checkpoint adapter + eval results to Drive/HF **continuously**. Pre-download weights.
- One runtime for all inference. Simplest: transformers + 4-bit bnb + outlines / lm-format-enforcer. Note latency is indicative, not production.

---

## 8. Process

- **Label gold before training.** Prevents anchoring on model output and "clarifying" labels to flatter the model.
- **Lock the harness before seeing results.** Prevents silent metric bugs and metric shopping.
- AI writes plumbing; **you own** schema, taxonomy, split logic, labels, canonicalization, metric definitions, interpretation. Rule: if you can't explain a line in one sentence, you don't own it.
- Time: **~10h**, not 6–8. Gates: schema+guide 0.75h → data 1.25h → gold labels 2h → env+training 2h → eval 1.5h → writeup 1.5h → demo 0.5h.

---

## 9. Deliverables

- Repo, README with eval table, HF model card (public, no real logs, state synthetic provenance + closed-vocab limitation), 60s screen-capture demo (unscripted).
- README's most-read section = **where the fine-tune loses**, with numbers and a hypothesis. Honest 0.88 + failure map > suspicious 0.97.
- Pre-committed cut-list if behind at hour 7: drop demo → drop 4th arm → drop per-category plots. Keep gold set, three arms, README table, failure section.

---

## 10. Resolved

- `date` is stamped by the app; never a model field.
- `spotting` is a separate boolean from `flow`; both may co-occur.
- `clots` → `blood_clots` (single field).
- A4 is the single source of truth for symptom names; A1 lists fields only.
- `painkiller`, `sleep_hours`, `no_symptoms_asserted`, `energy_level` stay in schema (energy `low/medium/high`, mood `low/neutral/good`).
- `raw_notes` dropped from the schema (journal text lives in the app, not in the extraction output).
- Severity is a band scale, not one keyword per level.
- **Severity is nullable**; unmarked → `null` (audit A2/A34).
- `cycle_day` set on explicit cycle language or contextual ordinal (A4/A10/A15).
- Contradiction: correction wins, otherwise `null` (A30). F9 is now labelable.
- Dysmenorrhea / belly pain → `cramps` (A11/A21).
- Emoji never asserts a field (A24/A26). Blank keys → `null` (A29).
- `no_symptoms_asserted` is `true` or `null`, never `false` (A33).
- Supplements: absence = unknown; skipped-supplement inputs banned (A36).
- `sleep_quality` added (`poor/fair/good/null`); "slept 8h but barely slept" is quantity + quality, not a contradiction.
- `blood_clots` uses its own scale: `null/light/moderate/large`.
- Compound severity → lower band (`mod-sev` → moderate).
- `flow` defaults to `medium` on a stated period day; `null` only when bleeding isn't implied.
- Unnamed medicine in a pain context → `painkiller: true`.
- Emoji are filler only.
- "mid" → `medium` / `neutral`. "as usual" is filler.
- `hair` and `skin` added as single nullable enums; `acne` moved out of symptoms. One value per field per log.

## 11. Next artifact

- Generate a 20-item pilot from S1–S2 using fact cards. Critic audit, fix the prompt if needed, then scale.
