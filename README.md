# Comena Onboarding Readiness Auditor

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
