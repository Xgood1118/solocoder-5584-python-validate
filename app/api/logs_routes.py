from flask import request, jsonify

from . import api_bp
from ..logs import get_logs_storage
from ..i18n import get_message


@api_bp.route('/logs', methods=['GET'])
def query_logs():
    business_id = request.args.get('business_id')
    start_time = request.args.get('start_time', type=int)
    end_time = request.args.get('end_time', type=int)
    success = request.args.get('success')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    success_bool = None
    if success is not None:
        success_bool = success.lower() == 'true'
    
    storage = get_logs_storage()
    result = storage.query_logs(
        business_id=business_id,
        start_time=start_time,
        end_time=end_time,
        success=success_bool,
        page=page,
        page_size=page_size
    )
    
    return jsonify({
        'success': True,
        'data': result
    })


@api_bp.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    storage = get_logs_storage()
    log = storage.get_log(log_id)
    
    if not log:
        return jsonify({
            'success': False,
            'error': get_message('log_not_found'),
            'error_key': 'log_not_found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': log
    })


@api_bp.route('/logs/statistics', methods=['GET'])
def get_log_statistics():
    business_id = request.args.get('business_id')
    start_time = request.args.get('start_time', type=int)
    end_time = request.args.get('end_time', type=int)
    
    storage = get_logs_storage()
    result = storage.get_statistics(
        business_id=business_id,
        start_time=start_time,
        end_time=end_time
    )
    
    return jsonify({
        'success': True,
        'data': result
    })
