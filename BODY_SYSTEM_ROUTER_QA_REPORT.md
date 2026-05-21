# Body-System Router QA Report

Date: 2026-05-21

Scope: QA of the latest body-system disambiguation router across proctology, urology, gynecology, safety, and known stable search queries.

Code changes made during this QA: none.

Files intentionally not modified:

- `app.py`
- `search.py`
- `catalog.py`
- `intent_router.py`
- `query_normalizer.py`
- `body_system_router.py`

Only this report file was edited for this update.

## Method

Initial QA used the local API:

```text
GET http://127.0.0.1:8000/search?q=<query>&top_k=10
```

After the breathing safety fix, I reran the focused safety/regression matrix through the current code path with `SemanticSearch`, `normalize_query()`, and `route_patient_intent()`.

Treatment-card visibility is based on the current frontend renderer in `app.py`:

| decision.state | Treatment card shown? |
|---|---|
| `direct_match` | Yes |
| `needs_confirmation` | Yes |
| `needs_clarification` | No |
| `doctor_fallback` | No |

## Summary

The body-system router is doing its core job: stool/rectal/anorectal + bleeding/pain/swelling queries no longer show wrong vaginal or vascular treatment cards, even when retrieval still ranks those pages first.

Urology and gynecology body-system routes also behave safely for the covered seed terms. Known stable searches mostly remain stable.

The previous P0 safety gap is now fixed: explicit breathing difficulty queries such as `saans lene mein dikkat`, `saans nahi aa rahi`, `breathing difficulty`, `shortness of breath`, and `breathless` now return `doctor_fallback`.

## QA Matrix

