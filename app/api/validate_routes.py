import time
from flask import request, jsonify

from . import api_bp
from ..engine import ValidationEngine, BatchValidator
from ..validators import init_validators, ValidatorRegistry
from ..rules import get_rules_storage
from ..logs import get_logs_storage
from ..i18n import get_message

init_validators()


@api_bp.route('/validate', methods=['POST'])
def validate():
    data = request.get_json() or {}
    
    rule_set_id = data.get('rule_set_id')
    business_id = data.get('business_id', '')
    input_data = data.get('data', {})
    
    rule_set = None
    rule_set_version = ''
    
    if rule_set_id:
        storage = get_rules_storage()
        rule_set = storage.get_rule(rule_set_id)
        if not rule_set:
            return jsonify({
                'success': False,
                'error': get_message('rule_not_found'),
                'error_key': 'rule_not_found'
            }), 404
        rule_set_version = rule_set.get('version', '')
    else:
        rule_set = data.get('rule_set', {})
    
    start_time = time.time()
    
    engine = ValidationEngine(rule_set)
    result = engine.validate(input_data)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    errors_serialized = []
    for error in result.errors:
        errors_serialized.append({
            'field': error.field,
            'message_key': error.message_key,
            'message': get_message(error.message_key, **error.message_params),
            'params': error.message_params,
            'actual_value': error.actual_value
        })
    
    error_summary = '; '.join([e['message'] for e in errors_serialized[:3]])
    if len(errors_serialized) > 3:
        error_summary += f' ... (+{len(errors_serialized) - 3} more)'
    
    logs_storage = get_logs_storage()
    logs_storage.add_log({
        'business_id': business_id,
        'rule_set_id': rule_set_id or 'inline',
        'rule_set_version': rule_set_version,
        'success': result.valid,
        'duration_ms': duration_ms,
        'error_summary': error_summary,
        'error_count': len(result.errors),
        'request_data': input_data,
        'errors': errors_serialized
    })
    
    return jsonify({
        'success': True,
        'data': {
            'valid': result.valid,
            'errors': errors_serialized,
            'error_count': len(result.errors),
            'duration_ms': duration_ms
        }
    })


@api_bp.route('/validate/batch', methods=['POST'])
def validate_batch():
    data = request.get_json() or {}
    
    items = data.get('items', [])
    business_id = data.get('business_id', '')
    
    results = []
    logs_storage = get_logs_storage()
    batch_validator = BatchValidator()
    
    for item in items:
        rule_set_id = item.get('rule_set_id')
        input_data = item.get('data', {})
        
        rule_set = None
        rule_set_version = ''
        
        if rule_set_id:
            storage = get_rules_storage()
            rule_set = storage.get_rule(rule_set_id)
            if not rule_set:
                results.append({
                    'valid': False,
                    'errors': [{
                        'field': '__system__',
                        'message_key': 'rule_not_found',
                        'message': get_message('rule_not_found'),
                        'params': {}
                    }]
                })
                continue
            rule_set_version = rule_set.get('version', '')
        else:
            rule_set = item.get('rule_set', {})
        
        start_time = time.time()
        result = batch_validator.validate_batch_fields(rule_set, input_data)
        duration_ms = int((time.time() - start_time) * 1000)
        
        errors_serialized = []
        for error in result.errors:
            errors_serialized.append({
                'field': error.field,
                'message_key': error.message_key,
                'message': get_message(error.message_key, **error.message_params),
                'params': error.message_params,
                'actual_value': error.actual_value
            })
        
        error_summary = '; '.join([e['message'] for e in errors_serialized[:3]])
        if len(errors_serialized) > 3:
            error_summary += f' ... (+{len(errors_serialized) - 3} more)'
        
        logs_storage.add_log({
            'business_id': business_id,
            'rule_set_id': rule_set_id or 'inline',
            'rule_set_version': rule_set_version,
            'success': result.valid,
            'duration_ms': duration_ms,
            'error_summary': error_summary,
            'error_count': len(result.errors),
            'request_data': input_data,
            'errors': errors_serialized
        })
        
        results.append({
            'valid': result.valid,
            'errors': errors_serialized,
            'error_count': len(result.errors),
            'duration_ms': duration_ms
        })
    
    return jsonify({
        'success': True,
        'data': {
            'results': results,
            'total': len(results)
        }
    })


@api_bp.route('/validators', methods=['GET'])
def list_validators():
    validators = ValidatorRegistry.all()
    result = []
    for name, cls in validators.items():
        result.append({
            'name': name,
            'category': getattr(cls, 'category', 'general')
        })
    return jsonify({
        'success': True,
        'data': result
    })
