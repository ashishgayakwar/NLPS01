# Current Search Logic Audit

This document describes the current NLP search and routing behavior exactly as it exists in the codebase now. It is written for product and engineering readers, so it explains both the user journey and the code paths that drive it.

Files inspected:

- `app.py`
- `search.py`
- `intent_router.py`
- `catalog.py`
- `api/index.py`

No application behavior is changed by this document.

## 1. End-to-end flow

### User opens the homepage

The root route `GET /` in `app.py` returns a single inline HTML page stored in `HTML_PAGE`.

At app startup, `app.py` also initializes the search engine:

```python
engine = SemanticSearch()
```

That means the catalog is indexed once when the FastAPI app process starts. If `OPENAI_API_KEY` is missing, startup fails because `SemanticSearch` requires it.

The homepage shows:

- Pristyn logo
- A search input
- A Search button
- Popular search chips
- An empty state saying "Start typing to find a treatment"
- A consultation modal, hidden until opened

### User types a query and searches

The frontend JavaScript listens to:

- typing in the search input
- Enter key
- Search button click

Typing triggers a debounced search after 300 ms. Pressing Enter or clicking Search calls `doSearch()` immediately.

`doSearch()` reads the input using:

```javascript
const query = q.value.trim();
```

It only trims leading and trailing whitespace. It does not normalize repeated words, repeated phrases, or multiple internal spaces.

If the query is empty, the UI returns to the empty state. If the query is non-empty, the frontend calls:

```javascript
fetch("/search?q=" + encodeURIComponent(query))
```

### User lands on `/?q=...`

On page load, the frontend runs:

```javascript
const params = new URLSearchParams(window.location.search);
const initialQuery = params.get("q");
```

If `q` exists, the input value is set to that query and `doSearch()` runs.

The root route still serves the same HTML page. The `q` parameter is handled entirely by frontend JavaScript after the page loads.

### Frontend calls `/search`

The JSON route is:

```python
@app.get("/search")
def search(q: str = Query(..., min_length=1), top_k: int = 5):
```

The backend flow is:

1. Run retrieval:

   ```python
   results = engine.search(q, top_k=top_k)
   ```

2. Run routing:

   ```python
   decision = route_patient_intent(q, results)
   ```

3. Return JSON:

   ```python
   {
     "query": q,
     "results": results,
     "decision": asdict(decision)
   }
   ```

The backend also prints intent debug logs to stdout.

### Backend returns results

The response contains:

- the original query
- top search results from `search.py`
- one routing decision from `intent_router.py`

Each result is a catalog item plus search scores:

- `score`
- `semantic_score`
- `bm25_score`

### UI decides what to render

The frontend receives the JSON and calls:

```javascript
render(data.results, query, data.decision);
```

Rendering is driven mainly by `decision.state`.

Current states:

- `direct_match`
- `needs_confirmation`
- `needs_clarification`
- `doctor_fallback`

Important current behavior:

- `doctor_fallback` shows only a consultation card.
- `direct_match`, `needs_confirmation`, and `needs_clarification` all show a primary treatment card and alternatives.
- Therefore, in the current code, `needs_clarification` still shows treatment cards.

## 2. Search retrieval logic

### How catalog items are indexed

`catalog.py` defines `CATALOG`, a static Python list of 363 treatment-like entries.

Each catalog item can include:

- `id`
- `name`
- `hindi_name`
- `slug`
- `url`
- `description`
- `hindi_description`
- `category`
- `hinglish_terms`

`search.py` creates one searchable document per catalog item using `get_searchable_text(item)`.

### What text fields are searched

`catalog.get_searchable_text(item)` combines these fields:

```python
parts = [
    item.get("name", ""),
    item.get("hindi_name", ""),
    item.get("slug", ""),
    " ".join(item.get("hinglish_terms", [])),
    item.get("description", ""),
    item.get("hindi_description", ""),
    item.get("category", ""),
]
```

The non-empty parts are joined with `" | "`.

