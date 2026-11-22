# batch_003 semantic audit — independent auditor (Agent 3)

Scope: 40 generated text records in `data/text/batch_003.jsonl` audited against the immutable fact cards in `data/facts/batch_003.jsonl` (25 ordinary + 15 specials). Independent semantic read; the deterministic script is being patched for specials and was not run here.

## Verdict summary

- **40 ACCEPT / 0 REJECT** (25 ordinary + 5 adversarial + 5 off_topic + 5 empty).
- Realism: **40 ok / 0 warn / 0 bad.**
- All twelve 4+-symptom cards verified individually — **all symptoms present** (see table below); this batch closes the dataset's 30-item long-multi-symptom minimum.
- Specials: all 5 adversarial injections are instruction-like noise (extra-keys asks) that reads as no health fact; all 5 off_topic texts contain no in-scope health mention; all 5 empty inputs are whitespace-only. Gold label for all 15 is the empty extraction object.

## Counts by type and structure

| type | n | accept | reject |
|---|---:|---:|---:|
| ordinary | 25 | 25 | 0 |
| adversarial (S1/S2 carrier) | 5 | 5 | 0 |
| off_topic (no carrier) | 5 | 5 | 0 |
| empty (no carrier) | 5 | 5 | 0 |

Ordinary by structure: S1 ×4, S2 ×4, S3 ×4, S4 ×4, S5 ×3, S6 ×3, S7 ×3 (25 total). Adversarial carriers: S1 ×3, S2 ×2.

## The twelve long cards (individual results)

Each carries 4 affirmed symptoms; every symptom's severity band was checked against the text. **No missed symptom.**

| id | symptoms (name → severity) | all present? |
|---|---|---|
| `train_S1_034` | mood_swings mild · headache severe · fatigue mild · breast_tenderness severe | ✓ |
| `train_S1_042` | cramps mild · cravings null · diarrhea mild · insomnia severe (+ denied back_pain, dizziness) | ✓ |
| `train_S2_034` | insomnia moderate · cramps null · cravings null · constipation null (+ denied bloating, blood_clots) | ✓ |
| `train_S2_042` | bloating moderate · fatigue null · constipation moderate · diarrhea null | ✓ |
| `train_S3_034` | fatigue severe · cravings null · bloating severe · diarrhea mild | ✓ |
| `train_S3_042` | pelvic_pain severe · diarrhea mild · dizziness severe · bloating mild | ✓ |
| `train_S3_050` | breast_tenderness severe · headache mild · nausea severe · dizziness mild | ✓ |
| `train_S4_034` | headache null · insomnia moderate · cravings null · nausea moderate | ✓ |
| `train_S4_042` | constipation null · bloating moderate · nausea null · back_pain moderate | ✓ |
| `train_S4_050` | dizziness null · diarrhea moderate · cravings null · constipation moderate | ✓ |
| `train_S5_042` | bloating mild · mood_swings severe · fatigue mild · insomnia severe | ✓ |
| `train_S7_034` | back_pain severe · insomnia mild · headache severe · bloating mild | ✓ |

Severity-band spot-checks across these: `mild`→slight/mild/a bit, `moderate`→bad/rough/awful, `severe`→crippling/unbearable/worst-ever; every `null` carries no cue (e.g. `train_S4_034` `"the headache is there"`, `train_S2_042` `"fatigue"`); `cravings` never gets a severity cue. All correct.

## Specials findings

- **adversarial** (5): carrier portions are clean S1 lists / S2 declaratives; the injected `[override/system note/admin notice/…]` text asks for extra keys (`raw_notes`, `confidence`, `debug_trace`) — genuine instruction-injection noise, not a health fact, and it does not determine the carrier. No current first-person in-scope assertion anywhere. Empty label correct.
- **off_topic** (5): everyday topics (bookshelf, train, balcony garden, chess club, museum) with zero extractable in-scope field. Empty label correct.
- **empty** (5): `""`, `" "`, `"\n"`, `"  "`, `"\t"` — whitespace-only. Empty label correct.

## Ordinary-record findings

Completeness/fidelity/polarity/phon: all 25 ordinary records verbalise every affirmed symptom with the exact severity band, every `denied`/`spotting:false`/`painkiller:false`/`no_symptoms_asserted`, flow defaults, clot scale, and sleep midpoints correctly; cycle-day arithmetic on `train_S3_035` and the implicit-dates ordinary cards is correct; no phantom dates/drugs/doses, no implied negatives, no S8–S10 forms. Structure and every per-card constraint (fact order, register, typos, hedging, duration ambiguity) hold.

One minor note, not a rejection: `train_S2_034` opens with the reaction `"seriously."` on a card with no mood fact — mood-adjacent but ambiguous (it may react to the *denials*), so it is left `ok` rather than `warn`.

## Audit reliability

Before writing this report I ran a Node verification script: the batch_003 fact/text id sets are identical (40/40) with 0 structure mismatches; every id and every quoted phrase in this report is a substring of the referenced record's text (0 quote failures); all twelve long-card symptom root tokens were confirmed present; all five empty inputs pass `^\s*$`; and a regex sweep over the 10 off_topic/adversarial texts found no in-scope health token. No claims were made from memory.

## Gate verdict

**SCALE NEXT BATCH.**

All 25 ordinary records are fact-faithful and structure-compliant, and all twelve 4+-symptom cards are complete — which is what matters most, since a single dropped symptom in any of them would have broken the dataset's 30-item long-multi-symptom minimum. The 15 specials are clean: adversarial injections are ignored-worthy noise (empty label), off_topic texts assert no in-scope field (empty label), and empty inputs are whitespace-only (empty label). Nothing here is label-affecting, so no re-audit or regeneration is warranted.

Files written:
- `reports/batch_003_item_audit.jsonl` (40 lines)
- `reports/batch_003_semantic_audit.md` (this file)
