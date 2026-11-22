# Pilot — S1 comma-list examples

Fact cards are partial: unspecified scalar fields become `null`; unspecified lists become `[]`.

| ID | Structure | Tags | Fact card | Text |
|---|---|---|---|---|
| S1-001 | S1 | `negation`, `hedging` | `symptoms=[{"name":"cramps","severity":"mild"}]`; `denied=["headache"]`; `sleep_hours=5.5` | "no headache, some cramps, maybe 5-6 sleep" |
| S1-002 | S1 | `implicit_dates` | `flow="light"`; `cycle_day=3`; `spotting=true` | "spotted before yesterday plus flow, then flow yesterday, today light period" |
| S1-003 | S1 | `typos` | `symptoms=[{"name":"cramps","severity":"moderate"},{"name":"pelvic_pain","severity":null},{"name":"cravings","severity":null}]` | "bad crmasp, really hurt eveyrwerhe, in my prviate arae too, plus cravnigs" |
| S1-004 | S1 | `implicit_dates` | `cycle_day=6`; `flow="medium"`; `symptoms=[{"name":"nausea","severity":null},{"name":"blood_clots","severity":"large"}]` | "started 5 days ago, now nighttime, today big blood_clot, nausea" |
| S1-005 | S1 | none | `flow="medium"`; `painkiller=true` | "had period, took painkiller" |
| S1-006 | S1 | `very_short` | `energy_level="low"`; `symptoms=[{"name":"fatigue","severity":null}]` | "tired, no energy" |
| S1-007 | S1 | `supplement_naming` | `supplements=["iron"]`; `symptoms=[{"name":"cravings","severity":null}]` | "took iron, had some cravings in the morning" |
| S1-008 | S1 | `emotional_language` | `mood="low"`; `symptoms=[{"name":"fatigue","severity":null}]` | "feel like shit, tired" |
