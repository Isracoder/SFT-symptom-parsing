# AUDIT — family coverage, overlap, label ambiguity

Verdict up front: **the 10 candidate families are ~4 distinct skeletons, cover 4 of 11 fields cleanly, and leave 1 of 12 hard-case categories with zero families.** As written, F9 is unlabelable and F5 is unlabelable on its main fact. Family-level split as designed is therefore weaker than it looks: holding out one family usually leaves its skeleton in train.

Coverage cells: `●` asserted cleanly · `◐` present but labeler-dependent · `○` token present, not asserted · `·` absent.

## 1. Coverage matrix

| field | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | F10 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `cycle_day` | · | ◐ | ● | ◐ | · | · | ● | · | · | · | **thin** — 2 clean, both telegraphic |
| `flow` | ◐ | ◐ | ◐ | · | · | · | · | · | · | ○ | **zero** — never states a level |
| `spotting` | · | · | · | · | · | · | · | · | · | ○ | **zero** |
| `symptoms` | ● | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | · | ◐ | ○ | adequate names; clean severity rare |
| `denied` | · | · | · | · | · | · | · | · | · | · | **zero** |
| `no_symptoms_asserted` | · | · | · | · | · | · | · | ○ | · | ○ | **zero** (`true` never produced) |
| `painkiller` | ● | · | ● | ● | ◐ | ● | ◐ | · | · | · | adequate |
| `supplements` | · | ● | · | · | ◐ | · | ◐ | · | · | · | **thin** — 1 clean, habitual |
| `sleep_hours` | · | ◐ | ● | ◐ | · | ● | · | · | ◐ | · | adequate (thin: 2 clean) |
| `energy_level` | · | · | · | ◐ | · | · | · | · | · | · | **thin** |
| `mood` | · | ◐ | · | ◐ | · | ◐ | · | · | · | · | **thin** — 0 clean |

Not a schema field, but blocking: **enum values never exercised anywhere** — `flow` all 5; `spotting` true *and* false; `painkiller: false`; 8 of 9 supplements; `energy` low/high; `mood` low/good; `other` for both vocabs. `extremely_heavy` and `severe` have no forced minimum and no natural carrier.

## 2. Category coverage

| # | category | families | flag |
|---|---|---|---|
| 1 | implicit dates | F2, F4 | both resolve to `null` under §2's rule → tests null-emitting, not the phenomenon |
| 2 | negation | — | **ZERO** |
| 3 | hedging | F2, F4 | ok (2), one form only ("think/approx") |
| 4 | typos | F4, F5 | **thin** — neither contains a misspelling; casing + grammar only |
| 5 | long multi-symptom | F4 | **thin** (1); max 2 symptoms anywhere |
| 6 | duration/quantity ambiguity | F1, F2, F4, F9 | ok (4), but effectively sleep-hours-only |
| 7 | supplement naming | F2 | **thin** (1), literal "iron supplement" |
| 8 | emotional language | F2, F4, F6, F9 | ok (4) |
| 9 | empty/off-topic | F10 | **thin** (1); and F10 is a schema-meta question, not generic chit-chat |
| 10 | adversarial | F8 | **thin** (1), one injection shape |
| 11 | contradictory | F9 | **thin** (1) + **unlabelable** |
| 12 | very short | F5, F9 | **thin** — F9 is contradiction; one real terse family |

8 of 12 fail the ≥2-family rule; **negation has none.** With 100 gold items across 4 real skeletons and 12 categories, most per-category `n` will land under the n<10 "indicative only" line.

## 3. Skeleton overlap

`=` same skeleton · `~` same skeleton, different vocabulary/formatting · `≠` genuinely different.

| | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | F10 |
|---|---|---|---|---|---|---|---|---|---|
| **F1** | ≠ | ~ | ≠ | = | ~ | ~ | ≠ | ≠ | ≠ |
| **F2** | | ≠ | **=** | ≠ | ≠ | ≠ | ≠ | ≠ | ≠ |
| **F3** | | | ≠ | ≠ | ≠ | **=** | ≠ | ≠ | ≠ |
| **F4** | | | | ≠ | ≠ | ≠ | ≠ | ≠ | ≠ |
| **F5** | | | | | ≠ | ~ | ≠ | ≠ | ≠ |
| **F6** | | | | | | ≠ | ≠ | ≠ | ≠ |
| **F7** | | | | | | | ≠ | ≠ | ≠ |
| **F8** | | | | | | | | ≠ | **=** |
| **F9** | | | | | | | | | ≠ |

Duplicates in disguise, worst first:

1. **F3 = F7.** Both are `label: value` telegraphese; F3 is F7 with abbreviations and periods instead of dashes. Zero structural novelty. Splitting one to gold tests nothing.
2. **F2 = F4.** Same narrative frame: [time marker] → [symptom + intensity] → [took painkiller] → [sleep quantity] → [energy/mood]. F4 adds fillers and lowercase. This is the most costly duplicate because it is the *only* carrier of `sleep_hours`, `energy_level`, `mood`, `supplements`, and both are needed for the "adequate" verdicts above. Holding out one still trains the other.
3. **{F1, F5, F6} ⊂ enumeration.** F5 is F1 with grammar stripped; F6 is F1 plus emoji plus a sleep clause. Emoji changes tokenization, not structure.
4. **F8 = F10.** Different inputs, identical gold (all-null). They teach one behaviour: emit nulls.

