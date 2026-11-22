Three separate failures: prose preamble, markdown fence, trailing comma. All three are _structurally_ impossible under a grammar. A constrained decoder can only produce the object.

**What it does not fix — and this is the whole point.** A grammar guarantees form, never meaning. Give it the schema `{"symptom": "cramps"|"bloating"|"headache", "severity": "mild"|"moderate"|"severe"}` and the input _"cramps are unreal today, could barely stand"_. The decoder will happily emit `"severity": "mild"` if that's the model's preference — because it _must_ emit one of three legal strings. You've traded "invalid JSON" for "confidently wrong value." In a menstrual-health app, a confidently wrong `severity` is more dangerous than a parse error, because a parse error is visible and a wrong value isn't.

That is precisely why your metric trio includes **schema-valid but semantically wrong**. Constrained decoding is what makes that metric matter.

**Why this is "what a competent engineer ships first."** Zero training, zero data, ten lines of config, and you get 100% structural validity today. If your fine-tune can't beat that on _semantics_, you've proven fine-tuning wasn't necessary — which is a genuine, valuable, slightly uncomfortable finding. Many teams would kill for that answer before burning a month.

**So make the comparison a 2×2, not a 3-way list.** Same prompt, same schema for every cell; only the weights and the decoder change:

|                | free decoding               | grammar-constrained          |
| -------------- | --------------------------- | ---------------------------- |
| **base model** | raw baseline (the strawman) | **the honest baseline**      |
| **fine-tuned** | shows format learning alone | **the production candidate** |

Two models to set up, four numbers, one table that answers every obvious question before it's asked. The fine-tuned + constrained cell is what you'd actually deploy.

---

## 2. Template-family split (leakage)

**What leakage looks like.** Say one of your seed templates is:

> `day {n}, {symptom}, took {drug}, slept {h}h`

You fill the slots 400 times. Then you shuffle all 600 examples and take 80/20. Now the model trains on _"day 3, bad cramps, took ibuprofen, slept 5h"_ and gets tested on _"day 4, mild headache, took paracetamol, slept 7h"_. Those are, to a tokenizer, almost the same sentence with different nouns. The model doesn't learn extraction — it learns **the skeleton**. Test F1 comes back 0.97. You put "0.97 F1" on your CV.

Then a real user writes: _"ugh day 3 and the cramps are unreal, popped 2 ibuprofens, maybe 4-5 hrs sleep?"_ and the model falls apart, because nobody taught it that sentence shape exists.

It's the exam analogy: you revise 100 versions of the same question with different numbers, then sit an exam containing that exact question. Of course you score 100%. It says nothing about whether you know the subject.

**The fix.** Label each seed template with a **family** — a distinct surface structure. Something like: `terse-comma-list`, `casual-narrative`, `clinical-shorthand`, `typo-heavy-chat`, `multi-clause-runon`, `question-form`, `mixed-language`. Then **assign whole families** to train or test. Your test set is now made of sentence _shapes_ the model has never seen, only slot patterns it has. That measures generalization instead of memorization.

**How to prove it in the README** (one sentence, huge credibility):

> _"Split by template family (19 families: 14 train, 5 held out). Verified zero shared 8-gram between train and test splits."_

An 8-gram overlap check is just a sanity check that no long phrase appears in both sets — cheap, and it catches accidental duplicates.

**Watch for the other leaks too:** the gold set must share _zero_ items with training; if you ever hand-edit a gold example into a training example you've destroyed it; and the sneaky one — **writing your training templates while staring at your gold set**. That's leakage by construction, even if the strings differ.

---

## 3. Correcting your reading of "stratify"

No — your interpretation is the opposite of what I meant, and it's worth being precise because it's a common confusion.

- **Template family decides _membership_**: does this item go to train or to test?
- **Category decides _balance_**: how much of each phenomenon appears in each split.

Stratify means: **every split contains all 12 categories, in roughly the same proportions.** You are not assigning "negation to train, mixed-language to test." You're ensuring test isn't accidentally 60% short inputs.

