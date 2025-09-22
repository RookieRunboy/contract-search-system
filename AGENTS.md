# Repository Guidelines

## Project Structure & Module Organization
Backend code sits in `backend/`: `contractApi.py` exposes FastAPI while ingestion and search helpers (`pdfToElasticSearch.py`, `elasticSearchSearch.py`, `document_processor.py`) share the folder with ES setup scripts and staged files in `backend/uploaded_contracts/`. The React stack lives in `frontend/`; `src/pages/`, `src/components/`, `src/services/`, and `src/types/` mirror page, UI, API, and model layers. Agent-friendly automation resides at the root (`actions.json`, `test_api_local.py`), with generated artefacts collected under `logs/` and `output/`.

## Build, Test, and Development Commands
- `python -m venv contract_env && source contract_env/bin/activate`: prepare the shared virtualenv once per workstation.
- `pip install -r backend/requirements.txt`: restore backend dependencies before running API or indexing scripts.
- `npm install --prefix frontend`: install the Vite toolchain; pair with `npm run dev --prefix frontend` for the live UI or `npm run build` before packaging.
- `./start.sh`: boot Elasticsearch (Docker), install dependencies if missing, and launch backend/front services; watch `logs/backend.log` for issues.
- `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload`: run the API standalone when iterating quickly.

## Coding Style & Naming Conventions
Backend modules follow PEP 8: 4-space indentation, snake_case for functions, PascalCase for classes, and informative filenames (`elasticSearchInputVector.py`). Prefer type hints and FastAPI response models when extending endpoints. Frontend TypeScript uses 2-space indentation, functional components, and camelCase utilities; keep shared types in `src/types/`. Run `npm run lint --prefix frontend` and format CSS assets before opening a PR.

## Testing Guidelines
Smoke checks live in `backend/test_api.py` and `backend/test_search.py`; execute them with the active virtualenv after changing extraction or search logic. `python test_api_local.py --check` performs an end-to-end ES pipeline validation (health checks, upload, search, cleanup). Store reproducible fixtures in `案例合同/` or `backend/uploaded_contracts/`, noting large files in documentation. Frontend changes should ship with a lint pass and manual validation until automated UI tests land.

## Commit & Pull Request Guidelines
Match the repo's concise subject style: conventional prefixes (`feat:`, `fix:`, `docs:`) or brief imperatives (`Add ...`) under 72 characters, optionally bilingual when stakeholder-facing. Detail behavioural changes, test evidence, and Elasticsearch index expectations in the message body. Pull requests should link issues, list affected endpoints or views, and include screenshots for UI work. Flag any ES schema or sample-data updates so reviewers can re-run setup scripts.
