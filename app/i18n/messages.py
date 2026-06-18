MESSAGES = {
    'zh': {
        'required': '{field} 是必填项',
        'string_min_length': '{field} 长度不能少于 {min} 个字符',
        'string_max_length': '{field} 长度不能超过 {max} 个字符',
        'string_length': '{field} 长度必须在 {min} 到 {max} 个字符之间',
        'number_min': '{field} 不能小于 {min}',
        'number_max': '{field} 不能大于 {max}',
        'number_range': '{field} 必须在 {min} 到 {max} 之间',
        'regex_pattern': '{field} 格式不正确',
        'enum_whitelist': '{field} 必须是 {allowed} 之一',
        'enum_blacklist': '{field} 不能是 {forbidden} 中的值',
        'date_format': '{field} 日期格式不正确，应为 {format}',
        'date_min': '{field} 不能早于 {min_date}',
        'date_max': '{field} 不能晚于 {max_date}',
        'date_range': '{field} 必须在 {min_date} 到 {max_date} 之间',
        'type_error': '{field} 类型错误，期望 {expected} 类型',
        
        'id_card_invalid': '身份证号格式不正确',
        'id_card_birthday_invalid': '身份证出生日期无效',
        'id_card_checksum_invalid': '身份证校验码错误',
        
        'phone_invalid': '手机号格式不正确',
        'phone_prefix_invalid': '手机号段不正确',
        
        'bank_card_invalid': '银行卡号格式不正确',
        'bank_card_luhn_invalid': '银行卡号校验失败',
        
        'cross_field_generic': '字段联合校验失败: {message}',
        'cross_field_start_before_end': '{start_field} 必须早于 {end_field}',
        'cross_field_fields_equal': '{field1} 必须与 {field2} 一致',
        'cross_field_fields_not_equal': '{field1} 不能与 {field2} 相同',
        
        'nested_field_error': '嵌套字段校验失败',
        
        'rule_not_found': '规则集不存在',
        'rule_already_exists': '规则集已存在',
        'rule_invalid': '规则集格式无效',
        
        'log_not_found': '校验日志不存在',
        
        'success': '校验通过',
        'failed': '校验失败',
    },
    'en': {
        'required': '{field} is required',
        'string_min_length': '{field} must be at least {min} characters',
        'string_max_length': '{field} must be at most {max} characters',
        'string_length': '{field} must be between {min} and {max} characters',
        'number_min': '{field} cannot be less than {min}',
        'number_max': '{field} cannot be greater than {max}',
        'number_range': '{field} must be between {min} and {max}',
        'regex_pattern': '{field} format is invalid',
        'enum_whitelist': '{field} must be one of {allowed}',
        'enum_blacklist': '{field} cannot be any of {forbidden}',
        'date_format': '{field} date format is invalid, expected {format}',
        'date_min': '{field} cannot be earlier than {min_date}',
        'date_max': '{field} cannot be later than {max_date}',
        'date_range': '{field} must be between {min_date} and {max_date}',
        'type_error': '{field} type error, expected {expected} type',
        
        'id_card_invalid': 'ID card number format is invalid',
        'id_card_birthday_invalid': 'ID card birthday is invalid',
        'id_card_checksum_invalid': 'ID card checksum is incorrect',
        
        'phone_invalid': 'Phone number format is invalid',
        'phone_prefix_invalid': 'Phone number prefix is invalid',
        
        'bank_card_invalid': 'Bank card number format is invalid',
        'bank_card_luhn_invalid': 'Bank card number Luhn check failed',
        
        'cross_field_generic': 'Cross-field validation failed: {message}',
        'cross_field_start_before_end': '{start_field} must be earlier than {end_field}',
        'cross_field_fields_equal': '{field1} must match {field2}',
        'cross_field_fields_not_equal': '{field1} cannot be the same as {field2}',
        
        'nested_field_error': 'Nested field validation failed',
        
        'rule_not_found': 'Rule set not found',
        'rule_already_exists': 'Rule set already exists',
        'rule_invalid': 'Rule set format is invalid',
        
        'log_not_found': 'Validation log not found',
        
        'success': 'Validation passed',
        'failed': 'Validation failed',
    }
}
