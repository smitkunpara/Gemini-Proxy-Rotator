import os
import json
import logging
from typing import List
from pathlib import Path


class Config:
    """Configuration management for Gemini Proxy"""
    
    def __init__(self):
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Load API keys from environment
        api_keys_json = os.getenv('GEMINI_API_KEYS', '[]')
        try:
            self.api_keys = json.loads(api_keys_json)
            if not isinstance(self.api_keys, list):
                raise ValueError("GEMINI_API_KEYS must be a JSON list")
        except json.JSONDecodeError:
            # Try comma-separated format as fallback
            api_keys_str = os.getenv('GEMINI_API_KEYS', '')
            if api_keys_str:
                self.api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        
        # Load other configurations
        self.port = int(os.getenv('PROXY_PORT', '8080'))
        self.host = os.getenv('PROXY_HOST', '0.0.0.0')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '1024'))
        self.stream_timeout = int(os.getenv('STREAM_TIMEOUT', '300'))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '60'))
        self.gemini_api_base_url = os.getenv('GEMINI_API_BASE_URL', 'https://generativelanguage.googleapis.com')
    
    def validate(self):
        """Validate configuration"""
        if not self.api_keys:
            raise ValueError("No API keys configured. Please set GEMINI_API_KEYS environment variable.")
        
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")
        
        return True
    
    def get_logging_config(self):
        """Get logging configuration"""
        return {
            'level': getattr(logging, self.log_level.upper(), logging.INFO),
            'format': '[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }