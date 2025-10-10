# Repository Guidelines

## Project Structure & Module Organization
Backend code resides in `backend/` with the FastAPI entrypoint `contractApi.py`, Elasticsearch helpers, and ingestion scripts; uploaded artifacts land in `backend/uploaded_contracts/`. The Vite/React frontend is under `frontend/` with pages in `frontend/src/pages/`, shared UI in `frontend/src/components/`, API clients in `frontend/src/services/`, and domain types in `frontend/src/types/`. Root-level utilities include automation in `actions.json`, local verification via `test_api_local.py`, dev bootstrap `start.sh`, and generated outputs in `logs/` and `output/`.

## Build, Test, and Development Commands
Create the backend venv and install deps with `python -m venv contract_env && source contract_env/bin/activate && pip install -r backend/requirements.txt`. Run the API locally via `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload`. Launch the full stack using `./start.sh`. Frontend setup uses `npm install --prefix frontend`, while `npm run dev --prefix frontend` starts the dev server and `npm run build --prefix frontend` produces production assets. Backend smoke tests are `python backend/test_api.py` and `python backend/test_search.py`, and the end-to-end pipeline check is `python test_api_local.py --check`.

## Coding Style & Naming Conventions
Follow PEP 8 for Python with 4-space indents, snake_case functions, and PascalCase classes; prefer type hints and FastAPI response models. Frontend code uses 2-space indents, functional React components, and camelCase helpers. Run `npm run lint --prefix frontend` before submitting UI changes.

## Testing Guidelines
Keep backend tests within `backend/` using fast, deterministic fixtures aligned with `案例合同/` or `backend/uploaded_contracts/`. Name tests descriptively and ensure smoke tests pass after backend changes. Manual UI verification remains the norm until automated frontend coverage is added.

## Commit & Pull Request Guidelines
Compose concise conventional commits (e.g., `feat: add search filter`) under 72 characters. PRs should link issues, describe affected endpoints or views, include screenshots or curl snippets for UX/API updates, and explain any index or schema adjustments. Document testing evidence for each change.

## Security & Configuration Tips
Never commit secrets or private documents; rely on environment variables and document large samples instead of checking them in. Treat `logs/` and `output/` as ephemeral artifacts. Apply focused, minimal patches that respect existing directory conventions and avoid introducing unrelated tooling without prior discussion.