The same combined text is used for both semantic embedding search and BM25 lexical search.

### How OpenAI embeddings are used

`search.py` uses OpenAI embeddings:

```python
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072
```

At startup:

1. Every catalog item is converted to searchable text.
2. Texts are embedded in batches through the OpenAI Embeddings API.
3. Embeddings are converted to `np.float32`.
4. Vectors are L2-normalized.

At query time:

1. The query is embedded using the same model.
2. The query vector is normalized.
3. Semantic similarity is calculated with dot product:

   ```python
   semantic_scores = np.dot(self.embeddings, query_embedding)
   ```

Because both vectors are normalized, this dot product behaves like cosine similarity.

### How BM25 is used

The BM25 index is also built at startup.

Tokenization is:

```python
re.findall(r"[\w]+", text.lower(), flags=re.UNICODE)
```

This lowercases text and extracts word-like tokens. It is simple token matching; it does not stem, lemmatize, translate, or understand spelling variants unless those variants are already present in the catalog text.

BM25 constants:

```python
BM25_K1 = 1.5
BM25_B = 0.75
```

For each query term, BM25 checks term frequency in each document and applies the standard BM25 length-normalized formula.

### How semantic and BM25 scores are combined

Both score arrays are min-max normalized per query:

```python
_min_max_normalize(scores)
```

If all scores are the same, normalization returns zeros.

The final score is:

```python
scores = (
    SEMANTIC_WEIGHT * normalized_semantic_scores
    + BM25_WEIGHT * normalized_bm25_scores
)
```

Current weights:

```python
SEMANTIC_WEIGHT = 0.75
BM25_WEIGHT = 0.25
```

The top results are selected by sorting this combined score descending.

### What fields are returned per result

Each returned result is a copy of the catalog item plus:

- `score`: combined normalized score
- `semantic_score`: raw embedding dot product
- `bm25_score`: raw BM25 score

The original catalog fields are preserved, including:

- `url`
- `name`
- `description`
- `slug`
- `hinglish_terms`
- `hindi_name`
- `hindi_description`
- `category`

### Normalization and thresholding

Retrieval itself does not apply a pass/fail threshold. It always returns the top `top_k` results if the catalog exists.

Thresholding happens later in `intent_router.py`.

Important limitation: because semantic and BM25 scores are min-max normalized per query, the best result for a weak or unsupported query can still receive a high normalized combined score. This can make unrelated results look routeable to the router.

## 3. Intent routing logic

The router lives in `intent_router.py`.

It receives:

- raw user query
- search results from `search.py`

It returns a `JourneyDecision`:

```python
JourneyDecision(
    state,
    title,
    message,
    primary_result,
    alternatives,
    clarifier_question,
    clarifier_chips,
    safety_note,
)
```

### Current routing order

`route_patient_intent(query, results)` runs in this exact order:

1. Normalize query:

   ```python
   normalized_query = " ".join(query.lower().strip().split())
   ```

2. Read top result and top score.
3. Check risky terms.
4. Check no results or low top score.
5. Check ambiguous stone intent.
6. Check broad body-part intent.
7. Check high-score direct match.
8. Check medium-score needs confirmation.
9. Else return general clarification.

### Safety / risky terms

Risky terms are:

```python
(
    "bahut bleeding",
    "severe bleeding",
    "chest pain",
    "emergency",
)
```

If any of these substrings appear in the normalized query, the router immediately returns `doctor_fallback`.

This happens before score checks, stone handling, broad body-part clarification, or direct matching.

### No result / low confidence fallback

If there are no results or the top combined score is below `0.45`, the router returns `doctor_fallback`.

Current reason text passed internally:

```python
"We could not confidently match this to a treatment."
```

This reason becomes part of `safety_note`.

### Ambiguous stone handling

Broad stone terms are:

```python
("pathri", "patthri", "pattari", "stone")
```

Specific stone terms are:

