import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseValidator, ValidationResult, ValidationError
from ..i18n import get_message


class RequiredValidator(BaseValidator):
    name = 'required'
    category = 'general'

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None or (isinstance(value, str) and value.strip() == ''):
            result.add_error(ValidationError(
                field=field,
                message_key='required',
                message_params={'field': field},
                actual_value=value
            ))
        
        return result


class MinLengthValidator(BaseValidator):
    name = 'min_length'
    category = 'string'

    def __init__(self, min: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.min = min

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        if len(value) < self.min:
            result.add_error(ValidationError(
                field=field,
                message_key='string_min_length',
                message_params={'field': field, 'min': self.min},
                actual_value=len(value)
            ))
        
        return result


class MaxLengthValidator(BaseValidator):
    name = 'max_length'
    category = 'string'

    def __init__(self, max: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.max = max

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        if len(value) > self.max:
            result.add_error(ValidationError(
                field=field,
                message_key='string_max_length',
                message_params={'field': field, 'max': self.max},
                actual_value=len(value)
            ))
        
        return result


class LengthValidator(BaseValidator):
    name = 'length'
    category = 'string'

    def __init__(self, min: int = 0, max: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.min = min
        self.max = max

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        length = len(value)
        if length < self.min or length > self.max:
            result.add_error(ValidationError(
                field=field,
                message_key='string_length',
                message_params={'field': field, 'min': self.min, 'max': self.max},
                actual_value=length
            ))
        
        return result


class MinValidator(BaseValidator):
    name = 'min'
    category = 'number'

    def __init__(self, min: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.min = min

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, (int, float)):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'number'},
                actual_value=type(value).__name__
            ))
            return result
        
        if value < self.min:
            result.add_error(ValidationError(
                field=field,
                message_key='number_min',
                message_params={'field': field, 'min': self.min},
                actual_value=value
            ))
        
        return result


class MaxValidator(BaseValidator):
    name = 'max'
    category = 'number'

    def __init__(self, max: float = 100, **kwargs):
        super().__init__(**kwargs)
        self.max = max

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, (int, float)):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'number'},
                actual_value=type(value).__name__
            ))
            return result
        
        if value > self.max:
            result.add_error(ValidationError(
                field=field,
                message_key='number_max',
                message_params={'field': field, 'max': self.max},
                actual_value=value
            ))
        
        return result


class RangeValidator(BaseValidator):
    name = 'range'
    category = 'number'

    def __init__(self, min: float = 0, max: float = 100, **kwargs):
        super().__init__(**kwargs)
        self.min = min
        self.max = max

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, (int, float)):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'number'},
                actual_value=type(value).__name__
            ))
            return result
        
        if value < self.min or value > self.max:
            result.add_error(ValidationError(
                field=field,
                message_key='number_range',
                message_params={'field': field, 'min': self.min, 'max': self.max},
                actual_value=value
            ))
        
        return result


class RegexValidator(BaseValidator):
    name = 'regex'
    category = 'format'

    def __init__(self, pattern: str = '', **kwargs):
        super().__init__(**kwargs)
        self.pattern = pattern
        self._regex = re.compile(pattern) if pattern else None

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None or not self._regex:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        if not self._regex.match(value):
            result.add_error(ValidationError(
                field=field,
                message_key='regex_pattern',
                message_params={'field': field, 'pattern': self.pattern},
                actual_value=value
            ))
        
        return result


