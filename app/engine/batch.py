import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from flask import current_app

from .core import ValidationEngine
from ..validators import ValidationResult, ValidationError
from ..i18n import get_message


class BatchValidator:
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers

    def _get_executor(self) -> ThreadPoolExecutor:
        workers = self.max_workers
        if workers is None:
            workers = current_app.config.get('THREAD_POOL_MAX_WORKERS', 10)
        return ThreadPoolExecutor(max_workers=workers)

    def validate_single(self, rule_set: Dict, data: Dict) -> ValidationResult:
        engine = ValidationEngine(rule_set)
        return engine.validate(data)

    def validate_batch_fields(self, rule_set: Dict, data: Dict) -> ValidationResult:
        engine = ValidationEngine(rule_set)
        
        if engine.has_cross_field_rules():
            return self._validate_serial(engine, data)
        else:
            return self._validate_parallel(rule_set, data)

    def _validate_serial(self, engine: ValidationEngine, data: Dict) -> ValidationResult:
        return engine.validate(data)

    def _validate_parallel(self, rule_set: Dict, data: Dict) -> ValidationResult:
        result = ValidationResult()
        field_rules = rule_set.get('fields', {})
        
        if not field_rules:
            return result

        def validate_field(field_name: str, field_config: Dict) -> List[ValidationError]:
            errors = []
            value = data.get(field_name)
            validators_config = field_config.get('validators', [])
            
            for validator_config in validators_config:
                validator_name = validator_config.get('type', '')
                validator_params = validator_config.get('params', {})
                
                from ..validators import ValidatorRegistry
                validator = ValidatorRegistry.create_validator(validator_name, **validator_params)
                if validator:
                    field_result = validator.validate(value, field_name, data)
                    if not field_result.valid:
                        errors.extend(field_result.errors)
            
            return errors

        with self._get_executor() as executor:
            futures = {}
            for field_name, field_config in field_rules.items():
                future = executor.submit(validate_field, field_name, field_config)
                futures[future] = field_name

            for future in as_completed(futures):
                try:
                    errors = future.result()
                    for err in errors:
                        result.add_error(err)
                except Exception:
                    pass

        nested_rules = rule_set.get('nested', {})
        if nested_rules:
            from .core import ValidationEngine
            engine = ValidationEngine(rule_set)
            nested_result = engine._validate_nested(data, '')
            result.merge(nested_result)

        return result

    def validate_multiple_datasets(self, rule_sets: List[Dict], data_list: List[Dict]) -> List[Dict]:
        results = []

        def validate_one(rule_set: Dict, data: Dict, index: int) -> Dict:
            start_time = time.time()
            try:
                result = self.validate_single(rule_set, data)
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    'index': index,
                    'valid': result.valid,
                    'errors': [self._serialize_error(e) for e in result.errors],
                    'duration_ms': duration_ms
                }
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    'index': index,
                    'valid': False,
                    'errors': [{'field': '__system__', 'message': str(e)}],
                    'duration_ms': duration_ms
                }

        with self._get_executor() as executor:
            futures = []
            for i, (rule_set, data) in enumerate(zip(rule_sets, data_list)):
                future = executor.submit(validate_one, rule_set, data, i)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception:
                    pass

        results.sort(key=lambda x: x['index'])
        return results

    def _serialize_error(self, error: ValidationError) -> Dict:
        return {
            'field': error.field,
            'message_key': error.message_key,
            'message': get_message(error.message_key, **error.message_params),
            'params': error.message_params,
            'actual_value': error.actual_value
        }
