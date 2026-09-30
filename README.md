# Comena Onboarding Readiness Auditor

> **ALL DATA IN THIS REPO IS SYNTHETIC.** No real customer data, catalogs, or
> purchase orders. Nothing here proves performance on a real distributor catalog.

## Benchmark: PO → SKU matching (A vs B vs C)

Frozen test split: **200 rows**, **275-SKU** catalog, one LLM extraction run
(10 batches, 0 fallbacks), model `space-bunny-free` via OpenCode Zen,
temperature 0. Test set SHA256
`3ccceeae8f9a2bb19538f6f7c95ba9ebaff0a94a5a5ab855c14fa0216e34cf69`.

| Matcher | Top-1 | False-match | Gap recall | Gap precision | Review rate | Auto rate |
|---|---|---|---|---|---|---|
| A baseline (fuzzy) | 64.5% | 11.0% | 40.0% | 27.9% | 29.0% | 49.5% |
| B attribute + LLM | 78.5% | **2.0%** | 90.0% | 52.9% | 12.0% | 62.5% |
| C hybrid | **82.0%** | 6.0% | 90.0% | 52.9% | 0.0% | 74.5% |

UoM pack-size accuracy: **21.7%** on the 23 rows that state a pack unit.
Cost of the frozen run: **10 LLM calls, 68,449 tokens, 0 fallbacks** (~17 min
wall-clock, batches dispatched 8-way concurrent).

**Read B and C carefully.** C wins on top-1 (82.0%) but has a *higher*
false-match rate than B (6.0% vs 2.0%) because its fuzzy tiebreak auto-resolves
cases B would safely review. If a wrong SKU written into an ERP costs more than
a review, **B is the safer matcher**, and the top-1 gap is only 3.5 points.
C's review rate of 0.0% is not a win; it is every ambiguity pushed to a coin flip.

### Honest limitations

- **Synthetic, self-authored data.** Descriptions were generated from templates,
  not taken from a real distributor. The 64.5% fuzzy baseline in particular
  flatters the incumbent: real customer wording is harder than these templates.
- **Small catalog (275 SKUs).** A real catalog is tens of thousands of rows; at
  50k the O(items × catalog) loop in A and B is the first thing to fall over.
- **No production traffic.** No OCR, no scanned PDFs, no multi-page documents.
- **Weak, narrow UoM result.** 21.7% on 23 rows; the conversion table covers only
  a handful of pack units and the sample is too small to trust.
- **One run, one model, temperature 0.** No variance estimate; a different model
  or a re-run could move these numbers.
- **One batch size (20) and one prompt** for extraction; either could change B/C.
- **`customer_pn` rows are unscoreable by design.** 0/20 is a property of the
  dataset (a bare customer part number shares no token with any description), not
  a fixable matcher bug.

### What this does NOT prove

- That these numbers transfer to a real catalog or real purchase orders.
- That the matcher is production-ready at catalog scale or under OCR noise.
- That Comena's actual catalog behaves like the hard negatives imagined here
  (`3/8-16` vs `3/8-24`, `Zinc` vs `Zinc Yellow`, `Grade 5` vs `Grade 8`,
  `6203-2RS` vs `6203-2Z` vs `6203-ZZ`).
- Anything about matching accuracy on customer part-number cross-references.

### Reproduce the numbers

One command (needs Python 3.11+ with `backend/requirements.txt` installed into
`backend/.venv`, and a real `LLM_API_KEY` in `backend/.env` — see *Run it* below):

```bash
backend/.venv/Scripts/python.exe benchmark/run_eval.py --split test
```

The harness re-checks `test.csv` against its SHA256 in `benchmark/data/manifest.json`
**before** scoring, so a silently edited test set cannot produce a flattering
number. Full protocol, failure breakdown, and per-row failure list live in
[`BENCHMARK.md`](BENCHMARK.md) and `benchmark/results/`.

---

## What this service is

A pre-flight check for deploying AI order-entry agents at industrial
distributors. Upload a prospect's sample purchase orders (PDF) and their
product catalog (CSV); the service extracts every line item via an LLM,
fuzzy-matches descriptions to catalog SKUs, and returns a readiness report
that surfaces the friction a deployment would hit **before** the sales team
promises a smooth go-live.

