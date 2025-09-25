# 🔄 Gemini Proxy Rotator

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance proxy server that automatically rotates between multiple Google Gemini API keys to avoid rate limits. Perfect for applications requiring high-throughput access to Gemini API.

## ✨ Features

- 🔗 **Customizable API Base URL**: Easily switch between different Gemini API endpoints
- 🔑 **Automatic Key Rotation**: Seamlessly switches between multiple API keys
- 🚀 **High Performance**: Handles both streaming and regular requests efficiently
- 🛡️ **Smart Rate Limit Handling**: Automatically detects and bypasses rate-limited keys
- 📊 **Intelligent Load Balancing**: Remembers last successful key for optimal performance
- 🔌 **Drop-in Replacement**: Works with any Gemini API client
- 📝 **Comprehensive Logging**: Detailed logs for monitoring and debugging

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/smitkunpara/gemini-proxy-rotator.git
cd gemini-proxy-rotator

# Install dependencies
pip install -r requirements.txt

# Copy environment example
cp .env.example .env
```

### Configuration

Edit `.env` file and add your Gemini API keys:

```bash
# Using JSON array format (recommended)
GEMINI_API_KEYS='["your-api-key-1", "your-api-key-2", "your-api-key-3"]'

# OR using comma-separated format
GEMINI_API_KEYS=your-api-key-1,your-api-key-2,your-api-key-3
```

### Running the Server

```bash
# Using Python directly
python -m gemini-proxy

# With custom port
python -m gemini-proxy --port 8888 --log-level DEBUG
```

## 📖 Usage

Once the proxy is running, simply point your Gemini API client to `http://localhost:8080` instead of the original Gemini API base URL. You can also configure a custom Gemini API base URL using the `GEMINI_API_BASE_URL` environment variable.

## ⚙️ Advanced Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `GEMINI_API_KEYS` | JSON array or comma-separated list of API keys | Required |
| `GEMINI_API_BASE_URL` | Base URL for the Gemini API (e.g., `https://generativelanguage.googleapis.com`) | `https://generativelanguage.googleapis.com` |
| `PROXY_PORT` | Port to run the proxy server | 8080 |
| `PROXY_HOST` | Host to bind the server | 0.0.0.0 |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `CHUNK_SIZE` | Streaming chunk size in bytes | 1024 |
| `STREAM_TIMEOUT` | Timeout for streaming requests (seconds) | 300 |
| `REQUEST_TIMEOUT` | Timeout for regular requests (seconds) | 60 |

## 🔧 How It Works

1. **Request Interception**: The proxy intercepts all requests meant for Gemini API
2. **Key Selection**: Starts with the last successful key or rotates if needed
3. **Request Forwarding**: Forwards the request with the selected API key
4. **Error Handling**: If a key is rate-limited or fails, automatically tries the next key
5. **Response Streaming**: Efficiently streams responses for streaming endpoints
6. **Success Tracking**: Remembers successful keys for optimal performance

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built to solve rate limiting issues with Google's Gemini API

## ⚠️ Disclaimer

This tool is meant for legitimate use cases where you have multiple API keys for load balancing. Please ensure you comply with Google's Gemini API terms of service.