```python
(
    "kidney",
    "gurda",
    "gurde",
    "urine",
    "urinary",
    "peshab",
    "gallbladder",
    "gall bladder",
    "gallstone",
    "pit ki thaili",
    "pitt ki thaili",
)
```

If a query contains a broad stone term and does not contain a specific stone term, the router returns `needs_clarification`.

Example: `pet ki pathri` contains `pathri` and no specific stone term, so it triggers this branch.

Decision copy:

- State: `needs_clarification`
- Title: `A little more detail would help`
- Message: `Pathri can refer to different stone-related conditions, so we should narrow this before choosing a treatment.`
- Question: `Pathri can mean different types of stones. Which one is closest?`
- Chips: `Kidney / urine stone`, `Gallbladder stone`, `Not sure`
- Safety note: `This is only a search guide, not a diagnosis.`

### Broad body-part clarification

The router has body-part chip groups for:

- `kaan`
- `ear`
- `pet`
- `stomach`
- `urine`
- `peshab`
- `ghutna`
- `knee`

If one of those terms appears in the query, and the query is not considered a clear treatment query, the router returns `needs_clarification`.

Decision copy:

- State: `needs_clarification`
- Title: `A little more detail would help`
- Message: `This sounds broad, so a symptom or problem type will help narrow the right treatment.`
- Question: `Which of these is closest to what you mean?`
- Chips: body-part-specific chips
- Safety note: `This is only a search guide, not a diagnosis.`

Examples:

- `kaan mei dikkat` gets ear-related chips.
- `pet dard` gets stomach/pet-related chips.
- `stomach pain` gets stomach-related chips.

### Direct condition terms

Clear treatment terms are:

```python
(
    "bawasir",
    "bavasir",
    "bawaseer",
    "piles",
    "kidney stone",
    "gallstone",
    "gall bladder stone",
    "gallbladder stone",
    "hernia",
    "kharrate",
    "snoring",
    "bachha nahi",
    "bachcha nahi",
    "bacha nahi",
    "infertility",
)
```

These terms prevent broad body-part clarification when present. They do not by themselves force `direct_match`; the final state still depends on score thresholds after earlier branches.

Specific stone intent also counts as clear treatment intent when the query contains both a broad stone term and a specific stone term.

### Score thresholds

After the rule checks above:

- `top_score >= 0.85` returns `direct_match`
- `top_score >= 0.65` returns `needs_confirmation`
- otherwise returns `needs_clarification`

### State: `direct_match`

Trigger:

- No earlier risky, low-score, ambiguous stone, or broad body-part rule triggered.
- Top combined score is at least `0.85`.

Decision copy:

- Title: `Best match found`
- Message: `This looks like a strong treatment match for your query.`
- Question: empty
- Chips: none
- Safety note: `Confirm symptoms with a qualified doctor before making care decisions.`

Current UI behavior:

- Shows result header.
- Shows a primary treatment card.
- Shows alternatives.
- Shows consultation CTA in the primary card.
- Does not show clarifier chips.

### State: `needs_confirmation`

Trigger:

- No earlier rule triggered.
- Top combined score is at least `0.65` and below `0.85`.

Decision copy:

- Title: `Likely match`
- Message: `This may be what you are looking for, but a quick confirmation would help.`
- Question: `Is this the treatment or symptom area you meant?`
- Chips: `yes, show this`, `show alternatives`, `talk to doctor`
- Safety note: `Search results are informational and do not replace medical advice.`

Current UI behavior:

- Shows result header.
- Shows clarifier chips.
- Shows a primary treatment card with badge `Likely Match`.
- Shows alternatives.
- Shows consultation CTA in the primary card.

### State: `needs_clarification`

Trigger:

- Ambiguous stone query.
- Broad body-part query without clear treatment intent.
- Or final fallback when score is below `0.65` but not below `0.45`.

Decision copy depends on the branch.

Ambiguous stone title/message:

- Title: `A little more detail would help`
- Message: `Pathri can refer to different stone-related conditions, so we should narrow this before choosing a treatment.`

Broad body-part title/message:

