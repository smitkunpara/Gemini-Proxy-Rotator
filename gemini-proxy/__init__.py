"""
Gemini Proxy Rotator - A proxy server for load balancing multiple Gemini API keys
"""

__version__ = "1.0.0"
__author__ = "Smit Kunpara"
__license__ = "MIT"

from .server import run_server
from .config import Config

__all__ = ["run_server", "Config"]