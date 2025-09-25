#!/usr/bin/env python3
"""
Command-line interface for Gemini Proxy
"""

from dotenv import load_dotenv
load_dotenv()
import argparse
import sys
from .server import run_server
from .config import Config


def main():
    parser = argparse.ArgumentParser(
        description='Gemini Proxy Rotator - Load balance multiple Gemini API keys'
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        help='Port to run the proxy server on (default: from env or 8080)'
    )
    parser.add_argument(
        '-H', '--host',
        type=str,
        help='Host to bind the server to (default: from env or 0.0.0.0)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level'
    )
    
    args = parser.parse_args()
    
    # Create config
    config = Config()
    
    # Override with command line args
    if args.port:
        config.port = args.port
    if args.host:
        config.host = args.host
    if args.log_level:
        config.log_level = args.log_level
    
    # Run server
    try:
        run_server(config)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()