| Category              | Train | Gold |
| --------------------- | ----- | ---- |
| implicit dates        | 12%   | 12%  |
| negation              | 10%   | 10%  |
| mixed-language        | 8%    | 8%   |
| typos                 | 10%   | 10%  |
| long multi-symptom    | 8%    | 8%   |
| unit ambiguity        | 8%    | 8%   |
| brand names           | 6%    | 6%   |
| emotional language    | 8%    | 8%   |
| empty/off-topic       | 6%    | 6%   |
| adversarial injection | 4%    | 4%   |
| contradictory         | 6%    | 6%   |
| very short            | 14%   | 14%  |

**Why train needs all 12:** otherwise a bad test score on negation means "it never saw a negation," which is a data problem, not a modelling result. You want the model to have _met_ each phenomenon and still be tested on _unseen shapes_ of it.

**Why gold needs all 12:** you want per-category F1 for every arm. A category absent from test is a category you know nothing about — and the whole point of the writeup is the breakdown.

**The two axes interact, and this is the design puzzle.** For each category, make sure it's covered by **at least 2–3 distinct template families**, then hold one family back. If "negation" is expressed by only one family and you hold that family out, train sees zero negations and your negation score measures zero-shot transfer, not learning. Decide deliberately which experiment you're running, and write down which it is.

Optional bonus if you're ahead of schedule: deliberately hold out _one entire category_ to test zero-shot generalization and report it separately. That's a genuinely interesting result either way.

---

## 4. Confidence intervals on 100 items

**The arithmetic first.** Suppose across your gold set your model gets 88% of field comparisons right. That's a proportion from n=100 records. Standard error = √(p(1−p)/n) = √(0.88 × 0.12 / 100) ≈ 0.032. A 95% interval is roughly ±1.96 SE ≈ **±6.4 points**. So "0.88" really means "somewhere around 0.81 to 0.94." That's the ±5–8 I quoted.

**The trap that makes it worse.** Your test set has 100 records but maybe 500 field comparisons. A naive person uses n=500, gets SE ≈ 0.014, and reports ±3 — falsely precise. Why is that wrong? Because fields **co-fail**. If the model misreads the sentence structure, it gets cycle_day, symptom, severity, and medication all wrong in one record. Those 5 failures are not 5 independent pieces of evidence; they're one failure counted five times. Effective n is closer to 100 than 500.

**The fix: bootstrap at the record level.** Resample your 100 _records_ with replacement, 1,000 times, recompute field-F1 each time, and take the 2.5th and 97.5th percentiles of those 1,000 values. Because you resample whole records, the co-failing fields move together and the interval widens honestly. Typical result on this kind of task: ±8–10 points rather than ±6.

**Why this changes your conclusions, not just your error bars.** If fine-tuned = 0.88 and prompted+grammar = 0.85 and the intervals overlap, **you cannot claim a win.** The honest sentence is: _"No measurable improvement at n=100; the fine-tune's advantage is within noise on this test set."_ That sentence is worth more than a fake victory, because it shows you know what your data can support.

And apply the same discipline to your per-category table. If "long inputs" has n=5, a 0.61 vs 0.78 gap is probably noise. So report **n next to every category F1**, and mark n<10 as indicative only. That's the maturity marker: not "I computed CIs," but "I declined to over-claim."

---

## 5. Canonicalization, and why exact-match is a trap

**Exact match on JSON strings compares serialization, not meaning.** Every one of these pairs is semantically identical and textually different:

- Key order: `{"a":1,"b":2}` vs `{"b":2,"a":1}`
- Whitespace: `{"a": 1}` vs `{"a":1}`
- Numbers: `5` vs `5.0` vs `5.00`
- Null vs absent: `{"dose_mg": null}` vs `{}`
- List order: `["cramps","bloating"]` vs `["bloating","cramps"]`
- Case/synonyms: `"Ibuprofen"` vs `"ibuprofen"` vs `"paracetamol"`/`"acetaminophen"` (same drug, different locale)

Without canonicalization you could get exact-match = 0.12 and conclude the model is broken, when 70% of its outputs were _right_ and you measured a comma. Or the reverse: canonicalization that's too lenient hides real errors.

