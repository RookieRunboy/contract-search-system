# Repository Guidelines

## Project Structure & Module Organization
Backend services reside under `backend/`: FastAPI entrypoints (`contractApi.py`), Elasticsearch helpers, and ingestion scripts share this folder with staging directories such as `backend/uploaded_contracts/`. Frontend code lives in `frontend/`, where `src/pages/`, `src/components/`, `src/services/`, and `src/types/` separate views, shared UI, API clients, and domain models. Automation artifacts (`actions.json`, `test_api_local.py`) sit at the repo root alongside dev scripts (`start.sh`) and generated outputs in `logs/` and `output/`.

## Build, Test, and Development Commands
Create the shared virtualenv once with `python -m venv contract_env && source contract_env/bin/activate`, then restore backend deps via `pip install -r backend/requirements.txt`. Start the full stack locally using `./start.sh`, or run the API alone with `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload`. For the frontend, bootstrap with `npm install --prefix frontend` and develop interactively using `npm run dev --prefix frontend`; build production assets through `npm run build --prefix frontend`.

## Coding Style & Naming Conventions
Python modules follow PEP 8: four-space indentation, snake_case functions, PascalCase classes, and descriptive filenames (e.g., `elasticSearchSearch.py`). Prefer type hints and FastAPI response models when extending endpoints. The Vite/React codebase uses 2-space indentation, functional components, and camelCase helpers. Shared types belong in `frontend/src/types/`. Run `npm run lint --prefix frontend` before opening a PR; format CSS and SCSS assets as needed.

## Testing Guidelines
Smoke tests live in `backend/test_api.py` and `backend/test_search.py`; execute them from an active virtualenv. `python test_api_local.py --check` performs an end-to-end Elasticsearch pipeline validation (health check, upload, search, cleanup). Frontend changes should at minimum pass `npm run lint --prefix frontend`; manual UI verification is expected until automated tests are added. Align fixtures with `案例合同/` or `backend/uploaded_contracts/`, and document large sample files.

## Commit & Pull Request Guidelines
Use concise subjects (<72 chars) with conventional prefixes (`feat:`, `fix:`, `docs:`) or brief imperatives. Describe behavioral changes, affected endpoints or views, and test evidence in the body; highlight any index schema updates so reviewers can rerun setup scripts. Pull requests should link relevant issues, enumerate impacted APIs or UI routes, and include screenshots or curl snippets when UX changes are introduced.
