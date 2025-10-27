from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch, exceptions as es_exceptions


class UploadStatusManager:
    """Manage upload status documents stored in Elasticsearch."""

    STATUS_LABELS = {
        "pending": "待解析",
        "parsing": "正在转化为文本",
        "vectorizing": "正在向量化",
        "metadata_extracting": "正在提取元数据",
        "completed": "解析成功",
        "failed": "解析失败",
    }

    def __init__(
        self,
        es_host: str = "http://localhost:9200",
        index_name: str = "contract_upload_status",
    ) -> None:
        self.es = Elasticsearch(es_host)
        self.index_name = index_name
        self._ensure_index()

    def _ensure_index(self) -> None:
        if self.es.indices.exists(index=self.index_name):
            return

        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {
                    "upload_id": {"type": "keyword"},
                    "file_name": {"type": "keyword"},
                    "contract_name": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "status_display": {"type": "keyword"},
                    "message": {"type": "text"},
                    "error": {"type": "text"},
                    "metadata_status": {"type": "keyword"},
                    "has_metadata": {"type": "boolean"},
                    "total_pages": {"type": "integer"},
                    "page_count": {"type": "integer"},
                    "processed_pages": {"type": "integer"},
                    "file_size_bytes": {"type": "long"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            },
        }

        try:
            self.es.indices.create(index=self.index_name, body=mapping)
        except es_exceptions.RequestError as exc:  # pragma: no cover - defensive
            # 索引可能在并发情况下已被创建，忽略 resource_already_exists 异常
            if exc.error != "resource_already_exists_exception":
                raise

    def create_upload_record(
        self,
        file_name: str,
        contract_name: str,
        file_size_bytes: Optional[int] = None,
    ) -> str:
        upload_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        doc = {
            "upload_id": upload_id,
            "file_name": file_name,
            "contract_name": contract_name,
            "status": "pending",
            "status_display": self.STATUS_LABELS.get("pending"),
            "metadata_status": "pending",
            "has_metadata": False,
            "total_pages": None,
            "page_count": None,
            "processed_pages": 0,
            "file_size_bytes": file_size_bytes,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        self.es.index(index=self.index_name, id=upload_id, body=doc, refresh="wait_for")
        return upload_id

    def update_upload_record(
        self,
        upload_id: str,
        *,
        status: Optional[str] = None,
        status_display: Optional[str] = None,
        metadata_status: Optional[str] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
        total_pages: Optional[int] = None,
        processed_pages: Optional[int] = None,
        page_count: Optional[int] = None,
        has_metadata: Optional[bool] = None,
        file_size_bytes: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        update_fields: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if status is not None:
            update_fields["status"] = status
            update_fields["status_display"] = status_display or self.STATUS_LABELS.get(status, status)
        elif status_display is not None:
            update_fields["status_display"] = status_display

        if metadata_status is not None:
            update_fields["metadata_status"] = metadata_status
        if message is not None:
            update_fields["message"] = message
        if error is not None:
            update_fields["error"] = error
        if total_pages is not None:
            update_fields["total_pages"] = total_pages
        if processed_pages is not None:
            update_fields["processed_pages"] = processed_pages
        if page_count is not None:
            update_fields["page_count"] = page_count
        if has_metadata is not None:
            update_fields["has_metadata"] = has_metadata
        if file_size_bytes is not None:
            update_fields["file_size_bytes"] = file_size_bytes
        if extra:
            update_fields.update(extra)

        self.es.update(
            index=self.index_name,
            id=upload_id,
            body={"doc": update_fields},
            doc_as_upsert=True,
            refresh="wait_for",
        )

    def get_upload_record(self, upload_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc = self.es.get(index=self.index_name, id=upload_id)
        except es_exceptions.NotFoundError:
            return None
        source = doc.get("_source", {})
        source["upload_id"] = upload_id
        return source

    def list_uploads(self, size: int = 1000) -> List[Dict[str, Any]]:
        body = {
            "size": size,
            "sort": [
                {"created_at": {"order": "desc"}},
                {"updated_at": {"order": "desc"}},
            ],
        }

        response = self.es.search(index=self.index_name, body=body)
        hits = response.get("hits", {}).get("hits", [])
        results: List[Dict[str, Any]] = []
        for hit in hits:
            source = hit.get("_source", {}) or {}
            source["upload_id"] = hit.get("_id")
            results.append(source)
        return results

