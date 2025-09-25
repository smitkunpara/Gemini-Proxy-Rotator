from http.server import HTTPServer
import logging
import signal
import sys
from typing import Optional

from .config import Config
from .proxy_handler import ProxyHTTPRequestHandler


def run_server(config: Optional[Config] = None, daemon: bool = False):
    """
    Run the Gemini proxy server
    
    Args:
        config: Configuration object (uses default if None)
        daemon: Run as daemon process
    """
    if config is None:
        config = Config()
    
    # Validate configuration
    config.validate()
    
    # Setup logging
    logging.basicConfig(**config.get_logging_config())
    logger = logging.getLogger(__name__)
    
    # Set configuration in handler
    ProxyHTTPRequestHandler.set_config(config)
    
    # Create server
    server_address = (config.host, config.port)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    
    logger.info('🚀 Gemini Proxy Server starting...')
    logger.info('🔑 Loaded %s API keys', len(config.api_keys))
    logger.info('🌐 Server running at http://%s:%s', config.host, config.port)
    logger.info('Press Ctrl+C to stop the server')
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info('\n🛑 Shutting down proxy server...')
        httpd.server_close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('\n🛑 Shutting down proxy server...')
        httpd.server_close()