- Title: `A little more detail would help`
- Message: `This sounds broad, so a symptom or problem type will help narrow the right treatment.`

General clarification title/message:

- Title: `Help us narrow it down`
- Message: `There are a few possible treatment areas for this query.`

Current UI behavior:

- Shows result header.
- Shows clarifier chips.
- Shows a primary treatment card with badge `Starting Point`.
- Shows alternatives.
- Shows consultation CTA in the primary card.

Important: treatment cards are currently shown for `needs_clarification`.

### State: `doctor_fallback`

Trigger:

- Query contains a risky term.
- Or no results.
- Or top combined score is below `0.45`.

Decision copy from router:

- Title: `Talk to a doctor`
- Message: `This may need clinical context before choosing a treatment path.`
- Question: `Would you like to describe your symptoms in a bit more detail?`
- Chips: `book consultation`, `talk to doctor`, `share symptoms`
- Safety note includes the reason and emergency-care language.

Current UI behavior:

- `app.py` does not use the router title/message directly for the visible fallback card.
- It renders a hardcoded consultation card:
  - Title: `Talk to a doctor`
  - Copy: `This may need clinical context before choosing a treatment path.`
  - Secondary copy: `We could not confidently map this to one treatment. A Pristyn care coordinator can help route you to the right specialist.`
  - Safety note if present
  - Buttons: `Book Free Consultation`, `Call Now`
- Does not show treatment cards.
- Does not show clarifier chips.

## 4. Query transformation logic

### Popular chip click

Popular chips are buttons with:

```javascript
onclick="setQ(this)"
```

`setQ(el)` does:

```javascript
q.value = el.innerText;
doSearch();
```

This replaces the input value with the chip text and runs a search.

It does not update the browser URL.

### Clarifier chip click

Clarifier chips are rendered as links:

```javascript
'<a class="clarifier-chip" href="/?q=' + encodeURIComponent(query + ' ' + chip) + '">'
```

Current behavior:

- Appends raw chip text to the current query.
- Navigates to `/?q=<old query> <chip text>`.
- The page reloads.
- On load, frontend reads `q`.
- `doSearch()` runs again.

Example:

- Current query: `pet dard`
- Click chip: `pet dard`
- New URL query: `pet dard pet dard`

There is no structured target query for chips.

### Not sure click

`Not sure` is just a normal clarifier chip string in current code.

Current behavior:

- It navigates to `/?q=<old query> Not sure`.
- It does not open the consultation modal.
- It does not trigger a special fallback by itself.

### Choose this click

Alternative cards include:

```javascript
'<a class="read-more-link choose-link" href="/?q=' + encodeURIComponent(it.name || '') + '">Choose this</a>'
```

Current behavior:

- Replaces the query with the selected treatment name.
- Navigates to `/?q=<treatment name>`.
- On load, frontend searches that treatment name.

This does not append to the old query.

### Read more click

There are two Read more behaviors:

- Primary card: `Read more on Pristyn ->`
- Alternative card: `Read more`

Both link to the catalog item's `url`, open in a new tab, and do not change the in-app query.

### Book Free Consultation click

Any element with `.consultation-trigger` is caught by a document-level click listener.

Behavior:

1. Prevent default link behavior.
2. Read `data-treatment`.
3. Open the existing consultation modal.
4. Reset the form.
5. Set default city to `Gurugram`.
6. Add/select the treatment option in the modal.

The modal submit is frontend-only. It validates name, phone, city, and treatment, then shows a local success message. There is currently no backend lead submission.

### Specific answers

Does any action append to the previous query?

- Yes. Clarifier chips append raw chip text to the previous query.

Does any action replace the query?

- Yes. Popular chips replace the input value.
- `Choose this` replaces the URL `q` with the selected treatment name.
- Loading `/?q=...` replaces the input with the URL query.

Are repeated tokens cleaned up?

- No. Only leading/trailing whitespace is trimmed before fetch.

Is there any clarification-depth guard?

