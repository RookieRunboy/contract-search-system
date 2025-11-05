# Repository Guidelines

## Project Structure & Module Organization
Backend services live in `backend/` with the FastAPI entrypoint `contractApi.py`, plus ingestion helpers, Elasticsearch utilities, and uploaded documents under `backend/uploaded_contracts/`. The React/Vite frontend resides in `frontend/` (pages in `frontend/src/pages/`, shared UI in `frontend/src/components/`, API clients in `frontend/src/services/`, and domain types in `frontend/src/types/`). Root-level automation and verification scripts include `actions.json`, `start.sh`, and `test_api_local.py`; generated artifacts land in `logs/` and `output/`.

## Build, Test, and Development Commands
Create a backend venv with `python -m venv contract_env && source contract_env/bin/activate && pip install -r backend/requirements.txt`. Run the API using `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload`. Start the entire stack via `./start.sh`. Frontend setup uses `npm install --prefix frontend`; start the UI with `npm run dev --prefix frontend` and produce production assets via `npm run build --prefix frontend`. Backend smoke tests: `python backend/test_api.py`, `python backend/test_search.py`, and end-to-end validation through `python test_api_local.py --check`.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indents, snake_case functions, PascalCase classes, and explicit type hints for FastAPI models. Frontend code uses 2-space indents, functional components, camelCase helpers, and TypeScript types from `frontend/src/types`. Run `npm run lint --prefix frontend` before submitting UI changes; format Python code with `black` and `ruff` if already configured locally.

## Testing Guidelines
Keep backend tests under `backend/`, referencing fixtures from `案例合同/` or `backend/uploaded_contracts/`. Name tests descriptively (e.g., `test_search_returns_ranked_hits`). Ensure the smoke tests and `test_api_local.py --check` pass before opening a PR, and attach curl snippets or screenshots for new endpoints or UX flows.

## Commit & Pull Request Guidelines
Use concise conventional commits like `feat: add search filter` under 72 characters. PRs should link related issues, summarize affected endpoints or views, detail schema or index changes, and include screenshots or curl traces for UI/API updates. Document the commands run for verification (tests, lint, builds) in the PR description.

## Security & Configuration Tips
Never commit secrets or private contracts; prefer environment variables and document how to obtain sensitive files. Treat `logs/` and `output/` as ephemeral artifacts, and avoid introducing new tooling without discussing it with the team. Keep patches minimal and focused on the documented directories above.
