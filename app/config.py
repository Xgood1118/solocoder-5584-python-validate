import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    PORT = 5001
    DEBUG = True
    
    THREAD_POOL_MAX_WORKERS = 10
    
    RULES_STORAGE_PATH = os.environ.get('RULES_STORAGE_PATH', 'data/rules.json')
    LOGS_STORAGE_PATH = os.environ.get('LOGS_STORAGE_PATH', 'data/logs.json')
    
    DEFAULT_LANGUAGE = 'zh'
    SUPPORTED_LANGUAGES = ['zh', 'en']
