# Query Normalization Candidate Report

Date: 2026-05-20

Scope: identify common patient-search normalization cases that may need support later.

Code changes made: none.

Files intentionally not modified:

- `app.py`
- `search.py`
- `intent_router.py`
- `catalog.py`

## Method

I evaluated each candidate through the current search and router flow:

```python
results = engine.search(query, top_k=5)
decision = route_patient_intent(query, results)
```

The current frontend `cleanQuery()` only trims, collapses whitespace, and removes exact repeated adjacent phrases. It does not insert missing spaces, correct spellings, or normalize variants.

The current router broad-symptom guard works when it sees recognizable phrases or tokens. Joined words like `bodypain` stay as one token.

## Current Behavior Matrix

| Example | Current decision.state | Current top result | Expected normalized query | Expected behavior | Best handling layer |
|---|---|---|---|---|---|
| `bodypain` | `doctor_fallback` | Left Nipple Pain in Male Treatment | `body pain` | `needs_clarification` with broad symptom area chips | Query normalizer |
| `chestpain` | `doctor_fallback` | Left Nipple Pain in Male Treatment | `chest pain` | `doctor_fallback` as risky symptom | Query normalizer + router guard |
| `stomachpain` | `needs_clarification` | Left Nipple Pain in Male Treatment | `stomach pain` | `needs_clarification`; no treatment card | Query normalizer |
| `kidneystone` | `needs_confirmation` | Kidney Stone Laser Treatment | `kidney stone` | direct/confirmation to kidney stone result | Query normalizer |
| `gallbladderstone` | `needs_confirmation` | Gallstone (Gallbladder) Surgery | `gallbladder stone` | direct/confirmation to gallstone result | Query normalizer |
| `earpain` | `needs_clarification` | Tinnitus: Ear Noise Surgical Treatment & Diagnosis | `ear pain` | `needs_clarification` with ear chips, or ENT route after clarification | Query normalizer |
| `kneepain` | `needs_clarification` | Knee Tendon Repair Surgery | `knee pain` | `needs_clarification` with knee chips, or ortho route after clarification | Query normalizer |
| `backpain` | `doctor_fallback` | Spine Surgery - Procedure, Diagnosis, and Treatment | `back pain` | likely `needs_clarification`, not fallback, unless severe/risky context | Query normalizer + router guard |
| `urineburning` | `needs_clarification` | Urinary Tract Stone Treatment | `urine burning` | `needs_clarification` with urine chips | Query normalizer |
| `periodproblem` | `doctor_fallback` | Irregular Periods Treatment | `period problem` | gyne/period-related result or clarification | Query normalizer + synonym dictionary |
| `periodsproblem` | `doctor_fallback` | Irregular Periods Treatment | `periods problem` | gyne/period-related result or clarification | Query normalizer + synonym dictionary |
| `bawaseer` | `direct_match` | Laser Treatment for Piles | `bawasir` / `piles` | direct/confirmation to piles | Already supported; synonym dictionary if formalized |
| `bavasir` | `direct_match` | Laser Treatment for Piles | `bawasir` / `piles` | direct/confirmation to piles | Already supported; synonym dictionary if formalized |
| `kharate` | `doctor_fallback` | Laser Hair Removal Treatment for Face | `kharrate` / `snoring` | ENT/snoring-adjacent result | Synonym dictionary + catalog enrichment |
| `pishaab` | `doctor_fallback` | Bladder Neck Incision Surgery in India | `peshab` / `urine` | urine-related clarification or urology route | Synonym dictionary |
| `pesab` | `doctor_fallback` | Preimplantation Genetic Testing for Aneuploidy | `peshab` / `urine` | urine-related clarification or urology route | Synonym dictionary |

## Observations

### 1. Missing Spaces / Compound Words

The most obvious gap is joined English tokens:

- `bodypain`
- `chestpain`
- `stomachpain`
- `kidneystone`
- `gallbladderstone`
- `earpain`
- `kneepain`
- `backpain`
- `urineburning`
- `periodproblem`
- `periodsproblem`

Current behavior is inconsistent because retrieval may still semantically find a plausible result, but BM25 is usually `0.0`. Routing then depends on the broad body-part rules, clear-treatment substrings, or weak-evidence fallback.

Recommended approach:

- Add a conservative query normalizer that can split known compound tokens only when the split is exact and high confidence.
- Examples:
  - `bodypain` -> `body pain`
  - `chestpain` -> `chest pain`
  - `kidneystone` -> `kidney stone`
  - `urineburning` -> `urine burning`

This should happen before routing and preferably before retrieval too.

### 2. Singular / Plural

Current tested examples:

- `periodproblem`
- `periodsproblem`