class EnumWhitelistValidator(BaseValidator):
    name = 'enum_whitelist'
    category = 'enum'

    def __init__(self, allowed: Optional[List[Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed = allowed or []

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if value not in self.allowed:
            result.add_error(ValidationError(
                field=field,
                message_key='enum_whitelist',
                message_params={'field': field, 'allowed': ', '.join(map(str, self.allowed))},
                actual_value=value
            ))
        
        return result


class EnumBlacklistValidator(BaseValidator):
    name = 'enum_blacklist'
    category = 'enum'

    def __init__(self, forbidden: Optional[List[Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self.forbidden = forbidden or []

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if value in self.forbidden:
            result.add_error(ValidationError(
                field=field,
                message_key='enum_blacklist',
                message_params={'field': field, 'forbidden': ', '.join(map(str, self.forbidden))},
                actual_value=value
            ))
        
        return result


class DateFormatValidator(BaseValidator):
    name = 'date_format'
    category = 'date'

    def __init__(self, format: str = '%Y-%m-%d', **kwargs):
        super().__init__(**kwargs)
        self.format = format

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        try:
            datetime.strptime(value, self.format)
        except ValueError:
            result.add_error(ValidationError(
                field=field,
                message_key='date_format',
                message_params={'field': field, 'format': self.format},
                actual_value=value
            ))
        
        return result


class DateMinValidator(BaseValidator):
    name = 'date_min'
    category = 'date'

    def __init__(self, min_date: str = '', format: str = '%Y-%m-%d', **kwargs):
        super().__init__(**kwargs)
        self.min_date_str = min_date
        self.format = format
        self.min_date = datetime.strptime(min_date, format) if min_date else None

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None or self.min_date is None:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        try:
            date_val = datetime.strptime(value, self.format)
        except ValueError:
            result.add_error(ValidationError(
                field=field,
                message_key='date_format',
                message_params={'field': field, 'format': self.format},
                actual_value=value
            ))
            return result
        
        if date_val < self.min_date:
            result.add_error(ValidationError(
                field=field,
                message_key='date_min',
                message_params={'field': field, 'min_date': self.min_date_str},
                actual_value=value
            ))
        
        return result


class DateMaxValidator(BaseValidator):
    name = 'date_max'
    category = 'date'

    def __init__(self, max_date: str = '', format: str = '%Y-%m-%d', **kwargs):
        super().__init__(**kwargs)
        self.max_date_str = max_date
        self.format = format
        self.max_date = datetime.strptime(max_date, format) if max_date else None

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None or self.max_date is None:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        try:
            date_val = datetime.strptime(value, self.format)
        except ValueError:
            result.add_error(ValidationError(
                field=field,
                message_key='date_format',
                message_params={'field': field, 'format': self.format},
                actual_value=value
            ))
            return result
        
        if date_val > self.max_date:
            result.add_error(ValidationError(
                field=field,
                message_key='date_max',
                message_params={'field': field, 'max_date': self.max_date_str},
                actual_value=value
            ))
        
        return result


class DateRangeValidator(BaseValidator):
    name = 'date_range'
    category = 'date'

    def __init__(self, min_date: str = '', max_date: str = '', format: str = '%Y-%m-%d', **kwargs):
        super().__init__(**kwargs)
        self.min_date_str = min_date
        self.max_date_str = max_date
        self.format = format
        self.min_date = datetime.strptime(min_date, format) if min_date else None
        self.max_date = datetime.strptime(max_date, format) if max_date else None

    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if not isinstance(value, str):
            result.add_error(ValidationError(
                field=field,
                message_key='type_error',
                message_params={'field': field, 'expected': 'string'},
                actual_value=type(value).__name__
            ))
            return result
        
        try:
            date_val = datetime.strptime(value, self.format)
        except ValueError:
            result.add_error(ValidationError(
                field=field,
                message_key='date_format',
                message_params={'field': field, 'format': self.format},
                actual_value=value
            ))
            return result
        
        if self.min_date and date_val < self.min_date:
            result.add_error(ValidationError(
                field=field,
                message_key='date_range',
                message_params={
                    'field': field,
                    'min_date': self.min_date_str,
                    'max_date': self.max_date_str
                },
                actual_value=value
            ))
        elif self.max_date and date_val > self.max_date:
            result.add_error(ValidationError(
                field=field,
                message_key='date_range',
                message_params={
                    'field': field,
                    'min_date': self.min_date_str,
                    'max_date': self.max_date_str
                },
                actual_value=value
            ))
        
        return result


BUILTIN_VALIDATORS = {
    'required': RequiredValidator,
    'min_length': MinLengthValidator,
    'max_length': MaxLengthValidator,
    'length': LengthValidator,
    'min': MinValidator,
    'max': MaxValidator,
    'range': RangeValidator,
    'regex': RegexValidator,
    'enum_whitelist': EnumWhitelistValidator,
    'enum_blacklist': EnumBlacklistValidator,
    'date_format': DateFormatValidator,
    'date_min': DateMinValidator,
    'date_max': DateMaxValidator,
    'date_range': DateRangeValidator,
}
