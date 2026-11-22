# Batch 001 semantic audit (re-audit after fixes)

## Per-structure accept/reject counts

| Structure | Total | ACCEPT | REJECT |
|---|---|---|---|
| S1 | 10 | 10 | 0 |
| S2 | 10 | 10 | 0 |
| S3 | 10 | 10 | 0 |
| S4 | 10 | 10 | 0 |
| S5 | 10 | 10 | 0 |
| S6 | 10 | 10 | 0 |
| S7 | 10 | 10 | 0 |
| **Total** | **70** | **70** | **0** |

## Realism assessment

- ok: 69
- warn: 1 (`train_S4_002` — prose run-on with repeated `and` glue)
- bad: 0

S1 and S3 are list-like by definition and are not flagged as schema dumps (per DECISIONS.md density cap). Their fact cards are within the 7-fact cap.

## Corrected repeated-opener findings (verified ids only)

Repeated opening tokens:
- `well` opens 4 records: `train_S1_008`, `train_S4_002`, `train_S4_003`, `train_S4_006`
- `morning` opens 3: `train_S1_006`, `train_S2_005`, `train_S3_009`
- `i` opens 3: `train_S2_008`, `train_S5_001`, `train_S5_005`
- `evening`, `hmm`, `how`, `late`, `no`, `skin`, `this`, `what` each open 2 records (see item audit for full lists).

Repeated leading phrases:
- `new hair growth`: `train_S1_003`, `train_S1_008`, `train_S2_007`
- `no symptoms at all`: `train_S1_001`, `train_S2_010`, `train_S4_010`, `train_S7_001`, `train_S7_010`
- `high energy`/`slept well`: `train_S1_009`, `train_S7_009`
- `skin is normal`: `train_S2_006`, `train_S2_010`, `train_S5_004`

No exact near-paraphrase pairs with only values swapped were found.

## Re-audited fixed records

- `train_S4_001`: ACCEPT — `spotting` no longer implies `flow: none`; global negation preserved.
- `train_S2_004`: ACCEPT — symptoms now contiguous before flow/spotting; hedged flow; spotting false.
- `train_S4_004`: ACCEPT — symptoms now contiguous before flow/spotting; hedged flow; spotting false.
- `train_S2_002`: ACCEPT — `insomnia too` removes severity cue; fact order and severities match card.

## Audit reliability

All ids cited in this report were programmatically verified to exist in `data/text/batch_001.jsonl` (70 records). No non-existent ids are cited.

## Gate verdict

SCALE NEXT BATCH

All 70 records now pass fact fidelity, structure compliance, and held-out-form checks after the four text fixes. Only one realism warning remains (a dense S4 run-on), which is acceptable for a quick health log. The batch is ready to scale.