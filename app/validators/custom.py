import re
import calendar
from datetime import datetime
from typing import Any, Dict, Optional

from .base import BaseValidator, ValidationResult, ValidationError
from ..i18n import get_message


class ValidatorRegistry:
    _validators: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, validator_class: type):
        cls._validators[name] = validator_class

    @classmethod
    def get(cls, name: str) -> Optional[type]:
        return cls._validators.get(name)

    @classmethod
    def all(cls) -> Dict[str, type]:
        return dict(cls._validators)

    @classmethod
    def create_validator(cls, name: str, **params) -> Optional[BaseValidator]:
        validator_cls = cls.get(name)
        if validator_cls:
            return validator_cls(**params)
        return None


def register_validator(name: str):
    def decorator(validator_cls):
        ValidatorRegistry.register(name, validator_cls)
        return validator_cls
    return decorator


@register_validator('id_card')
class IDCardValidator(BaseValidator):
    name = 'id_card'
    category = 'builtin'

    _WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    _CHECK_CODES = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

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
        
        value = value.strip().upper()
        
        if not re.match(r'^\d{17}[\dX]$', value):
            result.add_error(ValidationError(
                field=field,
                message_key='id_card_invalid',
                message_params={'field': field},
                actual_value=value
            ))
            return result
        
        year = int(value[6:10])
        month = int(value[10:12])
        day = int(value[12:14])
        
        try:
            if month < 1 or month > 12:
                raise ValueError("Invalid month")
            if day < 1 or day > calendar.monthrange(year, month)[1]:
                raise ValueError("Invalid day")
            datetime(year, month, day)
        except (ValueError, calendar.IllegalMonthError):
            result.add_error(ValidationError(
                field=field,
                message_key='id_card_birthday_invalid',
                message_params={'field': field},
                actual_value=value
            ))
            return result
        
        total = sum(int(value[i]) * self._WEIGHTS[i] for i in range(17))
        check_code = self._CHECK_CODES[total % 11]
        
        if value[17] != check_code:
            result.add_error(ValidationError(
                field=field,
                message_key='id_card_checksum_invalid',
                message_params={'field': field},
                actual_value=value
            ))
        
        return result


@register_validator('phone')
class PhoneValidator(BaseValidator):
    name = 'phone'
    category = 'builtin'

    _VALID_PREFIXES = {
        '130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
        '145', '146', '147', '148', '149',
        '150', '151', '152', '153', '155', '156', '157', '158', '159',
        '162', '165', '166', '167',
        '170', '171', '172', '173', '175', '176', '177', '178',
        '180', '181', '182', '183', '184', '185', '186', '187', '188', '189',
        '190', '191', '192', '193', '195', '196', '197', '198', '199',
    }

    def __init__(self, check_prefix: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.check_prefix = check_prefix

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
        
        value = value.strip()
        
        if not re.match(r'^1\d{10}$', value):
            result.add_error(ValidationError(
                field=field,
                message_key='phone_invalid',
                message_params={'field': field},
                actual_value=value
            ))
            return result
        
        if self.check_prefix:
            prefix = value[:3]
            if prefix not in self._VALID_PREFIXES:
                result.add_error(ValidationError(
                    field=field,
                    message_key='phone_prefix_invalid',
                    message_params={'field': field},
                    actual_value=value
                ))
        
        return result


@register_validator('bank_card')
class BankCardValidator(BaseValidator):
    name = 'bank_card'
    category = 'builtin'

    def __init__(self, check_luhn: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.check_luhn = check_luhn

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
        
        value = value.replace(' ', '').replace('-', '')
        
        if not re.match(r'^\d{12,19}$', value):
            result.add_error(ValidationError(
                field=field,
                message_key='bank_card_invalid',
                message_params={'field': field},
                actual_value=value
            ))
            return result
        
        if self.check_luhn:
            digits = [int(d) for d in value]
            checksum = 0
            for i, digit in enumerate(reversed(digits)):
                if i % 2 == 1:
                    digit *= 2
                    if digit > 9:
                        digit -= 9
                checksum += digit
            
            if checksum % 10 != 0:
                result.add_error(ValidationError(
                    field=field,
                    message_key='bank_card_luhn_invalid',
                    message_params={'field': field},
                    actual_value=value
                ))
        
        return result