**Effective distinct skeletons: 4.** {F1,F3,F5,F6,F7} enumeration · {F2,F4} narrative · {F8,F10} null · {F9} single-clause contradiction. F9 is a skeleton with one fact, so it carries no extraction skill. The family split can only ever be a ≤4-way generalization test, and each held-out skeleton gets ~25 gold items.

## 4. Label ambiguities (seed phrases)

| # | seed | phrase | competing readings | field(s) |
|---|---|---|---|---|
| A1 | F1 | "some light cramps" | mild (light=severity) / `flow: light` / moderate (light is a flow word, not a severity word) | `symptoms[].severity`, `flow` |
| A2 | F1 | "a headache" | moderate (§2 band rule) / severity unknown — no such value exists, so every bare symptom is a forced guess | `symptoms[].severity` |
| A3 | F1 | "took a painkiller" | true / null ("a painkiller" is too vague to be a real assertion) | `painkiller` |
| A4 | F2 | "the second day of my period" | `2` (ordinal + "of my period" is explicit) / `null` (§2: ordinal day = ambiguous) | `cycle_day` |
| A5 | F2 | "my period" | `flow: null` (no level stated) / `medium` (bleeding implied by "period") | `flow` |
| A6 | F2 | "some cravings" | mild ("some") / moderate (unmarked) | `symptoms[].severity` |
| A7 | F2 | "They didn't bother me much" | severity mild (attenuator) / `mood: good` (unbothered) / ignore as chatter | `symptoms[].severity`, `mood` |
| A8 | F2 | "8 hours approximately" | `8.0` / `null` (hedged quantity) | `sleep_hours` |
| A9 | F2 | "as usual" | iron logged (taken today) / nothing (habit, not today's event) | `supplements` |
| A10 | F3 | "CD3" | `3` / `null` (abbreviation, not an explicit statement) | `cycle_day` |
| A11 | F3 | "Dysmenorrhea" | cramps / pelvic_pain / both | `symptoms[].name` |
| A12 | F3 | "mod-sev" | moderate / severe / invalid range | `symptoms[].severity` |
| A13 | F3 | "CD3" (alone) | `flow: null` / `medium` (day 3 of a cycle implies bleeding) | `flow` |
| A14 | F3 | "Analgesia taken" | true / null (drug class, not an act the user reports) | `painkiller` |
| A15 | F4 | "its day three" | `3` / `null` (§2: ambiguous day; app context is not explicit text) | `cycle_day` |
| A16 | F4 | "really killing me" | severe / moderate ("bad/awful"→moderate, "unbearable"→severe; this sits between) | `symptoms[].severity` |
| A17 | F4 | "earlier" | true (today) / null (could be yesterday) | `painkiller` |
| A18 | F4 | "like five hours maybe the night before" | `5.0` / `null` (not last night) / range midpoint | `sleep_hours` |
| A19 | F4 | "energy is mid" | medium / low | `energy_level` |
| A20 | F4 | "same on mood" | neutral (mapped from "mid") / low / `null` (no mood word used; "same" refers to energy) | `mood` |
| A21 | F5 | "belly pain" | cramps / pelvic_pain / other | `symptoms[].name` |
| A22 | F5 | "head pain, belly pain" | moderate (unmarked) / severe ("pain" is stronger than "ache") | `symptoms[].severity` |
| A23 | F5 | "medicine no know name" | true (took something) / null (can't classify) / `supplements: other` | `painkiller`, `supplements` |
| A24 | F6 | "😭😭" | `mood: low` / severer severity / no field (pure emphasis) | `mood`, `symptoms[].severity` |
| A25 | F6 | "cramps so bad" | moderate ("bad") / severe (intensified) | `symptoms[].severity` |
| A26 | F6 | "😴" | energy low / fatigue symptom / no field | `energy_level`, `symptoms` |
| A27 | F7 | "meds: ibuprofen" | `painkiller: true` / `supplements: other` / both | `painkiller`, `supplements` |
| A28 | F7 | "clotting: some" | `blood_clots` mild / moderate / not a symptom at all ("some" is a count, not a band) | `symptoms[].severity` |
| A29 | F7 | *(structure)* unlisted keys | null (not stated) / `false`/`none` (a form's blanks read as negatives) | `flow`, `spotting`, `denied`, `no_symptoms_asserted` |
| A30 | F9 | "slept 8h but also barely slept" | `8.0` / `null` / ~1–2 (last clause wins) | `sleep_hours` |
| A31 | F9 | "barely slept" | insomnia symptom / sleep quantity only | `symptoms` |
| A32 | F10 | "should I pick cramps or spotting?" | all-null (question) / extract both / extract one | `symptoms`, `spotting` |
| A33 | F10 | "how does this app work?" | all-null (agreed) — but `no_symptoms_asserted` = null vs false is a live split | `no_symptoms_asserted` |

Cross-cutting (affects every item, not one seed):

| # | issue | readings | field(s) |
|---|---|---|---|
| A34 | unmarked symptom | always moderate (§2) — but "moderate" is an assertion the text never made, and no unknown value exists | all `symptoms[].severity` |
| A35 | mention vs assertion | only codified for adversarial/off-topic; not for quoted, hypothetical, or meta mentions inside otherwise-real logs | all fields |
| A36 | supplement negation | "didn't take my iron" ≡ "no iron mentioned": `[]` cannot distinguish skipped from unknown, and there is no per-supplement bool | `supplements` |
| A37 | negation boundary | "no cramps" → `denied` · "nothing today" → `no_symptoms_asserted: true` · "not much going on" → undefined | `denied`, `no_symptoms_asserted` |
| A38 | doc contradiction | §2 routes ambiguous cycle day to `raw_notes`; §10 removed `raw_notes`. A4/A15/A10 point at a field that does not exist | `cycle_day` (labels + `label_notes` process) |
| A39 | severity on non-banded fields | `cravings`, `blood_clots`, `diarrhea` etc. take a mild/moderate/severe band that has no meaning for a count or an urge | `symptoms[].severity` |
| A40 | severity ranges | §2 defines a midpoint rule for `sleep_hours` only; A12 has no legal midpoint (`mod-sev` cannot be `moderate.5`) | `symptoms[].severity` |

**Blockers:** F9 cannot be gold-labeled (no contradiction policy, A30/A31). F5 cannot be gold-labeled on its main fact (A21/A23 — `belly pain` and unknown-name medicine have no single correct mapping). Both must be resolved in DECISIONS before either family enters train *or* gold.

## 5. Missing families

Each closes a zero/thin cell. Register + facts only.

| ID | register | must cover | closes |
|---|---|---|---|
| M1 | one-fact terse status | `cycle_day` + 1 symptom + nothing else; 3–6 words | very short (12), sparse logs |
| M2 | product/pad-change log | all 5 `flow` values, `flow: none`, `spotting` true and false, spotting-only with `flow: null`, flow+spotting together | `flow`, `spotting` |
| M3 | reassurance / "all clear" note | `denied` list (1 and 3 items), cessation, affirmed+denied in one item, boundary to global claim | `denied`, negation (2) |
| M4 | one-line daily check-in | `no_symptoms_asserted: true`, plus the `false`/`null` contrast; true while `cycle_day` is set | `no_symptoms_asserted` |
| M5 | wellness/routine log | all 9 supplement values incl. `other`, multi-supplement, skipped supplement (see A36) | `supplements`, supplement naming (7) |
| M6 | affect rating | `energy_level` and `mood` all 3 values each, stated separately so they don't collapse (A20) | `energy_level`, `mood` |
| M7 | rambling symptom dump | 4–6 symptoms, mixed severities, 1 denial, 1 hedged | long multi-symptom (5) |
| M8 | truly empty / near-empty | zero-content and one-token input; distinct from a schema-meta question | empty/off-topic (9) |
| M9 | misspelling register | real misspellings over an otherwise-known skeleton (A4/F5 are grammar/casing, not typos) | typos (4) |
| M10 | implicit-duration register | timing without a numeral ("a few days in", "since yesterday"), resolved to `null` by rule | implicit dates (1) |

M1–M10 brings the set to 20, matching the 15–20 target. Note M3/M4/M8 still need the A37 boundary written down first; M5 is blocked by A36 unless the schema accepts "absence = unknown".

## 6. Share guidance

600 train items at 60/family overweights the trivial shapes.

| family | why | cap |
|---|---|---|
| F7 notes list | schema echo — input names the output keys; teaches key→enum mapping, not extraction | **≤5%** |
| F3 clinical | field-label telegraphese = F7 with abbreviations | **≤8%**, and not in addition to F7's budget |
| F1 comma list | flat enumeration, no syntax; learner sees each fact pre-segmented | **≤10%** |
| F5 weak English | short bare list; adds grammar noise, not structure | **≤8%** |
| F8 adversarial | one label (all-null), zero field content | **≤2%** — does not count as coverage of anything |
| F10 off-topic | same all-null target, plus schema words to ignore | **≤3%** |
| F6 emoji | F1 + emoji + sleep; emoji must never be the only signal for a field | **≤8%** |
| F9 contradictory | **0%** until A30 and a contradiction rule exist | 0 |

Combined cap: structured/echo families (F1+F3+F5+F7) **≤25%**; null-output families (F8+F10) **≤5%**. F2 and F4 are the load-bearing narrative pair — uncapped, but count them as **one** family for splitting, hold both out together, and expect their absence to cost `sleep_hours`/`energy`/`mood` recall, which is the honest test.
