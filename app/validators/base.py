from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ValidationError:
    def __init__(self, field: str, message_key: str, message_params: Optional[Dict] = None,
                 actual_value: Any = None):
        self.field = field
        self.message_key = message_key
        self.message_params = message_params or {}
        self.actual_value = actual_value


class ValidationResult:
    def __init__(self, valid: bool = True, errors: Optional[List[ValidationError]] = None):
        self.valid = valid
        self.errors = errors or []

    def add_error(self, error: ValidationError):
        self.valid = False
        self.errors.append(error)

    def merge(self, other: 'ValidationResult'):
        self.valid = self.valid and other.valid
        self.errors.extend(other.errors)


class BaseValidator(ABC):
    name = 'base'
    category = 'general'

    def __init__(self, **kwargs):
        self.params = kwargs

    @abstractmethod
    def validate(self, value: Any, field: str, all_data: Optional[Dict] = None) -> ValidationResult:
        pass
