from typing import Any, Dict, List, Optional
from datetime import datetime
import re

from ..validators import ValidationResult, ValidationError, ValidatorRegistry
from ..i18n import get_message
from .safe_eval import SafeExpressionEvaluator


def get_nested_value(data: Dict, path: str) -> Any:
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and key.isdigit():
            idx = int(key)
            if 0 <= idx < len(value):
                value = value[idx]
            else:
                return None
        else:
            return None
    return value


def set_nested_path(error: ValidationError, prefix: str):
    if prefix:
        error.field = f"{prefix}.{error.field}"


class CrossFieldValidator:
    def __init__(self, config: Dict):
        self.fields = config.get('fields', [])
        self.rule_type = config.get('rule_type', 'expression')
        self.expression = config.get('expression', '')
        self.message = config.get('message', '')
        self.message_key = config.get('message_key', 'cross_field_generic')
        self.params = config.get('params', {})

    def validate(self, data: Dict, prefix: str = '') -> ValidationResult:
        result = ValidationResult()

        if self.rule_type == 'start_before_end':
            return self._validate_start_before_end(data, prefix)
        elif self.rule_type == 'fields_equal':
            return self._validate_fields_equal(data, prefix)
        elif self.rule_type == 'fields_not_equal':
            return self._validate_fields_not_equal(data, prefix)
        elif self.rule_type == 'expression':
            return self._validate_expression(data, prefix)
        else:
            return result

    def _get_full_field(self, field: str, prefix: str) -> str:
        return f"{prefix}.{field}" if prefix else field

    def _validate_start_before_end(self, data: Dict, prefix: str) -> ValidationResult:
        result = ValidationResult()
        
        start_field = self.params.get('start_field', self.fields[0] if len(self.fields) > 0 else 'start')
        end_field = self.params.get('end_field', self.fields[1] if len(self.fields) > 1 else 'end')
        date_format = self.params.get('format', '%Y-%m-%d')

        start_val = get_nested_value(data, start_field)
        end_val = get_nested_value(data, end_field)

        if start_val is None or end_val is None:
            return result

        try:
            start_date = datetime.strptime(start_val, date_format)
            end_date = datetime.strptime(end_val, date_format)
        except (ValueError, TypeError):
            return result

        if start_date >= end_date:
            full_start = self._get_full_field(start_field, prefix)
            full_end = self._get_full_field(end_field, prefix)
            result.add_error(ValidationError(
                field=full_start,
                message_key='cross_field_start_before_end',
                message_params={
                    'start_field': full_start,
                    'end_field': full_end
                },
                actual_value=f"{start_val} >= {end_val}"
            ))

        return result

    def _validate_fields_equal(self, data: Dict, prefix: str) -> ValidationResult:
        result = ValidationResult()
        
        field1 = self.params.get('field1', self.fields[0] if len(self.fields) > 0 else 'field1')
        field2 = self.params.get('field2', self.fields[1] if len(self.fields) > 1 else 'field2')

        val1 = get_nested_value(data, field1)
        val2 = get_nested_value(data, field2)

        if val1 is None and val2 is None:
            return result

        if val1 != val2:
            full_field1 = self._get_full_field(field1, prefix)
            full_field2 = self._get_full_field(field2, prefix)
            result.add_error(ValidationError(
                field=full_field1,
                message_key='cross_field_fields_equal',
                message_params={
                    'field1': full_field1,
                    'field2': full_field2
                },
                actual_value=val1
            ))

        return result

    def _validate_fields_not_equal(self, data: Dict, prefix: str) -> ValidationResult:
        result = ValidationResult()
        
        field1 = self.params.get('field1', self.fields[0] if len(self.fields) > 0 else 'field1')
        field2 = self.params.get('field2', self.fields[1] if len(self.fields) > 1 else 'field2')

        val1 = get_nested_value(data, field1)
        val2 = get_nested_value(data, field2)

        if val1 is None or val2 is None:
            return result

        if val1 == val2:
            full_field1 = self._get_full_field(field1, prefix)
            full_field2 = self._get_full_field(field2, prefix)
            result.add_error(ValidationError(
                field=full_field1,
                message_key='cross_field_fields_not_equal',
                message_params={
                    'field1': full_field1,
                    'field2': full_field2
                },
                actual_value=val1
            ))

        return result

    def _validate_expression(self, data: Dict, prefix: str) -> ValidationResult:
        result = ValidationResult()
        
        if not self.expression:
            return result

        main_field = self._get_full_field(self.fields[0], prefix) if self.fields else prefix

        try:
            variables: Dict[str, Any] = {}
            for field in self.fields:
                var_name = field.replace('.', '_')
                variables[var_name] = get_nested_value(data, field)
                variables[field] = get_nested_value(data, field)

            is_valid = SafeExpressionEvaluator.evaluate(self.expression, variables)
            
            if not is_valid:
                result.add_error(ValidationError(
                    field=main_field,
                    message_key=self.message_key,
                    message_params={
                        'message': self.message,
                        **self.params
                    },
                    actual_value=self.expression
                ))

        except (SyntaxError, ValueError) as e:
            result.add_error(ValidationError(
                field=main_field,
                message_key='expression_syntax_error',
                message_params={
                    'field': main_field,
                    'detail': str(e)
                },
                actual_value=self.expression
            ))

        except NameError as e:
            result.add_error(ValidationError(
                field=main_field,
                message_key='expression_eval_error',
                message_params={
                    'field': main_field,
                    'detail': f'未定义的变量: {e}'
                },
                actual_value=self.expression
            ))

        except (TypeError, IndexError, KeyError, AttributeError) as e:
            pass

        except Exception as e:
            result.add_error(ValidationError(
                field=main_field,
                message_key='expression_eval_error',
                message_params={
                    'field': main_field,
                    'detail': str(e)
                },
                actual_value=self.expression
            ))

        return result


