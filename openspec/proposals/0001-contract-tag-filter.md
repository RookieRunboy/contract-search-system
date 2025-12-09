# Proposal: Contract Tag Filters

- Status: Draft
- Created: 2025-11-06
- Author: Codex (AI assistant)
- Owners: Search Platform Team
- Related Docs: openspec/project.md

## Problem Statement
Reviewers need a fast way to slice contract search results by business attributes (e.g., 客户类型, 区域, 合同阶段). Today every query returns the full semantic result set, forcing analysts to skim dozens of irrelevant agreements. We lack structured tags that can be attached during upload or post-processing, so downstream workflows (compliance review, renewal tracking) stay manual and error-prone.

## Goals
- Allow users to add zero-or-more textual tags to each uploaded contract.
- Persist tags in Elasticsearch so they are filterable alongside semantic search scores.
- Extend the search API/UI so users can filter results by one or many tags.
- Provide a lightweight tag-editing surface without re-uploading the PDF.

## Non-Goals
- Automatic tag generation via ML (manual entry only for this iteration).
- Hierarchical or nested tagging schemes.
- Per-user permissions or tag visibility controls.

## Solution Overview
Introduce a `tags: List[str]` attribute at ingestion time and expose CRUD support through API + UI. Search requests can include `tags` as an optional filter; when provided we intersect the semantic hits with documents that contain all requested tags.

### Backend Changes
1. **Data Model**
   - Update `backend/contractApi.py` document schema (Pydantic models + Elasticsearch payload) to include `tags` (default empty list).
   - Migrate existing Elasticsearch index: add `tags` as `keyword` array; reindex existing documents with `tags=[]`.
2. **Endpoints**
   - `POST /document/add`: accept `tags` array in multipart payload (JSON field or comma-delimited string) and store it.
   - `POST /document/search`: accept optional `tags` array; when present, apply a `terms_set` or `bool must match` clause.
   - `PATCH /document/{id}/tags`: new endpoint to replace tags on an existing contract without re-upload.
3. **Validation**
   - Enforce max 10 tags per document, 24 chars per tag, alphanumeric + dashes/underscores.
   - Normalize tags to lowercase to ensure deterministic filters.

### Frontend Changes
1. **Upload Flow** (`frontend/src/pages/UploadPage.tsx` or equivalent)
   - Add multi-select input (Ant Design `Select` with `mode="tags"`) bound to the `tags` field.
   - Send tags via existing upload service.
2. **Search Page** (`frontend/src/pages/SearchPage.tsx`)
   - Add tag filter UI (multi-select). Persist latest selection in URL query params.
   - Display applied tags as chips near the search bar for quick removal.
3. **Contract Detail Drawer** (`frontend/src/components/DocumentDrawer.tsx`)
   - Show current tags and expose an inline editor that calls the new PATCH endpoint.

### API & Contract Changes
```json
// POST /document/search body (new fields only)
{
  "query": "renewal terms",
  "tags": ["vip", "2024-renewal"]
}
```
- Response will echo `tags` per document so the UI can render them.

### Rollout & Migration
1. Add index template update + reindex script under `backend/scripts/reindex_with_tags.py`.
2. Backfill tags for existing docs via CSV import or manual editing UI.
3. Deploy backend first (new fields are optional). Release frontend once backend patch is live.

### Risks & Mitigations
- **Index size growth**: Tags stored as keywords add marginal storage (<1 KB/doc). Monitor index stats weekly.
- **Search latency**: Additional filter clause could increase query time by ~5-10%. Use `terms_set` with `minimum_should_match_script` to keep filters efficient.
- **User education**: Provide helper copy/tooltips on allowed characters and recommended tag taxonomy.

### Testing Strategy
- Backend unit tests for schema validation and ES query builder.
- Integration test covering `tags` filter combination with semantic query.
- Frontend cypress/RTL test to ensure selected tags propagate to API payloads.
- Manual QA: upload tagged docs, update tags, verify filtered search results.

### Open Questions
1. Should we seed common tag suggestions from config or previously used tags?
2. Is there a need for audit logging on tag changes?
3. Do we need translation/localization for the default helper text?
