# Batch 001 — two-layer audit adjudication

Scope: 70 records in `data/text/batch_001.jsonl` against immutable cards in `data/facts/batch_001.jsonl`.

Two independent audit layers were run and **disagreed**. This file records how every disagreement was resolved. Neither layer is treated as authoritative on its own.

| Layer | Method | Result |
|---|---|---|
| Agent 3 (LLM, `beam-free`) | per-record semantic reading | 70 ACCEPT / 0 REJECT, realism 69 ok / 1 warn |
| `scripts/audit_batch_001.py` (deterministic) | cue/fidelity/structure matching | 57 accept / 13 reject |
| Orchestrator (hand adjudication of all 13) | read text + card for each flagged id | 12 script false positives, **1 genuine omission** |

## The genuine catch (script right, LLM auditor wrong)

`train_S5_002` — card affirms four symptoms (`cravings` severity null, `pelvic_pain` severe, `nausea` mild, `fatigue` severe). The text expressed only pelvic pain, nausea and fatigue; **cravings was absent**. The card is tagged `long_multi_symptom`, which requires at least four affirmed symptoms, so this was both a fidelity error and a tag violation. The LLM auditor accepted it on both of its passes.

Lesson recorded for the process: an LLM auditor reading for *"does this text say anything wrong"* reliably misses *"is something missing"*. The deterministic completeness check is therefore load-bearing, not decorative.

## The 12 false positives (LLM auditor right, script wrong)

| id | Script complaint | Actual text evidence |
|---|---|---|
| `train_S1_003` | spotting false / painkiller true "no cue" | `no spoting`, `took a painkilr` — typos |
| `train_S2_003` | no recoverable relative date; diarrhea no cue | `period started a week ago` -> cycle_day 8; `no diarhea` |
| `train_S3_003` | spotting false no cue | `spotng: none` |
| `train_S3_005` | S3 segment not label:value; supplement other no cue | leading `evening` is the required opener aside; `sups: other` |
| `train_S3_008` | spotting true but locally negated | `spotting: yes`; negation leaked from earlier lines |
| `train_S3_009` | S3 segment not label:value | leading `morning` opener aside |
| `train_S4_001` | global no-symptoms claim missing | `honestly nothing else going on` |
| `train_S4_003` | no recoverable relative date; supplement other no cue | `period strted 9 days ago` -> cycle_day 10; `plus some other stuff` |
| `train_S5_003` | spotting false no cue | `no spoting` |
| `train_S5_004` | blood_clots large not recoverable | `Big blood clots` = large on the clot scale |
| `train_S6_007` | global no-symptoms claim missing | `nothing at all today` |
| `train_S7_003` | supplement calcium no cue | `took calcuim`; also `hair los` = hair loss |

Seven root causes, all in the script: no typo tolerance, no number-word/relative-date paraphrases, negation scope crossing segment boundaries, opener asides treated as content lines, unrecognised `other`/abbreviated supplement wording, unrecognised global-negation paraphrases, missing clot-size synonyms.

## Actions taken

1. `train_S5_002` text rewritten to affirm cravings with no severity cue, keeping the other three symptoms, both denials, spotting and painkiller.
2. Audit script extended for all seven false-positive classes, with a regression fixture requiring that the *original* S5_002 text still fails.
3. Earlier in the batch, four records were rejected by the LLM auditor and fixed (`train_S4_001` phantom `flow: none` implied by "just spotting"; `train_S2_004` and `train_S4_004` fact-order constraint violations; `train_S2_002` severity-cue wording on null-severity insomnia).
4. Audit-reliability note: the LLM auditor's first report cited three non-existent ids (`train_S2_015`, `train_S2_019`, `train_S3_029`). All subsequent cited ids and phrases were re-verified programmatically by the orchestrator; all 17 citations in the second report were confirmed present. **Every LLM-auditor claim must cite ids that exist.**

## Realism metrics (deterministic, post-exemption)

`realism_warnings`: 0 warnings, 0 hard warnings across all six checks — fact-density alignment, schema dump (S1/S3 exempt by project rule), list-structure density cap, opener-frame repetition, sentence-subject repetition, length variance. Coverage report matches: 400 train / 35 validation / 60 gold / 70 batch, 495 unique ids, train/validation fact overlap 0.

Near-duplicate maxima: token 4-gram Jaccard 0.111 (`train_S1_001` / `train_S2_010`); numeric-normalised 0.160 (`train_S1_003` / `train_S1_007`). Both far below the 0.85 threshold.

## Human gate

Automated and LLM verdicts are advisory only. Every record still requires individual human acceptance before use in training.
