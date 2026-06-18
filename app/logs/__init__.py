import json
import os
import time
import uuid
from typing import Dict, List, Optional

from flask import current_app


class LogsStorage:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self._logs: List[Dict] = []
        self._ensure_storage_file()
        self._load_from_file()

    def _ensure_storage_file(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load_from_file(self):
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self._logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._logs = []

    def _save_to_file(self):
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self._logs, f, ensure_ascii=False, indent=2)

    def add_log(self, log_data: Dict) -> Dict:
        log_id = str(uuid.uuid4())
        now = int(time.time())
        
        log = {
            'id': log_id,
            'business_id': log_data.get('business_id', ''),
            'rule_set_id': log_data.get('rule_set_id', ''),
            'rule_set_version': log_data.get('rule_set_version', ''),
            'success': log_data.get('success', True),
            'duration_ms': log_data.get('duration_ms', 0),
            'error_summary': log_data.get('error_summary', ''),
            'error_count': log_data.get('error_count', 0),
            'request_data': log_data.get('request_data', {}),
            'errors': log_data.get('errors', []),
            'created_at': now
        }
        
        self._logs.append(log)
        self._save_to_file()
        return log

    def query_logs(self, business_id: Optional[str] = None, 
                   start_time: Optional[int] = None,
                   end_time: Optional[int] = None,
                   success: Optional[bool] = None,
                   page: int = 1,
                   page_size: int = 20) -> Dict:
        filtered = self._logs
        
        if business_id:
            filtered = [log for log in filtered if log.get('business_id') == business_id]
        
        if start_time:
            filtered = [log for log in filtered if log.get('created_at', 0) >= start_time]
        
        if end_time:
            filtered = [log for log in filtered if log.get('created_at', 0) <= end_time]
        
        if success is not None:
            filtered = [log for log in filtered if log.get('success') == success]
        
        filtered.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]
        
        return {
            'items': paginated,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    def get_log(self, log_id: str) -> Optional[Dict]:
        for log in self._logs:
            if log.get('id') == log_id:
                return log
        return None

    def get_statistics(self, business_id: Optional[str] = None,
                       start_time: Optional[int] = None,
                       end_time: Optional[int] = None) -> Dict:
        filtered = self._logs
        
        if business_id:
            filtered = [log for log in filtered if log.get('business_id') == business_id]
        
        if start_time:
            filtered = [log for log in filtered if log.get('created_at', 0) >= start_time]
        
        if end_time:
            filtered = [log for log in filtered if log.get('created_at', 0) <= end_time]
        
        total = len(filtered)
        success_count = sum(1 for log in filtered if log.get('success'))
        fail_count = total - success_count
        avg_duration = sum(log.get('duration_ms', 0) for log in filtered) / total if total > 0 else 0
        total_errors = sum(log.get('error_count', 0) for log in filtered)
        
        return {
            'total': total,
            'success': success_count,
            'failed': fail_count,
            'success_rate': success_count / total if total > 0 else 0,
            'avg_duration_ms': round(avg_duration, 2),
            'total_errors': total_errors
        }


_logs_storage: Optional[LogsStorage] = None


def init_logs_storage(app):
    global _logs_storage
    storage_path = app.config.get('LOGS_STORAGE_PATH', 'data/logs.json')
    _logs_storage = LogsStorage(storage_path)


def get_logs_storage() -> LogsStorage:
    return _logs_storage
