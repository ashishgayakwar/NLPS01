# Stabilization QA Report

Date: 2026-05-20

Scope: regression QA of the current stabilized NLP search flow.

Code changes made during this QA: none.

Files intentionally not modified:

- `app.py`
- `search.py`
- `intent_router.py`
- `catalog.py`
- UI behavior

## Method

I started the local FastAPI app with:

```bash
venv/bin/python app.py
```

Then I called the real JSON API:

```text
GET /search?q=<query>&top_k=5
```

For UI behavior, I mapped the returned `decision.state` to the current `app.py` renderer:

- `direct_match`: treatment card shown
- `needs_confirmation`: treatment card shown, confirmation chips shown
- `needs_clarification`: clarification-only card shown, no treatment cards
- `doctor_fallback`: fallback card shown, no treatment cards

I also inspected the current frontend chip/modal behavior in `app.py`.

## Query QA Matrix

| Query | Actual decision.state | Top result name | Treatment cards shown? | Clarifier chips shown? | Fallback shown? | Product acceptability |
|---|---:|---|---|---|---|---|
| `bawasir ka ilaj` | `direct_match` | Laser Treatment for Piles | Yes | No | No | Acceptable. Clear treatment query maps correctly. |
| `kharrate` | `needs_confirmation` | Knee Cartilage Repair Treament | Yes | Yes | No | Not acceptable. Query means snoring, but top result is unrelated knee treatment. Stabilized UI works, but retrieval/router relevance is bad. |
| `bachha nahi ho raha` | `direct_match` | Blocked Fallopian Tubes Treatment: Consult Today | Yes | No | No | Mostly acceptable. Fertility intent maps to a plausible gyne/fertility result. |
| `pet ki pathri` | `needs_clarification` | Gallstone (Gallbladder) Surgery | No | Yes | Clarification fallback line | Acceptable. Ambiguous stone term asks clarification before showing treatment. |
| `pathri` | `needs_clarification` | Gallstone (Gallbladder) Surgery | No | Yes | Clarification fallback line | Acceptable. Ambiguous stone term asks clarification before showing treatment. |
| `kaan mei dikkat` | `needs_clarification` | Tinnitus: Ear Noise Surgical Treatment & Diagnosis | No | Yes | Clarification fallback line | Acceptable. Broad ear complaint asks clarification first. |
| `pet dard` | `needs_clarification` | Percutaneous Drainage Treatment | No | Yes | Clarification fallback line | Acceptable from UI/state standpoint. Top result is odd, but hidden until user clarifies. |
| `stomach pain` | `needs_clarification` | Swallowable Gastric Balloon Treatment for Weight Loss | No | Yes | Clarification fallback line | Partly acceptable. UI safely clarifies, but repeated same-chip behavior can still stay in clarification. |
| `body pain` | `direct_match` | Left Nipple Pain in Male Treatment | Yes | No | No | Not acceptable. Broad symptom still over-routes to a specific treatment. |
| `body rash` | `doctor_fallback` | Urticaria Treatment & Diagnosis \| Cure for Hives, Swollen Skin | No | No | Doctor fallback | Acceptable as safe fallback for unclear/unsupported phrasing. |
| `skin allergy` | `direct_match` | Urticaria Treatment & Diagnosis \| Cure for Hives, Swollen Skin | Yes | No | No | Acceptable if dermatology/urticaria is in supported catalog scope. |
| `chest pain` | `doctor_fallback` | Left Nipple Pain in Male Treatment | No | No | Doctor fallback | Acceptable. Risky query is blocked from treatment cards. |
| `bahut bleeding ho rahi hai` | `doctor_fallback` | Vaginal BleedingTreatment \| Consult Female Gynaecologist | No | No | Doctor fallback | Acceptable. Risky bleeding query is blocked from treatment cards. |
| `random unsupported text` | `doctor_fallback` | Poor Ovarian Response: Book Discounted Consultation | No | No | Doctor fallback | Acceptable. Unsupported text does not show a random treatment card. |

## Raw State Notes

### Clear treatment queries

`bawasir ka ilaj` behaves well:

- State: `direct_match`
- Top result: Laser Treatment for Piles
- Product result: pass

`bachha nahi ho raha` behaves reasonably:

- State: `direct_match`
- Top result: Blocked Fallopian Tubes Treatment
- Product result: pass or acceptable enough for current catalog

`kharrate` is a regression risk:

- State: `needs_confirmation`
- Top result: Knee Cartilage Repair Treament
- Product result: fail
- Reason: the clear term `kharrate` avoids the weak lexical-evidence fallback, but retrieval does not find a relevant snoring result.

### Ambiguous terms

`pet ki pathri` and `pathri` both return:

- State: `needs_clarification`
- Chips:
  - Kidney / urine stone -> `kidney stone`
  - Gallbladder stone -> `gallstone`
  - Not sure -> consultation

Product result: pass.

The top result is still included in API JSON, but the UI does not show treatment cards for this state.

### Broad body-part/symptom queries

`kaan mei dikkat`, `pet dard`, and `stomach pain` return `needs_clarification`.

Product result: mostly pass.