Both are currently routed to `doctor_fallback`, despite top result being `Irregular Periods Treatment`.

The issue is not only plural handling. These are also joined compound words. After splitting, the product still needs a synonym layer:

- `period problem`
- `periods problem`
- `period issue`
- `irregular periods`

Recommended approach:

- Query normalizer for missing spaces.
- Synonym dictionary for period-related variants.
- Consider gyne-specific clarification instead of direct match if query is broad.

### 3. Common Hinglish Spelling Variants

Already working:

- `bawaseer`
- `bavasir`

These route to `Laser Treatment for Piles`, likely because the router has clear treatment terms and the catalog includes these variants.

Not working:

- `kharate`
- `pishaab`
- `pesab`

Recommended approach:

- Synonym dictionary for high-frequency Hinglish variants:
  - `kharate` -> `kharrate`
  - `pishaab` -> `peshab`
  - `pesab` -> `peshab`
- Catalog enrichment may also help if these are common enough and tied to a specific treatment area.

### 4. Simple Typos

Some examples are better treated as typos than medical synonyms:

- `kharate` missing one `r`
- `pesab` simplified spelling for `peshab`

Recommended approach:

- Avoid broad fuzzy matching across all medical terms. It can create unsafe matches.
- Use a curated typo/synonym dictionary for common patient inputs.
- Keep typo normalization explainable and limited to known variants.

## Classification By Handling Layer

### Query Normalizer

Best for spacing and safe compound splitting:

- `bodypain`
- `chestpain`
- `stomachpain`
- `kidneystone`
- `gallbladderstone`
- `earpain`
- `kneepain`
- `backpain`
- `urineburning`
- `periodproblem`
- `periodsproblem`

### Synonym Dictionary

Best for known equivalent spellings or Hinglish variants:

- `bawaseer` -> `bawasir` / `piles`
- `bavasir` -> `bawasir` / `piles`
- `kharate` -> `kharrate` / `snoring`
- `pishaab` -> `peshab` / `urine`
- `pesab` -> `peshab` / `urine`
- `period problem` -> `irregular periods` or period-related clarification

### Router Guard

Best for safety/state decisions after normalization:

- `body pain` -> broad symptom clarification
- `chest pain` -> risky fallback
- `back pain` -> likely broad-area clarification, depending product scope
- `fever`, `weakness`, `dard`-style broad symptoms

The router should not be responsible for splitting `bodypain` into `body pain`. It should receive normalized text.

### Catalog Enrichment

Best when a term is a valid patient phrase tied to a known catalog area:

- snoring/kharrate variants on ENT pages
- peshab/pishaab variants on urology pages
- period problem variants on gyne pages

Catalog enrichment should not become the only normalization mechanism, because it does not help safety routing before retrieval unless the router also knows the variant.

### Not Worth Supporting Now

None of the tested examples are obviously worthless. They are all plausible patient inputs.

Lower priority candidates:

- `periodproblem`
- `periodsproblem`

Reason: they need both spacing and product decisions about whether to route directly to irregular periods or ask a gyne clarification question.

## Recommended General Fix

Build a small query normalization layer before retrieval and routing.

Suggested behavior:

1. Preserve the original query for display and analytics.
2. Create a normalized query for search/routing.
3. Apply conservative whitespace cleanup.
4. Apply exact compound splitting using a curated lexicon.
5. Apply curated synonym/variant mapping.
6. Pass normalized query to retrieval and router.
7. Include both original and normalized query in debug logs/API response if useful.

Example normalization map:

| Raw input | Normalized query |
|---|---|
| `bodypain` | `body pain` |
| `chestpain` | `chest pain` |
| `stomachpain` | `stomach pain` |
| `kidneystone` | `kidney stone` |
| `gallbladderstone` | `gallbladder stone` |
| `earpain` | `ear pain` |
| `kneepain` | `knee pain` |
| `backpain` | `back pain` |
| `urineburning` | `urine burning` |
| `periodproblem` | `period problem` |
| `periodsproblem` | `periods problem` |
| `kharate` | `kharrate` |
| `pishaab` | `peshab` |
| `pesab` | `peshab` |

## Priority Recommendation

Priority 1:

- `bodypain`
- `chestpain`
- `kidneystone`
- `gallbladderstone`
- `kharate`

Reason: these affect safety or high-intent treatment searches.

Priority 2:

- `stomachpain`
- `earpain`
- `kneepain`
- `backpain`
- `urineburning`
- `pishaab`
- `pesab`

Reason: common patient phrasing, mostly clarification/routing quality.

Priority 3:

- `periodproblem`
- `periodsproblem`

Reason: likely important, but product should decide whether period queries are supported as direct catalog matches or should clarify first.