class ValidationEngine:
    def __init__(self, rule_set: Dict):
        self.rule_set = rule_set
        self.field_rules = rule_set.get('fields', {})
        self.cross_field_rules = rule_set.get('cross_field', [])
        self.nested_rules = rule_set.get('nested', {})

    def validate(self, data: Dict, prefix: str = '') -> ValidationResult:
        result = ValidationResult()

        result.merge(self._validate_fields(data, prefix))
        result.merge(self._validate_nested(data, prefix))
        result.merge(self._validate_cross_field(data, prefix))

        return result

    _FLAT_CONSTRAINTS = {
        'required': {'type': 'required', 'param_map': {}},
        'min_length': {'type': 'min_length', 'param_map': {'min_length': 'min'}},
        'max_length': {'type': 'max_length', 'param_map': {'max_length': 'max'}},
        'length': {'type': 'length', 'param_map': {'min_length': 'min', 'max_length': 'max'}},
        'min': {'type': 'min', 'param_map': {'min': 'min'}},
        'max': {'type': 'max', 'param_map': {'max': 'max'}},
        'range': {'type': 'range', 'param_map': {'min': 'min', 'max': 'max'}},
        'pattern': {'type': 'regex', 'param_map': {'pattern': 'pattern'}},
        'regex': {'type': 'regex', 'param_map': {'regex': 'pattern'}},
        'enum': {'type': 'enum_whitelist', 'param_map': {'enum': 'allowed'}},
        'allowed': {'type': 'enum_whitelist', 'param_map': {'allowed': 'allowed'}},
        'forbidden': {'type': 'enum_blacklist', 'param_map': {'forbidden': 'forbidden'}},
        'format': {'type': 'date_format', 'param_map': {'format': 'format'}},
        'date_format': {'type': 'date_format', 'param_map': {'date_format': 'format'}},
    }

    @classmethod
    def build_field_validators(cls, field_config: Dict) -> List[tuple]:
        validators_to_run: List[tuple] = []

        validators_config = field_config.get('validators', [])
        for validator_config in validators_config:
            validator_name = validator_config.get('type', '')
            validator_params = validator_config.get('params', {})
            validators_to_run.append((validator_name, validator_params))

        for constraint_key, mapping in cls._FLAT_CONSTRAINTS.items():
            if constraint_key in field_config and constraint_key != 'validators':
                constraint_value = field_config[constraint_key]
                params: Dict[str, Any] = {}
                for src_key, dst_key in mapping['param_map'].items():
                    if src_key in field_config:
                        params[dst_key] = field_config[src_key]
                if mapping['type'] == 'required':
                    if constraint_value:
                        validators_to_run.append((mapping['type'], params))
                elif mapping['type'] in ('enum_whitelist', 'enum_blacklist'):
                    params[mapping['param_map'].get(constraint_key, constraint_key)] = constraint_value
                    validators_to_run.append((mapping['type'], params))
                elif mapping['type'] == 'length':
                    if 'min' not in params and isinstance(constraint_value, (list, tuple)) and len(constraint_value) == 2:
                        params['min'] = constraint_value[0]
                        params['max'] = constraint_value[1]
                    validators_to_run.append((mapping['type'], params))
                elif mapping['type'] == 'range':
                    if 'min' not in params and isinstance(constraint_value, (list, tuple)) and len(constraint_value) == 2:
                        params['min'] = constraint_value[0]
                        params['max'] = constraint_value[1]
                    validators_to_run.append((mapping['type'], params))
                else:
                    if not params:
                        if constraint_key in mapping['param_map']:
                            params[mapping['param_map'][constraint_key]] = constraint_value
                        else:
                            params[constraint_key] = constraint_value
                    validators_to_run.append((mapping['type'], params))

        return validators_to_run

    def _validate_fields(self, data: Dict, prefix: str) -> ValidationResult:
        result = ValidationResult()

        for field_name, field_config in self.field_rules.items():
            field_path = f"{prefix}.{field_name}" if prefix else field_name
            value = get_nested_value(data, field_name)

            validators_to_run = self.build_field_validators(field_config)

            for validator_name, validator_params in validators_to_run:
                validator = ValidatorRegistry.create_validator(validator_name, **validator_params)
                if validator:
                    field_result = validator.validate(value, field_path, data)
                    if not field_result.valid:
                        for err in field_result.errors:
                            result.add_error(err)

        return result

    def _validate_nested(self, data: Dict, prefix: str) -> ValidationResult:
        result = ValidationResult()

        for nested_name, nested_config in self.nested_rules.items():
            nested_type = nested_config.get('type', 'object')
            nested_rules = nested_config.get('rules', {})
            nested_prefix = f"{prefix}.{nested_name}" if prefix else nested_name

            nested_value = get_nested_value(data, nested_name)

            if nested_value is None:
                continue

            if nested_type == 'object':
                if isinstance(nested_value, dict):
                    sub_engine = ValidationEngine(nested_rules)
                    sub_result = sub_engine.validate(nested_value, nested_prefix)
                    result.merge(sub_result)
            elif nested_type == 'list':
                if isinstance(nested_value, list):
                    for idx, item in enumerate(nested_value):
                        item_prefix = f"{nested_prefix}.{idx}"
                        if isinstance(item, dict):
                            sub_engine = ValidationEngine(nested_rules)
                            sub_result = sub_engine.validate(item, item_prefix)
                            result.merge(sub_result)

        return result

    def _validate_cross_field(self, data: Dict, prefix: str) -> ValidationResult:
        result = ValidationResult()

        for cross_config in self.cross_field_rules:
            cross_validator = CrossFieldValidator(cross_config)
            cross_result = cross_validator.validate(data, prefix)
            result.merge(cross_result)

        return result

    def has_cross_field_rules(self) -> bool:
        if self.cross_field_rules:
            return True
        for nested_config in self.nested_rules.values():
            nested_rules = nested_config.get('rules', {})
            if nested_rules.get('cross_field'):
                return True
        return False