The UI now correctly asks for clarification only. However, some target queries such as `stomach pain` and `ear pain` can themselves return `needs_clarification`, so a same-chip click can keep the user on a clarification screen. It does not create repeated query text, but it can still feel like a loop.

`body pain` is still a failure:

- State: `direct_match`
- Top result: Left Nipple Pain in Male Treatment
- Product result: fail

This is the biggest remaining product safety issue in the tested matrix.

### Unsupported queries

`body rash` and `random unsupported text` return `doctor_fallback`.

Product result: pass.

`skin allergy` returns `direct_match` to Urticaria. This is acceptable if Urticaria/skin allergy is considered supported in this product surface.

### Risky/urgent queries

`chest pain` and `bahut bleeding ho rahi hai` both return `doctor_fallback`.

Product result: pass.

No treatment cards are shown for these states.

## Action QA

### Click Not sure

Current frontend behavior:

```html
<a class="clarifier-chip consultation-trigger" href="#" data-treatment="Doctor Consultation">
```

Result:

- Opens existing consultation modal.
- Uses treatment value `Doctor Consultation`.
- Does not navigate to `/?q=...`.
- Does not call `/search`.

Product result: pass.

### Click same clarifier chip twice

Example: `pet dard`

Returned chip:

```json
{"label": "pet dard", "target_query": "stomach pain"}
```

First click:

```text
/?q=stomach%20pain
```

It does not become:

```text
/?q=pet%20dard%20pet%20dard
```

If the user clicks the same resulting chip again on `stomach pain`, the URL remains:

```text
/?q=stomach%20pain
```

Result:

- Repeated query text is not created.
- The same clarification state can still repeat for some targets like `stomach pain` or `ear pain`.

Product result: partial pass. Query growth is fixed; repeated clarification can still happen.

### Click a clarifier chip with `target_query`

Examples tested from API payloads:

- `pet ki pathri` -> `Kidney / urine stone` targets `kidney stone`
- `pet ki pathri` -> `Gallbladder stone` targets `gallstone`
- `kaan mei dikkat` -> `kaan dard` targets `ear pain`
- `pet dard` -> `pet dard` targets `stomach pain`

Follow-up `/search` results:

| Target query | Actual state | Top result | Product note |
|---|---:|---|---|
| `kidney stone` | `direct_match` | Urinary Tract Stone Treatment | Pass |
| `gallstone` | `direct_match` | Gallstone (Gallbladder) Surgery | Pass |
| `ear pain` | `needs_clarification` | Ear Infection Surgical Treatment By Best ENT Surgeon | Partial. Clean query is used, but router clarifies again. |
| `stomach pain` | `needs_clarification` | Swallowable Gastric Balloon Treatment for Weight Loss | Partial. Clean query is used, but router clarifies again. |

Product result: target-query behavior passes; some target choices still need better resolution strategy later.

### Click Book Free Consultation

Current frontend behavior:

- Any `.consultation-trigger` click is intercepted.
- Default navigation is prevented.
- `openConsultationModal(...)` runs.
- Treatment defaults to `Doctor Consultation` for clarification/fallback CTAs.
- Primary treatment cards use the treatment name as `data-treatment`.

Product result: pass.

## Repeated Query Cleanup QA

Frontend `doSearch()` now calls `cleanQuery(q.value)` before fetching `/search`.

Expected frontend cleanup:

- `pet dard pet dard` -> `pet dard`
- `kaan dard kaan dard` -> `kaan dard`

Important nuance:

- This cleanup is frontend-only.
- Direct API calls to `/search?q=pet+dard+pet+dard` still search the repeated query.
- That is acceptable for the current requirement because the requested stabilization was frontend query cleanup before fetch.

## Pass/Fail Summary

### Passed

- `needs_clarification` no longer shows treatment cards.
- Clarifier chips no longer append raw text to the old query.
- Structured `target_query` chips navigate to clean queries.
- String fallback chips would search only the chip label.
- `Not sure` opens consultation instead of searching.
- Risky queries tested do not show treatment cards.
- Unsupported text tested does not show treatment cards.
- `/search` remains JSON API usage from frontend fetch, not user-facing navigation.

### Failed / Remaining Product Risks

1. `body pain` still routes to `direct_match` with `Left Nipple Pain in Male Treatment`.

   This is not acceptable for a broad symptom query. The stabilization did not add broad symptom medical routing rules, so this remains unresolved.

2. `kharrate` routes to `needs_confirmation` with an unrelated knee result.

   This is not acceptable for a popular/clear query. The current catalog/retrieval combination does not produce a relevant snoring result.

3. Some clean clarifier targets can still return `needs_clarification`.

   Examples:

   - `ear pain`
   - `stomach pain`

   The query no longer grows, but users can still see another clarification screen after choosing a chip.

## Overall QA Verdict

The stabilization work succeeds for the main interaction model:

- clarification states are clarification-only
- chips no longer concatenate raw text
- consultation escape works
- unsupported and urgent examples are safer than before

However, the product is not fully stable yet because relevance/routing issues remain for broad symptoms and missing/weak catalog coverage. The highest-priority remaining failures from this QA are:

1. `body pain` should not be `direct_match`.
2. `kharrate` should not show a knee treatment.
3. Clarifier targets that are already specific enough should avoid repeating the same clarification state when possible.