**Canonicalization means: parse, then normalize, then compare structurally.** Decide explicitly, before running anything:

- Case-fold enum values; map synonyms to a fixed vocabulary (is `paracetamol` = `acetaminophen`? decide).
- Round floats to a fixed precision.
- Decide whether list order is meaningful. If not, sort before comparing. If yes, define the ordering rule (e.g., order of mention).
- Pick one convention for null vs absent and enforce it on both sides.
- Decide whether extra keys are a failure, ignored, or penalized.
- Decide what `[]` vs `null` means for "no symptoms."

Write those seven rules down in the README _before_ you compute a number. Otherwise your headline metric is a property of your serializer, and anyone who re-implements your eval gets a different answer.

**Then the trio, defined properly.**

_Field-level F1._ For each leaf field (or field path, e.g. `symptoms[0].severity`), count TP (gold has value X, pred has X), FP (pred asserts something gold doesn't), FN (gold asserts something pred missed). Precision = TP/(TP+FP); recall = TP/(TP+FN); F1 = harmonic mean. Example:

- Gold: `{"cycle_day": 3, "symptoms":[{"name":"cramps","severity":"severe"}], "medications":[{"name":"ibuprofen","dose_mg":null}], "sleep_hours": 5.0}`
- Pred: `{"cycle_day": 3, "symptoms":[{"name":"cramps","severity":"moderate"}], "medications":[{"name":"ibuprofen","dose_mg": 200}], "sleep_hours": 5.0}`

Parses fine, validates fine. `cycle_day` ✓, `sleep_hours` ✓, `severity` wrong (one FP + one FN), `dose_mg` **invented 200mg that the text never said** — that's not a rounding error, that's a hallucination with clinical consequences. Valid JSON. F1 ≈ 0.6 on this record. _This_ is what an honest metric catches.

Also decide **micro vs macro**: micro pools all fields (common fields dominate); macro averages per-field F1 (rare fields count equally). Macro is the honest one for "does it handle rare schemas" — and it's the one that will make your numbers look worse, which is why you should use it and say why.

_Invalid-JSON rate._ Doesn't parse, or fails schema validation. Keep it separate — never fold it into F1, because it's the one metric constrained decoding trivializes, and hiding it inside an average would launder that fact.

_Schema-valid but semantically wrong._ Parses and validates; content is wrong, incomplete, or hallucinated. The `dose_mg: 200` case above. This is the metric that distinguishes a demo from a system, because it's the failure mode real users experience and never notice.

---

## 6. What the 100 gold examples actually are

**No — not model outputs.** That would poison the test set in a subtle, fatal way.

Model-generated inputs are **too clean**. They're the right length, grammatical, use the vocabulary the base model already prefers, and never contain the disfluency real people type ("ughhh day 3 😭 cramps r awful, took 2 ibuprofens at like 8pm, maybe slept 4h??"). Test on those and you're measuring performance on a distribution friendlier than production. The whole _premise_ of the project is that real logs are messy — so the test set must be the messiest thing you own.

**What to do instead, in order of quality:**

1. **Your own real logs**, anonymized and consented (you're building Orba — you know what users actually write). Best possible. Even 30 of these transforms the project.
2. **Hand-written by you**, deliberately covering the 12 categories, ~2 hours for 100. Mix registers: terse, rambling, typo-heavy, non-native, emoji, medical shorthand.
3. **Generator as a muse, never as a source.** Prompt it for "10 ways someone might describe a missed pill," read them, then write your own versions. Never copy its phrasing wholesale — that's how model fingerprints get in. Be transparent in the README about the method.

**And the labels are yours.** Not the model's, not the generator's. Where a sentence is genuinely ambiguous, record the ambiguity (a `notes` field, or a flag) instead of forcing a guess — that's data too, and it tells you the schema is underspecified, which is a real finding worth a README paragraph.

**"Blind" means:** you label the 100 inputs _without ever having seen any model output for them_. Not the base model's, not the fine-tune's.

---

## 7. The two sequencing rules, mechanically

### "Label gold before you train"

Two distinct failure mechanisms:

**Anchoring.** You see the base model parse _"maybe day 3, light spotting"_ as `{"cycle_day": 3}`. You were unsure. Now you go "eh, sure, day 3." Your label is no longer your independent judgment — it's a ratification of the model. Your test set now measures **agreement with the model**, which is a circular metric that will look excellent and mean nothing.

**Motivated revision.** You see the model fails on negations. You re-read your labels and "clarify" three of them. Now the test set has been quietly tuned toward the model. Nobody can prove you did it, including you — that's what makes it dangerous.

Practical form: write the 100 labels into a file, commit it, don't touch it again. If you must change one, log the change and the reason.

### "Lock the eval harness before you look at results"

Two mechanisms again:

**Silent metric bugs.** Say your F1 code treats a missing key as `""` instead of `null`, so every correct null counts as an error. You discover this _after_ seeing that the fine-tune scores 0.41. You now have a strong incentive to... leave it. Bugs that flatter you are the ones that survive. If you'd found it before seeing results, you'd have fixed it in thirty seconds.

**Metric shopping.** You compute exact-match, micro-F1, macro-F1, per-field F1, token-level F1. Whichever shows a win becomes "the metric." This is p-hacking, it's usually unconscious, and it's invisible to a reader unless you pre-register. Pre-registering costs you 20 minutes and makes every claim you make survive scrutiny.

Practical form: a README section titled "Evaluation protocol," written _before_ the fine-tune runs, listing the metrics, the canonicalization rules, and the primary metric (pick one; the rest are supporting). Commit the harness. If you later change it, report both versions and say why.

It's deciding what counts as a goal before the match starts. Every sport does it, for a reason.

---

## 8. Why generate the plumbing instead of writing it

Let me push back on my own advice first, because your instinct isn't wrong: **writing code is how you learn**, and an eval loop written by an AI is an eval loop you don't understand — which is a liability on a CV, not an asset. If an interviewer says "walk me through your evaluation" and the answer is "the model wrote it," the project scores zero regardless of the F1.

So the rule isn't "generate everything." It's a **decision test applied per block of code**:

1. **Does this block contain a judgment I'll be asked about?** Schema, split logic, canonicalization, what counts as a TP, how ambiguous cases are labeled, which metric is primary → **you write it**.
2. **Could I defend every branch in an interview?** If not, it isn't done yet, no matter who typed it.
3. **Is there a known-correct reference implementation and no decision in it?** Dataloader, batching, tokenizer plumbing, LoRA config boilerplate, matplotlib axes, file I/O → **generate it**.

Concretely, for this project:

- **Generate:** the training script (adapt Unsloth's own notebook — it's the reference implementation, and re-deriving it is a waste of your one day), data-generation loops, plotting, CLI plumbing, the README skeleton.
- **Write yourself (or generate then rewrite line by line):** the metric functions, the canonicalization, the split logic, the label format, the failure-analysis code.
- **Own completely, no delegation:** the schema, the 12-category taxonomy, the 100 labels, the interpretation.

The asymmetry is that **metric bugs are silent and metric decisions are everything.** A wrong dataloader crashes and you fix it in five minutes. A wrong F1 runs beautifully and produces a number you'll put on your CV. That's why the 40% of the eval loop that encodes judgment is not boilerplate, and why "the eval harness is locked" and "I wrote the metric" are the same sentence.

And the time argument: you have ~10 hours. Typing boilerplate costs 3–4 of them and teaches you nothing you'll be asked about. Debugging why your F1 is 0.31 when you expected 0.85 costs an hour and teaches you the entire domain. Spend the day on the second kind.

One-line rule to carry: **generate, then read every line and rewrite the ones that encode a decision. If you can't state what a line does in one sentence, you don't own it.**

---

Next concrete step, since you're at zero files: tell me your GPU situation, then draft the schema and the 12-category list _in prose_ (not code) and I'll pressure-test them with you — specifically the null/absent convention, the negation representation, and the severity scale, because those three decisions ripple into every metric you compute later.