- No. There is no `clarify=1` parameter and no repeated-clarification guard.

Can the same clarification repeat?

- Yes. A user can click the same clarifier chip repeatedly, creating repetitive queries like `pet dard pet dard pet dard`.
- The router can also return `needs_clarification` again if the expanded query still matches a broad body-part or ambiguous term branch.

## 5. Current UI behavior by state

### `direct_match`

Rendered UI:

- Header with router title/message.
- Section label: `Best match found`.
- Primary treatment card.
- Badge: `Best Match`.
- Alternatives section if alternatives exist.
- Consultation CTA inside the primary card.
- Call Now button.
- Read more link.

Treatment cards are shown.

### `needs_confirmation`

Rendered UI:

- Header with router title/message.
- Clarifier question.
- Clarifier chips.
- Section label: `Please confirm the closest match`.
- Primary treatment card.
- Badge: `Likely Match`.
- Alternatives section if alternatives exist.
- Consultation CTA inside the primary card.
- Call Now button.
- Read more link.

Treatment cards are shown.

### `needs_clarification`

Rendered UI:

- Header with router title/message.
- Clarifier question.
- Clarifier chips.
- Section label: `Likely starting point`.
- Primary treatment card.
- Badge: `Starting Point`.
- Alternatives section if alternatives exist.
- Consultation CTA inside the primary card.
- Call Now button.
- Read more link.

Treatment cards are shown, even though the state asks for clarification.

### `doctor_fallback`

Rendered UI:

- One consultation card.
- Title: `Talk to a doctor`.
- Hardcoded fallback copy.
- Optional safety note from router.
- Book Free Consultation button.
- Call Now button.

Treatment cards are not shown.

## 6. Current known risks

### Search can over-route

Because retrieval always returns top results and scores are min-max normalized per query, unsupported or vague queries can still get a high top score. The router may then show `needs_confirmation` or `direct_match` for an unrelated treatment.

Examples at risk:

- `body pain`
- `body rash`
- random unsupported text
- vague symptoms without a supported specialty

### Router can block valid results

Risky terms are substring rules. If a valid treatment query contains one of the risky substrings, it routes to `doctor_fallback` before retrieval confidence or catalog relevance is considered.

Broad body-part rules also override high-scoring results when the query includes terms like `pet`, `stomach`, `kaan`, or `knee` and does not contain a clear treatment term.

### User can get stuck

Clarifier chips append text instead of resolving to a clean target query. A user can repeat the same broad query by clicking the same chip.

Examples:

- `pet dard` -> click `pet dard` -> `pet dard pet dard`
- `kaan mei dikkat` -> click `kaan dard` -> `kaan mei dikkat kaan dard`
- `pet ki pathri` -> click `Not sure` -> `pet ki pathri Not sure`

There is no guard to stop repeated clarifications.

### Local and production may differ

`api/index.py` imports the same `app` object from `app.py`, so deployment should use the same code path if the deployed code is current.

However, production may differ if:

- latest local code is not deployed
- environment variables differ
- OpenAI API availability differs
- the process has old code loaded
- static assets differ
- a previous deployment is still serving traffic

### Fallback may be too aggressive

The risky-term fallback is intentionally early and simple. It may route some queries to `doctor_fallback` even when a catalog result exists.

The low-score fallback threshold is `0.45`, but because scores are normalized per query, many weak queries may still score above this threshold and avoid fallback.

So fallback can be both too aggressive for some risky substrings and not aggressive enough for unrelated but high-normalized retrieval results.

### Clarification may be too broad

The body-part clarification lists are small and manually defined. They may not cover the user's actual intent.

If no body-part-specific chips match, generic chips are used:

- `pain`
- `bleeding`
- `swelling`
- `infection`
- `operation`
- `doctor consult`

These generic chips also append to the query, so they can make the query longer without resolving intent.

## 7. Test matrix

These are current expected behaviors based on the inspected code. Exact top treatment names depend on the OpenAI embedding response and the current catalog content.

