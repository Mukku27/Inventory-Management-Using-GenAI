# CLAUDE.md

This file provides guidance for Claude Code when working with this repository.

## Project Overview

AI-powered Inventory Management System using Streamlit and Google Gemini AI. Users can query inventory via natural language (converted to SQL), view dashboards, modify inventory, upload Excel files, and generate AI-driven insights/reports.

## Tech Stack

- **Python 3.11+**, **Streamlit** (web UI), **SQLite3** (database)
- **Google Gemini AI** (`google-generativeai`) for SQL generation, insights, predictions
- **pandas**, **plotly**, **openpyxl** for data processing and visualization
- **pytest**, **ruff**, **pip-audit** for testing, linting, security

## Development Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Environment variables** (create a `.env` file):
```
GOOGLE_API_KEY=your_google_gemini_api_key_here
PANDASAI_API_KEY=your_pandasai_api_key_here   # optional
```

**Initialize the database** (generates `product_inventory.db` with 10,000 sample products):
```bash
python database.py
```

**Run the app:**
```bash
streamlit run app.py
```

## Common Commands

```bash
pytest                # run all tests
ruff check .          # lint
pip-audit             # scan dependencies for vulnerabilities
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit UI — dashboard, query, Excel upload, analytics |
| `database.py` | SQLite schema, sample data generation |
| `analytics.py` | AI-powered insights, predictions, report generation |
| `prompt.py` | Prompt engineering for SQL generation via Gemini |
| `guardrails.py` | SQL safety validation — blocks destructive queries |
| `excel_processing.py` | Excel parsing, column mapping, bulk DB updates |
| `utils.py` | SQL execution helpers, column mapping utilities |
| `config.py` | Settings dataclass, API key initialization |
| `audit.py` | JSONL audit log (`ai_operation_audit.jsonl`) for all AI ops |

## Architecture Notes

- **Guardrails (`guardrails.py`)**: All AI-generated SQL is validated before execution. UPDATE, DELETE, DROP, and other destructive statements are blocked by default. Schema changes require explicit approval.
- **Audit logging (`audit.py`)**: Every AI-assisted operation is appended to `ai_operation_audit.jsonl`.
- **Graceful degradation**: The app starts without API keys and falls back to deterministic SQL patterns for common queries.
- **PandasAI** is optional (not in core dependencies) — import errors are caught and the feature is skipped.

## Code Style

- **Line length**: 100 characters (ruff)
- **Python target**: 3.11+
- **Linting rules**: E, F, W, I (configured in `pyproject.toml`)

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push to `main` and all PRs:
1. **Lint** — `ruff check .`
2. **Security** — `pip-audit`
3. **Test** — `pytest` on Python 3.11 and 3.12

All three stages must pass before merging.

## Database Schema

Single table `PRODUCT` with columns: `ID`, `NAME`, `CATEGORY`, `BRAND`, `PRICE`, `STOCK`, `SIZE`, `COLOR`, `WEIGHT`, `SPECIFICATIONS`.
