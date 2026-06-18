import json
import os
import time
import uuid
import threading
import errno
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from flask import current_app


class FileLock:
    def __init__(self, file_path: str, timeout: float = 10.0):
        self.lock_path = file_path + '.lock'
        self.timeout = timeout
        self._lock_fd: Optional[int] = None

    def acquire(self):
        start_time = time.time()
        while True:
            try:
                self._lock_fd = os.open(
                    self.lock_path,
                    os.O_CREAT | os.O_RDWR | os.O_EXCL,
                    0o644
                )
                return
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if (time.time() - start_time) >= self.timeout:
                    raise TimeoutError(f"Could not acquire lock on {self.lock_path}")
                time.sleep(0.05)

    def release(self):
        if self._lock_fd is not None:
            try:
                os.close(self._lock_fd)
            except OSError:
                pass
            try:
                os.unlink(self.lock_path)
            except OSError:
                pass
            self._lock_fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class LogsStorage:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self._logs: List[Dict] = []
        self._thread_lock = threading.RLock()
        self._file_lock = FileLock(storage_path, timeout=15.0)
        self._ensure_storage_file()
        self._load_from_file()

    def _ensure_storage_file(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with self._thread_lock:
                if not os.path.exists(self.storage_path):
                    with open(self.storage_path, 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=2)

    @contextmanager
    def _write_lock(self):
        with self._thread_lock:
            with self._file_lock:
                self._load_from_file()
                yield
                self._persist_to_file()

    def _load_from_file(self):
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self._logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._logs = []

    def _persist_to_file(self):
        tmp_path = self.storage_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(self._logs, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.storage_path)

    def add_log(self, log_data: Dict) -> Dict:
        with self._write_lock():
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
            return log

    def query_logs(self, business_id: Optional[str] = None, 
                   start_time: Optional[int] = None,
                   end_time: Optional[int] = None,
                   success: Optional[bool] = None,
                   page: int = 1,
                   page_size: int = 20) -> Dict:
        with self._thread_lock:
            filtered = list(self._logs)
            
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
        with self._thread_lock:
            for log in self._logs:
                if log.get('id') == log_id:
                    return log
            return None

    def get_statistics(self, business_id: Optional[str] = None,
                       start_time: Optional[int] = None,
                       end_time: Optional[int] = None) -> Dict:
        with self._thread_lock:
            filtered = list(self._logs)
            
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