| Query | Current expected state | Current expected UI | Why |
|---|---|---|---|
| `bawasir ka ilaj` | Likely `direct_match` | Best-match treatment card plus alternatives | `bawasir` is a clear treatment term and catalog has piles/proctology content; if score is at least `0.85`, router returns `direct_match`. |
| `kharrate` | Score-dependent, likely `needs_confirmation` or `direct_match` | Treatment card plus alternatives | `kharrate` is listed as a clear treatment term, but state still depends on top score. Clear term prevents broad clarification but does not force direct match. |
| `bachha nahi ho raha` | Likely `direct_match` or `needs_confirmation` | Treatment card plus alternatives | `bacha nahi` is a clear treatment term and catalog includes infertility-related Hinglish terms. Final state depends on top score. |
| `pet ki pathri` | `needs_clarification` | Clarifier chips plus `Starting Point` treatment card and alternatives | Contains broad stone term `pathri` without a specific stone term, so ambiguous stone branch triggers. Current UI still shows treatment cards. |
| `stomach pain` | `needs_clarification` if score is at least `0.45` | Clarifier chips plus `Starting Point` treatment card and alternatives | `stomach` is a broad body-part key and no clear treatment term is present. |
| `pet dard` | `needs_clarification` if score is at least `0.45` | Clarifier chips plus `Starting Point` treatment card and alternatives | `pet` is a broad body-part key and no clear treatment term is present. |
| `kaan mei dikkat` | `needs_clarification` if score is at least `0.45` | Ear-related clarifier chips plus `Starting Point` treatment card and alternatives | `kaan` is a broad body-part key and no clear treatment term is present. |
| `body pain` | Score-dependent; can become `direct_match` or `needs_confirmation` | Treatment card plus alternatives, potentially unrelated | There is no broad symptom rule for `body pain`. If retrieval score is high enough, router uses score thresholds. |
| `body rash` | Score-dependent; often `needs_confirmation` if top score is at least `0.65` | Likely-match treatment card plus alternatives | No risky term and no broad body-part key. Unsupported query can still get high normalized retrieval score. |
| `chest pain` | `doctor_fallback` | Consultation fallback card only | `chest pain` is in `RISKY_TERMS`, checked before all other routing. |
| `bahut bleeding ho rahi hai` | `doctor_fallback` | Consultation fallback card only | Contains risky substring `bahut bleeding`. |
| `random unsupported text` | Score-dependent; may become `needs_confirmation` | Possibly unrelated likely-match card | Retrieval still returns nearest catalog items; min-max normalized top score may exceed router thresholds. |

## 8. Summary

### What the system is currently good at

- It can search across English, Hindi, and Hinglish catalog text.
- It combines semantic retrieval with lexical BM25, which helps both meaning-based and exact-term searches.
- It has simple safety routing for a few urgent phrases.
- It has manual clarification branches for common ambiguous areas like `pathri`, `pet`, `kaan`, `urine`, and `knee`.
- It returns enough debug fields in JSON for engineers to inspect retrieval scores and catalog metadata.

### Where the system is brittle

- Per-query min-max normalization can make weak matches appear strong.
- The router relies heavily on top combined score thresholds.
- Broad symptom queries like `body pain` are not specially handled.
- Clarifier chips append raw text to the old query, which can create loops and repetitive queries.
- `Not sure` is treated as search text instead of a consultation action.
- `needs_clarification` still displays treatment cards, which can feel premature.
- Doctor fallback copy currently includes internal matching language in the UI.
- Safety coverage is limited to a short list of risky substrings.

### Most risky layer

The most risky layer is query transformation, followed closely by router thresholding.

The retrieval layer can return imperfect nearest neighbors, but that is expected for semantic search. The bigger product risk is that the router and UI sometimes treat those nearest neighbors as patient-facing treatment recommendations, and clarification clicks can make the query worse instead of resolving intent.

UI rendering is also risky for `needs_clarification` because it currently shows treatment cards before the user has answered the clarifying question.
