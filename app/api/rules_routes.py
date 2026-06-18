from flask import request, jsonify, Response

from . import api_bp
from ..rules import get_rules_storage
from ..i18n import get_message
import json


@api_bp.route('/rules', methods=['GET'])
def list_rules():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    storage = get_rules_storage()
    result = storage.list_rules(page=page, page_size=page_size)
    
    return jsonify({
        'success': True,
        'data': result
    })


@api_bp.route('/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    storage = get_rules_storage()
    rule = storage.get_rule(rule_id)
    
    if not rule:
        return jsonify({
            'success': False,
            'error': get_message('rule_not_found'),
            'error_key': 'rule_not_found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': rule
    })


@api_bp.route('/rules', methods=['POST'])
def create_rule():
    data = request.get_json() or {}
    
    storage = get_rules_storage()
    try:
        rule = storage.create_rule(data)
    except ValueError as e:
        if str(e) == 'rule_already_exists':
            return jsonify({
                'success': False,
                'error': get_message('rule_already_exists'),
                'error_key': 'rule_already_exists'
            }), 409
        raise
    
    return jsonify({
        'success': True,
        'data': rule
    }), 201


@api_bp.route('/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    data = request.get_json() or {}
    
    storage = get_rules_storage()
    rule = storage.update_rule(rule_id, data)
    
    if not rule:
        return jsonify({
            'success': False,
            'error': get_message('rule_not_found'),
            'error_key': 'rule_not_found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': rule
    })


@api_bp.route('/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    storage = get_rules_storage()
    success = storage.delete_rule(rule_id)
    
    if not success:
        return jsonify({
            'success': False,
            'error': get_message('rule_not_found'),
            'error_key': 'rule_not_found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': {'deleted': True}
    })


@api_bp.route('/rules/<rule_id>/export', methods=['GET'])
def export_rule(rule_id):
    storage = get_rules_storage()
    export_data = storage.export_rule(rule_id)
    
    if not export_data:
        return jsonify({
            'success': False,
            'error': get_message('rule_not_found'),
            'error_key': 'rule_not_found'
        }), 404
    
    json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    return Response(
        json_data,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=rule_{rule_id}.json'
        }
    )


@api_bp.route('/rules/import', methods=['POST'])
def import_rule():
    data = request.get_json() or {}
    overwrite = request.args.get('overwrite', 'false').lower() == 'true'
    
    storage = get_rules_storage()
    result = storage.import_rule(data, overwrite=overwrite)
    
    if not result.get('success'):
        return jsonify({
            'success': False,
            'error': get_message(result.get('error', 'rule_invalid')),
            'error_key': result.get('error', 'rule_invalid')
        }), 400
    
    return jsonify({
        'success': True,
        'data': result
    })


@api_bp.route('/rules/export/all', methods=['GET'])
def export_all_rules():
    storage = get_rules_storage()
    export_data = storage.export_all()
    
    json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    return Response(
        json_data,
        mimetype='application/json',
        headers={
            'Content-Disposition': 'attachment; filename=all_rules.json'
        }
    )


@api_bp.route('/rules/import/all', methods=['POST'])
def import_all_rules():
    data = request.get_json() or {}
    overwrite = request.args.get('overwrite', 'false').lower() == 'true'
    
    storage = get_rules_storage()
    result = storage.import_all(data, overwrite=overwrite)
    
    return jsonify({
        'success': True,
        'data': result
    })
