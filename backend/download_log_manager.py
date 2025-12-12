"""
下载日志管理器

记录和查询用户的合同下载行为。
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class DownloadLogManager:
    """管理用户下载日志的存储和查询"""

    def __init__(self, log_file: Optional[str] = None):
        """
        初始化下载日志管理器
        
        Args:
            log_file: 日志文件路径，默认为 backend/download_logs.json
        """
        if log_file:
            self.log_file = Path(log_file)
        else:
            self.log_file = Path(__file__).resolve().parent / "download_logs.json"
        
        self._lock = threading.RLock()
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """确保日志文件存在"""
        if not self.log_file.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_logs([])

    def _read_logs(self) -> List[Dict[str, Any]]:
        """读取所有日志"""
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_logs(self, logs: List[Dict[str, Any]]) -> None:
        """写入日志到文件"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def record_download(self, user_id: str, document_name: str) -> Dict[str, Any]:
        """
        记录一次下载行为
        
        Args:
            user_id: 下载用户的ID
            document_name: 下载的合同文件名
            
        Returns:
            创建的日志记录
        """
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "user_id": user_id,
            "document_name": document_name,
            "download_time": datetime.now(timezone.utc).isoformat(),
        }
        
        with self._lock:
            logs = self._read_logs()
            logs.append(log_entry)
            self._write_logs(logs)
        
        return log_entry

    def get_user_logs(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        获取指定用户的下载日志
        
        Args:
            user_id: 用户ID
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            包含日志列表和分页信息的字典
        """
        with self._lock:
            all_logs = self._read_logs()
        
        # 过滤出该用户的日志
        user_logs = [log for log in all_logs if log.get("user_id") == user_id]
        
        # 按下载时间倒序排列
        user_logs.sort(key=lambda x: x.get("download_time", ""), reverse=True)
        
        total = len(user_logs)
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = user_logs[start_idx:end_idx]
        
        return {
            "logs": paginated_logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    def get_all_logs(
        self,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        获取所有下载日志（管理用途）
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            包含日志列表和分页信息的字典
        """
        with self._lock:
            all_logs = self._read_logs()
        
        # 按下载时间倒序排列
        all_logs.sort(key=lambda x: x.get("download_time", ""), reverse=True)
        
        total = len(all_logs)
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = all_logs[start_idx:end_idx]
        
        return {
            "logs": paginated_logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }
