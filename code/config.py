#!/usr/bin/env python3
"""
Configuration settings for Sequencing Data Management System
"""

import os
from typing import Dict, Any

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/app/uploads')
    DATA_FOLDER = os.environ.get('DATA_FOLDER', '/data')
    LOGS_FOLDER = os.environ.get('LOGS_FOLDER', '/app/logs')
    
    # Scanning settings
    MAX_SCAN_THREADS = int(os.environ.get('MAX_SCAN_THREADS', '4'))
    ENABLE_DETAILED_LOGGING = os.environ.get('ENABLE_DETAILED_LOGGING', 'True').lower() == 'true'
    CHUNK_SIZE_MB = int(os.environ.get('CHUNK_SIZE_MB', '10'))  # For file hashing
    
    # Security settings
    ALLOW_DELETE_OPERATIONS = os.environ.get('ALLOW_DELETE_OPERATIONS', 'True').lower() == 'true'
    REQUIRE_CONFIRMATION = os.environ.get('REQUIRE_CONFIRMATION', 'True').lower() == 'true'
    
    # Performance settings
    MAX_FILES_PER_CATEGORY = int(os.environ.get('MAX_FILES_PER_CATEGORY', '10000'))
    ENABLE_DUPLICATE_DETECTION = os.environ.get('ENABLE_DUPLICATE_DETECTION', 'True').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure required directories exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOGS_FOLDER, exist_ok=True)
        
        # Set up logging
        if Config.ENABLE_DETAILED_LOGGING:
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(os.path.join(Config.LOGS_FOLDER, 'app.log')),
                    logging.StreamHandler()
                ]
            )

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENABLE_DETAILED_LOGGING = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            # Set up file logging with rotation
            file_handler = RotatingFileHandler(
                os.path.join(cls.LOGS_FOLDER, 'seqmanager.log'),
                maxBytes=10485760,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Sequencing Data Manager startup')

class DockerConfig(ProductionConfig):
    """Docker-specific configuration."""
    DATA_FOLDER = '/data'
    LOGS_FOLDER = '/app/logs'
    UPLOAD_FOLDER = '/app/uploads'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}

def get_config() -> Config:
    """Get configuration based on environment."""
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config.get(config_name, config['default'])
