# Repository Guidelines

## Project Structure & Module Organization
The repo splits hybrid-search services in `backend/` and the React console in `frontend/`. `backend/contractApi.py` exposes FastAPI endpoints, with `pdfToElasticSearch.py` for ingest and `elasticSearchSearch.py` for retrieval; staging files sit in `backend/uploaded_contracts/`. Frontend views live in `frontend/src/pages`, shared UI in `frontend/src/components`, and API clients in `frontend/src/services`; builds emit to `frontend/dist` for static serving. Root helpers include `actions.json` (agent command spec), `start.sh` for orchestration, and sample PDFs in `案例合同/`.

## Build, Test, and Development Commands
- `python -m venv contract_env && source contract_env/bin/activate` sets up the expected virtual environment.
- `pip install -r backend/requirements.txt` installs FastAPI, Elasticsearch, and PDF tooling.
- `python backend/elasticSearchSettingVector.py` provisions the `contracts_vector` index before ingestion.
- `python backend/contractApi.py` (or `uvicorn backend.contractApi:app --reload`) serves the API on `http://localhost:8006`.
- `npm install --prefix frontend` restores the React toolchain.
- `npm run dev --prefix frontend` starts the Vite dev server; `npm run build --prefix frontend` emits the production bundle.
- `python test_api_local.py --check` runs the smoke flow; add `-q`/`-U` to exercise search and upload paths.

## Coding Style & Naming Conventions
Python code uses 4-space indentation, snake_case modules, and CamelCase classes; keep responses JSON-structured like existing handlers and co-locate helpers beside their feature. Mirror current logging style. The frontend follows `frontend/eslint.config.js`: TypeScript, PascalCase components (for example `SearchPage.tsx`), camelCase hooks/utilities, and `npm run lint --prefix frontend` before pushing.

## Testing Guidelines
Scripts expect live services. `python test_api_local.py --check` confirms Elasticsearch and FastAPI; add `-q` or `-U` to exercise search/upload. `python backend/test_search.py` and `python test_search_result.py` hit `/document/search` and require populated indices. New tests should sit next to the feature (backend smoke scripts, frontend component tests under `frontend/src/__tests__`) and document sample PDFs or index prerequisites in the PR.

## Commit & Pull Request Guidelines
History is empty, so adopt Conventional Commits (`feat:`, `fix:`, `docs:`) with concise scopes (for example `feat: adjust vector weights`). Keep each commit buildable (`python backend/contractApi.py`, `npm run build --prefix frontend`). PRs should supply a summary, affected endpoints or routes, executed commands, data/index migrations, and screenshots for UI tweaks. Update `actions.json` or `STARTUP_GUIDE.md` when agent-facing workflows change.

## Environment & Configuration Tips
Use `start.sh` to spin up Dockerized Elasticsearch, create indices, and launch both services; `stop.sh` releases ports 8006/9200. Configure secrets such as `HF_ENDPOINT` via environment variables, not Git. Store large contract fixtures under `案例合同/` or `backend/uploaded_contracts/` and scrub private data before committing.

## Agent Collaboration Notes
与 Codex 或自动化代理协作时，默认使用简体中文回复，除非请求明确要求其它语言；保持与文档、API 响应字段一致的术语描述，以便上下游代理正确解析。
