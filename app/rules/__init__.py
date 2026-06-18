import json
import os
import time
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


class RulesStorage:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self._rules: Dict[str, Dict] = {}
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
                        json.dump({}, f, ensure_ascii=False, indent=2)

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
                self._rules = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._rules = {}

    def _persist_to_file(self):
        tmp_path = self.storage_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(self._rules, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.storage_path)

    def list_rules(self, page: int = 1, page_size: int = 20) -> Dict:
        with self._thread_lock:
            items = list(self._rules.values())
            total = len(items)
            
            start = (page - 1) * page_size
            end = start + page_size
            paginated = items[start:end]
            
            return {
                'items': paginated,
                'total': total,
                'page': page,
                'page_size': page_size
            }

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        with self._thread_lock:
            return self._rules.get(rule_id)

    def create_rule(self, rule_data: Dict) -> Dict:
        with self._write_lock():
            rule_id = rule_data.get('id') or self._generate_id()
            
            if rule_id in self._rules:
                raise ValueError('rule_already_exists')
            
            now = int(time.time())
            
            rule = {
                'id': rule_id,
                'name': rule_data.get('name', ''),
                'description': rule_data.get('description', ''),
                'version': rule_data.get('version', '1.0.0'),
                'business_id': rule_data.get('business_id', ''),
                'fields': rule_data.get('fields', {}),
                'cross_field': rule_data.get('cross_field', []),
                'nested': rule_data.get('nested', {}),
                'created_at': now,
                'updated_at': now
            }
            
            self._rules[rule_id] = rule
            return rule

    def update_rule(self, rule_id: str, rule_data: Dict) -> Optional[Dict]:
        with self._write_lock():
            if rule_id not in self._rules:
                return None
            
            existing = self._rules[rule_id]
            now = int(time.time())
            
            for key in ['name', 'description', 'version', 'business_id', 'fields', 'cross_field', 'nested']:
                if key in rule_data:
                    existing[key] = rule_data[key]
            
            existing['updated_at'] = now
            return existing

    def delete_rule(self, rule_id: str) -> bool:
        with self._write_lock():
            if rule_id not in self._rules:
                return False
            
            del self._rules[rule_id]
            return True

    def export_rule(self, rule_id: str) -> Optional[Dict]:
        with self._thread_lock:
            rule = self._rules.get(rule_id)
            if not rule:
                return None
            
            return {
                'id': rule['id'],
                'name': rule['name'],
                'description': rule['description'],
                'version': rule['version'],
                'business_id': rule['business_id'],
                'fields': rule['fields'],
                'cross_field': rule['cross_field'],
                'nested': rule['nested'],
                '_export_meta': {
                    'exported_at': int(time.time()),
                    'format_version': '1.0'
                }
            }

    def import_rule(self, import_data: Dict, overwrite: bool = False) -> Dict:
        with self._write_lock():
            rule_id = import_data.get('id') or self._generate_id()
            
            if rule_id in self._rules and not overwrite:
                return {'success': False, 'error': 'rule_already_exists', 'rule_id': rule_id}
            
            now = int(time.time())
            
            rule = {
                'id': rule_id,
                'name': import_data.get('name', ''),
                'description': import_data.get('description', ''),
                'version': import_data.get('version', '1.0.0'),
                'business_id': import_data.get('business_id', ''),
                'fields': import_data.get('fields', {}),
                'cross_field': import_data.get('cross_field', []),
                'nested': import_data.get('nested', {}),
                'created_at': self._rules[rule_id]['created_at'] if rule_id in self._rules else now,
                'updated_at': now
            }
            
            self._rules[rule_id] = rule
            return {'success': True, 'rule_id': rule_id, 'rule': rule}

    def export_all(self) -> Dict:
        with self._thread_lock:
            return {
                'exported_at': int(time.time()),
                'format_version': '1.0',
                'rules': list(self._rules.values())
            }

    def import_all(self, import_data: Dict, overwrite: bool = False) -> Dict:
        with self._write_lock():
            rules = import_data.get('rules', [])
            imported = 0
            skipped = 0
            errors = []

            for rule_data in rules:
                rule_id = rule_data.get('id')
                if rule_id and rule_id in self._rules and not overwrite:
                    skipped += 1
                    errors.append({'id': rule_id, 'reason': 'already_exists'})
                    continue
                
                now = int(time.time())
                rid = rule_id or self._generate_id()
                rule = {
                    'id': rid,
                    'name': rule_data.get('name', ''),
                    'description': rule_data.get('description', ''),
                    'version': rule_data.get('version', '1.0.0'),
                    'business_id': rule_data.get('business_id', ''),
                    'fields': rule_data.get('fields', {}),
                    'cross_field': rule_data.get('cross_field', []),
                    'nested': rule_data.get('nested', {}),
                    'created_at': self._rules[rid]['created_at'] if rid in self._rules else now,
                    'updated_at': now
                }
                self._rules[rid] = rule
                imported += 1

            return {
                'imported': imported,
                'skipped': skipped,
                'errors': errors
            }

    def _generate_id(self) -> str:
        return f"rule_{int(time.time() * 1000)}_{len(self._rules)}_{os.getpid()}"


_rules_storage: Optional[RulesStorage] = None


def init_rules_storage(app):
    global _rules_storage
    storage_path = app.config.get('RULES_STORAGE_PATH', 'data/rules.json')
    _rules_storage = RulesStorage(storage_path)


def get_rules_storage() -> RulesStorage:
    return _rules_storage