It is not the Comena agent itself — it is the tool that makes the agent's
onboarding predictable: match rate, catalog gaps, unit-of-measure mismatches,
ERP mapping flags, and recommendations.

## Pipeline

```
PDF (pdfplumber) → structured JSON (LLM, OpenAI-compatible API)
                 → fuzzy SKU match (rapidfuzz, token_sort_ratio @ 85)
                 → ReadinessReport JSON
```

Stateless by design: uploads are written to a temp directory, analyzed, and
deleted in a `finally` block. No database, no persistence.

## Run it

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# .venv/bin/python -m pip install -r requirements.txt     # macOS/Linux

cp .env.example .env        # then set LLM_API_KEY (never commit .env)
.venv/Scripts/python -m uvicorn app.main:app --reload
```

The LLM settings work with any OpenAI-compatible endpoint; the default points
at [OpenCode Zen](https://opencode.ai/zen) (`https://opencode.ai/zen/v1`,
model `space-bunny-free`). For Groq, set `LLM_API_BASE=https://api.groq.com/openai/v1`
and a Groq model id.

## Test it

Sample fixtures (two POs plus a catalog with deliberate gaps, one fuzzy
near-match, and two unit mismatches) live in `samples/` and can be regenerated
with `backend/.venv/Scripts/python.exe samples/generate_fixtures.py`.

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/api/analyze \
  -F "pdfs=@samples/po-acme-4102.pdf" \
  -F "pdfs=@samples/po-premium-0088.pdf" \
  -F "catalog=@samples/catalog.csv"
```

Example response (trimmed):

```json
{
  "documents_processed": 2,
  "total_line_items": 7,
  "matched_items": 5,
  "match_rate": 0.7143,
  "overall_score": 71.4,
  "unmatched_descriptions": ["M8 x 40 Socket Head Cap Screw Black", "..."],
  "catalog_gaps": [
    {"description": "Stainless Steel Cable Ties 11 inch",
     "best_candidate_sku": "TYW-114-316", "best_candidate_score": 41.9}
  ],
  "unit_mismatches": [
    {"sku": "VLV-BV-075-BR", "description": "Ball Valve 3/4 Brass FIP",
     "po_unit": "Carton", "catalog_unit": "Ea"}
  ],
  "erp_mapping_flags": ["2 of 7 line items have no catalog SKU and would require manual ERP entry.", "..."],
  "recommendations": ["Review the unmatched descriptions and add catalog aliases before go-live.", "..."]
}
```

## API

| Endpoint | Description |
| --- | --- |
| `GET /health` | Liveness probe. |
| `POST /api/analyze` | Multipart form: `pdfs` (1+ PDF files) and `catalog` (1 CSV file). Returns a `ReadinessReport`. |

### Limits and validation

- Only `.pdf` and `.csv` uploads are accepted; filenames are sanitized and 10 MB max per file.
- Errors are returned as `{"detail": "..."}`:
  `400` wrong file type/size, `422` unreadable PDF or invalid catalog,
  `502` LLM unavailable or returned unparseable output.

## Configuration (`.env`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_API_KEY` | — | API key for the OpenAI-compatible endpoint (required). |
| `LLM_API_BASE` | `https://opencode.ai/zen/v1` | Endpoint base URL. |
| `LLM_MODEL` | `space-bunny-free` | Chat model used for extraction. |
| `UPLOAD_DIR` | `uploads` | Scratch directory for in-flight uploads. |
| `MATCH_THRESHOLD` | `85` | Minimum fuzzy score (0–100) to bind a SKU. |

## Layout

```
backend/app/
├── main.py              # app factory, CORS, domain-error → HTTP mapping
├── config.py            # pydantic-settings, reads .env
├── exceptions.py        # PDFExtractionError, LLMParsingError, CatalogValidationError
├── models/schemas.py    # LineItem, ExtractedDocument, ReadinessReport (Pydantic v2)
├── services/            # business rules: pdf_extractor, llm_parser, sku_matcher, analyzer
├── api/routes.py        # /health, /api/analyze (thin HTTP layer)
└── utils/file_handler.py# upload validation, sanitized saves, cleanup
```

Layering is strict: routes parse input and delegate; services hold the
business rules and never import FastAPI; utils handle files only.
