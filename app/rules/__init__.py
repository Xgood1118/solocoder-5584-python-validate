import json
import os
import time
from typing import Dict, List, Optional

from flask import current_app, g


class RulesStorage:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self._rules: Dict[str, Dict] = {}
        self._ensure_storage_file()
        self._load_from_file()

    def _ensure_storage_file(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def _load_from_file(self):
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self._rules = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._rules = {}

    def _save_to_file(self):
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self._rules, f, ensure_ascii=False, indent=2)

    def list_rules(self, page: int = 1, page_size: int = 20) -> Dict:
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
        return self._rules.get(rule_id)

    def create_rule(self, rule_data: Dict) -> Dict:
        rule_id = rule_data.get('id') or self._generate_id()
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
        self._save_to_file()
        return rule

    def update_rule(self, rule_id: str, rule_data: Dict) -> Optional[Dict]:
        if rule_id not in self._rules:
            return None
        
        existing = self._rules[rule_id]
        now = int(time.time())
        
        for key in ['name', 'description', 'version', 'business_id', 'fields', 'cross_field', 'nested']:
            if key in rule_data:
                existing[key] = rule_data[key]
        
        existing['updated_at'] = now
        self._save_to_file()
        return existing

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id not in self._rules:
            return False
        
        del self._rules[rule_id]
        self._save_to_file()
        return True

    def export_rule(self, rule_id: str) -> Optional[Dict]:
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
        self._save_to_file()
        return {'success': True, 'rule_id': rule_id, 'rule': rule}

    def export_all(self) -> Dict:
        return {
            'exported_at': int(time.time()),
            'format_version': '1.0',
            'rules': list(self._rules.values())
        }

    def import_all(self, import_data: Dict, overwrite: bool = False) -> Dict:
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
            
            result = self.import_rule(rule_data, overwrite=overwrite)
            if result.get('success'):
                imported += 1
            else:
                skipped += 1
                errors.append(result)

        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }

    def _generate_id(self) -> str:
        return f"rule_{int(time.time() * 1000)}_{len(self._rules)}"


_rules_storage: Optional[RulesStorage] = None


def init_rules_storage(app):
    global _rules_storage
    storage_path = app.config.get('RULES_STORAGE_PATH', 'data/rules.json')
    _rules_storage = RulesStorage(storage_path)


def get_rules_storage() -> RulesStorage:
    return _rules_storage