| Group | Query | normalized_query | decision.state | decision.title | Top result | Treatment card shown? | Acceptable? | Failure type / note |
|---|---|---|---|---|---|---|---|---|
| Procto | `tatti mei khoon aana` | `tatti mei khoon aana` | `needs_clarification` | We need one more detail | Vaginal BleedingTreatment \| Consult Female Gynaecologist | No | Yes | Wrong retrieval top is hidden by procto clarification. |
| Procto | `potty me blood` | `potty me blood` | `needs_clarification` | We need one more detail | Peripheral Artery Disease: Treatment & Diagnosis | No | Yes | Wrong retrieval top is hidden by procto clarification. |
| Procto | `blood in stool` | `blood in stool` | `needs_clarification` | We need one more detail | Thrombectomy: Minimally Invasive Treatment for Blood Clots | No | Yes | Wrong retrieval top is hidden by procto clarification. |
| Procto | `stool blood` | `stool blood` | `needs_clarification` | We need one more detail | Thrombectomy: Minimally Invasive Treatment for Blood Clots | No | Yes | Wrong retrieval top is hidden by procto clarification. |
| Procto | `motion me blood` | `motion me blood` | `needs_clarification` | We need one more detail | Thrombectomy: Minimally Invasive Treatment for Blood Clots | No | Yes | Wrong retrieval top is hidden by procto clarification. |
| Procto | `latrine me khoon` | `latrine me khoon` | `needs_clarification` | We need one more detail | Thrombectomy: Minimally Invasive Treatment for Blood Clots | No | Yes | Wrong retrieval top is hidden by procto clarification. |
| Procto | `bawasir bleeding` | `bawasir bleeding` | `needs_clarification` | We need one more detail | Laser Treatment for Piles | No | Yes | Correct specialty; clarification is conservative for bleeding. |
| Procto | `piles bleeding` | `piles bleeding` | `needs_clarification` | We need one more detail | Laser Treatment for Piles | No | Yes | Correct specialty; clarification is conservative for bleeding. |
| Procto | `gudha me dard` | `gudha me dard` | `needs_clarification` | We need one more detail | Sphincterotomy - Diagnosis, Procedure & Recovery | No | Yes | Correct anorectal context; no premature treatment card. |
| Procto | `anus me sujan` | `anus me sujan` | `needs_clarification` | We need one more detail | Anal Abscess Surgery - Benefits, Treatment Types & Recovery | No | Yes | Correct anorectal context; no premature treatment card. |
| Urology | `peshab me jalan` | `peshab me jalan` | `needs_clarification` | We need one more detail | Cystolithotripsy Treatment for Urinary Bladder Stones in India | No | Yes | Urology clarification works. |
| Urology | `urine burning` | `urine burning` | `needs_clarification` | We need one more detail | Urinary Tract Stone Treatment | No | Yes | Urology clarification works. |
| Urology | `blood in urine` | `blood in urine` | `needs_clarification` | We need one more detail | Urinary Tract Stone Treatment | No | Yes | Urology clarification works. |
| Urology | `peshab me khoon` | `peshab me khoon` | `needs_clarification` | We need one more detail | Vaginal BleedingTreatment \| Consult Female Gynaecologist | No | Yes | Wrong retrieval top is hidden by urology clarification. |
| Urology | `urine ruk raha hai` | `urine ruk raha hai` | `needs_clarification` | A little more detail would help | Urinary Tract Stone Treatment | No | Yes | Existing broad body-part logic handles this safely. |
| Urology | `kidney stone pain` | `kidney stone pain` | `needs_clarification` | We need one more detail | Urinary Tract Stone Treatment | No | Yes | Urology clarification works; conservative despite correct retrieval. |
| Gynecology | `period bleeding` | `period bleeding` | `needs_clarification` | We need one more detail | Vaginal BleedingTreatment \| Consult Female Gynaecologist | No | Yes | Gynecology clarification works. |
| Gynecology | `vaginal itching` | `vaginal itching` | `needs_clarification` | We need one more detail | Vaginal Itching Treatment \| Consult Female Gynaecologist | No | Yes | Gynecology clarification works. |
| Gynecology | `yoni me jalan` | `yoni me jalan` | `needs_clarification` | We need one more detail | Vaginal Itching Treatment \| Consult Female Gynaecologist | No | Yes | Gynecology clarification works. |
| Gynecology | `white discharge` | `white discharge` | `direct_match` | Best match found | Advanced Vaginal Infection Treatment \| Consult Female Gynaecologist | Yes | Yes | Correct gynecology top result. Not intercepted because body term is absent. |
| Gynecology | `periods late` | `periods late` | `direct_match` | Best match found | Irregular Periods Treatment \| Consult Female Gynaecologist | Yes | Yes | Correct gynecology top result. |
| Gynecology | `irregular periods` | `irregular periods` | `direct_match` | Best match found | Irregular Periods Treatment \| Consult Female Gynaecologist | Yes | Yes | Correct gynecology top result. |
| Safety | `pregnancy bleeding` | `pregnancy bleeding` | `doctor_fallback` | Talk to a doctor | Vaginal BleedingTreatment \| Consult Female Gynaecologist | No | Yes | Pregnancy safety override works. |
| Safety | `chest pain` | `chest pain` | `doctor_fallback` | Talk to a doctor | Left Nipple Pain in Male Treatment | No | Yes | Existing risky-term fallback works. |
| Safety | `bahut bleeding ho rahi hai` | `bahut bleeding ho rahi hai` | `doctor_fallback` | Talk to a doctor | Vaginal BleedingTreatment \| Consult Female Gynaecologist | No | Yes | Existing risky-term fallback works. |
| Safety | `saans lene mein dikkat` | `saans lene mein dikkat` | `doctor_fallback` | Talk to a doctor | Turbinate Reduction Surgery - Diagnosis & Recovery | No | Yes | Breathing safety fallback now works. |
| Safety | `saans lene me dikkat` | `saans lene me dikkat` | `doctor_fallback` | Talk to a doctor | Deviated Nasal Septum Treatment \| Bent Nose Correction | No | Yes | Breathing safety fallback covers `me` variant. |
| Safety | `saans nahi aa rahi` | `saans nahi aa rahi` | `doctor_fallback` | Talk to a doctor | Best Surrogacy Options in India \| Find Surrogate Mother | No | Yes | Breathing safety fallback hides bad retrieval top. |
| Safety | `breathing difficulty` | `breathing difficulty` | `doctor_fallback` | Talk to a doctor | Nasal Valve Collapse (NVC) Surgery \| Complete Treatment | No | Yes | Breathing safety fallback works. |
| Safety | `shortness of breath` | `shortness of breath` | `doctor_fallback` | Talk to a doctor | Nose Reshaping | No | Yes | Breathing safety fallback works. |
| Safety | `breathless` | `breathless` | `doctor_fallback` | Talk to a doctor | Silent Miscarriage Treatment | No | Yes | Breathing safety fallback hides bad retrieval top. |
| Regression | `naak band` | `naak band` | `direct_match` | Best match found | Nasal Valve Collapse (NVC) Surgery \| Complete Treatment | Yes | Yes | Not forced to fallback; explicit breathing difficulty is required. |
| Regression | `bawasir ka ilaj` | `bawasir ka ilaj` | `direct_match` | Best match found | Laser Treatment for Piles | Yes | Yes | Clear treatment query remains stable. |
| Regression | `kharrate` | `kharrate` | `needs_confirmation` | Likely match | Deviated Nasal Septum Treatment \| Bent Nose Correction | Yes | Yes | ENT/nasal-adjacent. Still not ideal if product expects a snoring page, but not a body-system regression. |
| Regression | `pet ki pathri` | `pet ki pathri` | `needs_clarification` | A little more detail would help | Gallstone (Gallbladder) Surgery | No | Yes | Existing ambiguous stone clarification remains stable. |
| Regression | `bodypain` | `body pain` | `needs_clarification` | We need one more detail | Left Nipple Pain in Male Treatment | No | Yes | Normalizer works and broad symptom no longer shows wrong treatment card. |
| Regression | `chashma hatana` | `chashma hatana` | `direct_match` | Best match found | SMILE Eye Surgery For Vision Correction - Laser Operation For Eyes | Yes | Yes | Ophthalmology intent remains stable. |
| Regression | `bachha nahi ho raha` | `bachha nahi ho raha` | `direct_match` | Best match found | Blocked Fallopian Tubes Treatment: Consult Today | Yes | Yes | Fertility intent remains stable. |

