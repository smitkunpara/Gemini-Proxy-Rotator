from http.server import BaseHTTPRequestHandler
import json
import logging
import requests
from urllib.parse import urlparse, parse_qsl, urlencode
import time
from typing import Optional, Dict, Any

from .config import Config


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Gemini API proxy with key rotation"""
    
    config: Config = None
    _last_successful_index: int = 0
    
    @classmethod
    def set_config(cls, config: Config):
        """Set configuration for the handler"""
        cls.config = config
    
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super().__init__(*args, **kwargs)
    
    def is_streaming_request(self, path: str, post_data: Optional[bytes] = None) -> bool:
        """Detect if this is a streaming request by path or request body."""
        if 'streamGenerateContent' in path:
            return True
        if 'stream' in path.lower():
            return True
        
        if post_data:
            try:
                body = post_data.decode('utf-8', errors='ignore').lower()
                if 'stream' in body or 'streaming' in body or 'responsetype": "stream' in body:
                    return True
            except Exception:
                pass
        return False
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Parse URL
            parsed_url = urlparse(self.path)
            query_params = [(k, v) for k, v in parse_qsl(parsed_url.query)
                           if k.lower() not in ('key', 'api_key')]
            
            # Detect streaming
            is_streaming = self.is_streaming_request(parsed_url.path, post_data)
            self.logger.info("Request type: %s", 'STREAMING' if is_streaming else 'NORMAL')
            
            # Process request with key rotation
            self._process_with_rotation(parsed_url, query_params, post_data, is_streaming)
            
        except Exception as e:
            self.logger.exception("Error handling POST request: %s", e)
            self.send_json_error(500, "INTERNAL", "Internal server error")
    
    def _process_with_rotation(self, parsed_url, query_params, post_data, is_streaming):
        """Process request with API key rotation"""
        gemini_base = self.config.gemini_api_base_url
        
        n_keys = len(self.config.api_keys)
        if n_keys == 0:
            self.logger.error('No API keys available')
            self.send_json_error(500, "INTERNAL", "No API keys configured")
            return
        
        # Generate rotation order
        start_index = self.__class__._last_successful_index
        try_order = [(start_index + i) % n_keys for i in range(n_keys)]
        
        self.logger.info('Starting from key index: %s', start_index)
        
        error_response = None
        last_error_type = None
        last_status_code = 503
        
        for i, key_index in enumerate(try_order):
            current_api_key = self.config.api_keys[key_index]
            self.logger.info('Trying key %s (attempt %s/%s)', key_index, i + 1, n_keys)
            
            # Build request URL
            full_query_params = query_params + [('key', current_api_key)]
            new_query = urlencode(full_query_params)
            forward_url = gemini_base + parsed_url.path
            if new_query:
                forward_url += '?' + new_query
            
            headers = {'Content-Type': 'application/json'}
            
            try:
                timeout = (10, self.config.stream_timeout if is_streaming else self.config.request_timeout)
                response = requests.post(
                    forward_url,
                    headers=headers,
                    data=post_data,
                    stream=is_streaming,
                    timeout=timeout
                )
                
                self.logger.info('Response status %s for key %s', response.status_code, key_index)
                
                # Handle various response codes
                if response.status_code == 429:
                    self.logger.warning('Key %s rate limited (429)', key_index)
                    error_response = response
                    last_error_type = "rate_limited"
                    last_status_code = 429
                    response.close()
                    continue
                
                if response.status_code >= 500:
                    self.logger.warning('Key %s got server error (%s)', key_index, response.status_code)
                    last_status_code = response.status_code
                    last_error_type = "server_error"
                    error_response = response
                    response.close()
                    continue
                
                if 400 <= response.status_code < 500:
                    self.logger.warning('Key %s got client error (%s)', key_index, response.status_code)
                    self._forward_error_response(response)
                    response.close()
                    return
                
                # Success - handle response
                if is_streaming:
                    success = self._handle_streaming_response(response, key_index)
                else:
                    success = self._handle_normal_response(response, key_index)
                
                if success:
                    self.__class__._last_successful_index = key_index
                    self.logger.info('Success with key %s', key_index)
                    return
                else:
                    last_error_type = "processing_failed"
                    continue
                    
            except requests.exceptions.Timeout:
                self.logger.warning('Timeout for key %s', key_index)
                last_error_type = "timeout"
                last_status_code = 504
                continue
            except requests.exceptions.ConnectionError:
                self.logger.warning('Connection error for key %s', key_index)
                last_error_type = "connection_error"
                last_status_code = 503
                continue
            except Exception as e:
                self.logger.exception('Exception for key %s: %s', key_index, e)
                last_error_type = "unknown_error"
                last_status_code = 500
                continue
        
        # All keys failed
        self.logger.error('All API keys failed')
        self._send_final_error_response(error_response, last_error_type, last_status_code)
    
    def _handle_streaming_response(self, response, key_index: int) -> bool:
        """Handle streaming response"""
        try:
            # Send headers
            self.send_response(response.status_code)
            for k, v in response.headers.items():
                if k.lower() in ('transfer-encoding', 'content-encoding'):
                    continue
                self.send_header(k, v)
            
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            
            chunk_count = 0
            
            # Stream chunks
            for chunk in response.iter_content(chunk_size=self.config.chunk_size, decode_unicode=False):
                if not chunk:
                    continue
                chunk_count += 1
                
                try:
                    # Send chunk with HTTP chunked encoding
                    size_line = ("%x\r\n" % len(chunk)).encode('utf-8')
                    self.wfile.write(size_line)
                    self.wfile.write(chunk)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    self.logger.info('Client disconnected during streaming')
                    response.close()
                    return True
                except Exception as e:
                    self.logger.exception('Error writing chunk: %s', e)
                    response.close()
                    return False
            
            # Check for remaining data
            try:
                remaining = response.raw.read()
                if remaining:
                    self.logger.info('Found %s bytes of remaining data', len(remaining))
                    size_line = ("%x\r\n" % len(remaining)).encode('utf-8')
                    self.wfile.write(size_line)
                    self.wfile.write(remaining)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
            except Exception:
                pass
            
            # Send terminating chunk
            try:
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
                time.sleep(0.01)  # Ensure data is sent
            except Exception:
                pass
            
            response.close()
            self.logger.info('Streaming completed, sent %s chunks', chunk_count)
            return True
            
        except Exception as e:
            self.logger.exception('Streaming error: %s', e)
            try:
                response.close()
            except:
                pass
            return False
    
    def _handle_normal_response(self, response, key_index: int) -> bool:
        """Handle normal (non-streaming) response"""
        try:
            response_content = response.content
            
            # Check for UNAVAILABLE error
            try:
                response_json = json.loads(response_content.decode('utf-8'))
                if isinstance(response_json, dict) and 'error' in response_json:
                    err_status = response_json.get('error', {}).get('status', '')
                    if err_status == 'UNAVAILABLE':
                        self.logger.warning('UNAVAILABLE error for key %s', key_index)
                        response.close()
                        return False
            except:
                pass
            
            # Send response
            self.send_response(response.status_code)
            for k, v in response.headers.items():
                if k.lower() not in ('transfer-encoding', 'content-encoding'):
                    self.send_header(k, v)
            self.end_headers()
            
            self.wfile.write(response_content)
            self.wfile.flush()
            
            response.close()
            return True
            
        except Exception as e:
            self.logger.exception('Normal response error: %s', e)
            try:
                response.close()
            except:
                pass
            return False
    
    def _forward_error_response(self, response):
        """Forward error response from API"""
        try:
            error_data = response.json()
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode())
        except:
            self.send_json_error(response.status_code, "INVALID_ARGUMENT", "Bad request")
    
    def _send_final_error_response(self, error_response, last_error_type: str, last_status_code: int):
        """Send final error response when all keys fail"""
        if error_response is not None:
            try:
                error_content = error_response.content
                error_json = json.loads(error_content)
                self.send_response(error_response.status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_json).encode())
                return
            except:
                pass
        
        # Generate appropriate error
        error_map = {
            "rate_limited": (429, "RESOURCE_EXHAUSTED", "All API keys have exceeded their rate limits"),
            "timeout": (504, "DEADLINE_EXCEEDED", "Request timeout - all API keys failed to respond"),
            "connection_error": (503, "UNAVAILABLE", "Service temporarily unavailable"),
            "server_error": (last_status_code, "INTERNAL", "Internal server error"),
        }
        
        status, error_status, message = error_map.get(
            last_error_type, 
            (503, "UNAVAILABLE", "All API keys failed")
        )
        
        self.send_json_error(status, error_status, message)
    
    def send_json_error(self, status_code: int, error_status: str, message: str, details: Optional[list] = None):
        """Send JSON error response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_obj = {
            "error": {
                "code": status_code,
                "message": message,
                "status": error_status
            }
        }
        
        if details:
            error_obj["error"]["details"] = details
        
        self.wfile.write(json.dumps(error_obj).encode())
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_json_error(405, "METHOD_NOT_ALLOWED", "Only POST requests are supported")
    
    def log_message(self, format, *args):
        """Override to use custom logger"""
        self.logger.info(format % args)