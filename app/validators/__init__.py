from .base import BaseValidator, ValidationResult, ValidationError
from .builtin import BUILTIN_VALIDATORS
from .custom import ValidatorRegistry, register_validator
from . import custom


def init_validators():
    for name, validator_cls in BUILTIN_VALIDATORS.items():
        ValidatorRegistry.register(name, validator_cls)


__all__ = [
    'BaseValidator',
    'ValidationResult',
    'ValidationError',
    'BUILTIN_VALIDATORS',
    'ValidatorRegistry',
    'register_validator',
    'init_validators',
]