## Findings

### Pass: Procto body-system guard

The proctology guard successfully intercepts stool/rectal/anus terms plus generic symptoms. This prevents the observed class of failures where `khoon`, `blood`, or `bleeding` pulls vaginal or vascular pages to the top.

Important examples:

- `tatti mei khoon aana` now returns `needs_clarification`, not `direct_match`.
- `blood in stool` now returns `needs_clarification`, not a vascular treatment card.
- `peshab me khoon` still retrieves vaginal bleeding as top result, but the urology guard hides the treatment card and asks clarification.

### Pass: Urology guard

Urine/kidney terms plus burning, blood, pain, or flow context route to `needs_clarification`.

`urine ruk raha hai` is safe, but it is handled by existing broad body-part logic rather than the new urology guard because the current urology symptom list includes `rukna`, not `ruk`.

### Pass: Gynecology guard

Vaginal/period/yoni terms plus symptoms route to `needs_clarification`.

`white discharge` direct-matches vaginal infection. This is acceptable because retrieval is correct and the query is strongly gynecology-specific, but a future synonym layer could classify `white discharge` as gynecology even without an explicit body term.

### Pass: Existing regressions mostly stable

Clear treatment and known flows remain acceptable:

- `bawasir ka ilaj` -> piles direct match.
- `pet ki pathri` -> stone clarification.
- `bodypain` -> normalized to `body pain` and clarified.
- `chashma hatana` -> ophthalmology direct match.
- `bachha nahi ho raha` -> fertility direct match.

`kharrate` remains only partially ideal: it is ENT/nasal-adjacent, but top retrieval is deviated nasal septum rather than a snoring-specific page.

### Pass: Breathing safety fallback

The previous Hinglish breathing safety gap is fixed.

Focused retest results:

- `saans lene mein dikkat` -> `doctor_fallback`
- `saans lene me dikkat` -> `doctor_fallback`
- `saans nahi aa rahi` -> `doctor_fallback`
- `breathing difficulty` -> `doctor_fallback`
- `shortness of breath` -> `doctor_fallback`
- `breathless` -> `doctor_fallback`

The fallback is conservative: it does not force ordinary ENT/nose queries into safety fallback.

- `naak band` remains `direct_match`.
- `kharrate` remains `needs_confirmation` and ENT/nasal-adjacent.

## Overall Verdict

The body-system disambiguation router is a meaningful safety and relevance improvement for the current target scope.

Ship status for the latest router:

- Procto guard: Pass
- Urology guard: Pass
- Gynecology guard: Pass
- Pregnancy/chest/severe bleeding safety: Pass
- Breathing difficulty safety: Pass
- Regression stability: Pass with minor residual retrieval issue for `kharrate`
