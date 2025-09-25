"""Utility functions for Gemini Proxy"""

import json
from typing import Dict, Any


def parse_json_safely(data: bytes) -> Dict[str, Any]:
    """Safely parse JSON data"""
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} TB"