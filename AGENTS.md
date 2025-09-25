# Repository Guidelines

## Project Structure & Module Organization
- Backend lives in `backend/`: FastAPI entrypoint `contractApi.py`, Elasticsearch helpers, and ingestion scripts. Staging dirs like `backend/uploaded_contracts/` hold uploaded files.
- Frontend lives in `frontend/`: views in `src/pages/`, shared UI in `src/components/`, API clients in `src/services/`, and domain models in `src/types/`.
- Root contains automation (`actions.json`), local E2E validation (`test_api_local.py`), dev scripts (`start.sh`), and generated artifacts in `logs/` and `output/`.

## Build, Test, and Development Commands
- Create venv + install backend deps: `python -m venv contract_env && source contract_env/bin/activate && pip install -r backend/requirements.txt`.
- Run API only (dev): `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload` (run from `backend/` or ensure PYTHONPATH).
- Start full stack: `./start.sh` (from repo root).
- Frontend setup: `npm install --prefix frontend`. Dev server: `npm run dev --prefix frontend`. Build: `npm run build --prefix frontend`.
- Smoke tests (backend): run from active venv: `python backend/test_api.py` and `python backend/test_search.py`.
- End-to-end ES pipeline check: `python test_api_local.py --check`.

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indent, snake_case functions, PascalCase classes, descriptive modules (e.g., `elasticSearchSearch.py`). Prefer type hints and FastAPI response models when adding endpoints.
- Frontend: Vite/React, 2-space indent, functional components, camelCase helpers. Shared types in `frontend/src/types/`.
- Linting: `npm run lint --prefix frontend`. Format CSS/SCSS consistently.

## Testing Guidelines
- Keep smoke tests under `backend/` (e.g., `backend/test_api.py`, `backend/test_search.py`). Align fixtures with `案例合同/` or `backend/uploaded_contracts/`.
- Manual UI verification is expected until frontend tests are added.
- For new tests, mirror existing patterns; prefer fast, deterministic checks.

## Commit & Pull Request Guidelines
- Commits: concise subjects (<72 chars) with conventional prefixes (`feat:`, `fix:`, `docs:`). Describe behavior changes and affected endpoints/views; note any index/schema updates.
- PRs: link issues, summarize impacted APIs or routes, include screenshots or curl snippets for UX/API changes, and note testing evidence.

## Security & Configuration Tips
- Do not commit secrets or private documents; use environment variables. Large sample files should be documented.
- Generated outputs in `logs/` and `output/` are not source; treat them as ephemeral.

## Agent-Specific Notes
- Apply minimal, focused changes consistent with this codebase’s style. Obey directory conventions and keep patches surgical. Do not introduce unrelated fixes or new tooling without discussion.
