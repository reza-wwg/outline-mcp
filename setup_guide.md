# Outline MCP Server - Complete Setup Guide

This guide provides step-by-step instructions to create and set up the Outline MCP Server from scratch.

## Project Structure

Create the following directory structure:

```
outline-mcp-server/
├── outline_mcp_server.py      # Main server implementation
├── __init__.py                # Package initialization
├── pyproject.toml             # UV package configuration
├── README.md                  # Documentation
├── LICENSE                    # MIT License
├── .env.example              # Environment variables template
├── SETUP_GUIDE.md            # This file
├── tests/                    # Test directory
│   ├── __init__.py
│   └── test_server.py        # Unit tests
└── .github/                  # GitHub Actions
    └── workflows/
        └── ci.yml            # CI/CD pipeline
```

## Step-by-Step Setup

### 1. Prerequisites

Install the required tools:

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your terminal or source your shell profile
source ~/.bashrc  # or ~/.zshrc
```

### 2. Create Project Directory

```bash
mkdir outline-mcp-server
cd outline-mcp-server
```

### 3. Initialize Python Project

```bash
# Initialize with UV
uv init --name outline-mcp-server

# Or manually create the files shown in the artifacts above
```

### 4. Create Project Files

Create each file using the contents from the artifacts:

1. **`outline_mcp_server.py`** - The main server implementation
2. **`pyproject.toml`** - Package configuration
3. **`README.md`** - Documentation
4. **`__init__.py`** - Package initialization
5. **`.env.example`** - Environment template
6. **`LICENSE`** - MIT license
7. **`tests/test_server.py`** - Unit tests
8. **`.github/workflows/ci.yml`** - CI pipeline

### 5. Install Dependencies

```bash
# Install project dependencies
uv sync

# Install development dependencies
uv sync --dev
```

### 6. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your actual API token
nano .env  # or your preferred editor
```

Set your Outline API token:
```bash
OUTLINE_API_TOKEN=ol_api_your_actual_token_here
```

### 7. Get Your Outline API Token

1. Go to your Outline workspace
2. Navigate to **Settings → API & Apps**
3. Click "Create API Token"
4. Give it a descriptive name
5. Copy the token (starts with `ol_api_`)
6. Set the required scopes:
   - `documents.read`
   - `documents.search`
   - `collections.read`

### 8. Test the Server

```bash
# Test server startup
uv run outline_mcp_server.py

# Run in development mode with MCP Inspector
uv run mcp dev outline_mcp_server.py

# Run tests
uv run pytest

# Run linting
uv run black .
uv run ruff check .

# Type checking
uv run mypy .
```

### 9. Claude Desktop Integration

#### For macOS:
```bash
# Open Claude Desktop config
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

#### For Linux:
```bash
# Open Claude Desktop config
code ~/.config/Claude/claude_desktop_config.json
```

Add this configuration:
```json
{
  "mcpServers": {
    "outline": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/outline-mcp-server",
        "run",
        "outline_mcp_server.py"
      ],
      "env": {
        "OUTLINE_API_TOKEN": "your_actual_api_token_here"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/outline-mcp-server` with the actual absolute path to your project directory.

### 10. Restart Claude Desktop

Close and reopen Claude Desktop to load the new MCP server.

## Verification

### Test MCP Server Connection

In Claude Desktop, look for the hammer (🔨) icon in the interface. This indicates MCP tools are available.

### Test the Tools

Try these example queries in Claude Desktop:

1. **Search documents**:
   ```
   Search for documents about "hiring policy"
   ```

2. **List collections**:
   ```
   Show me all available collections
   ```

3. **Get a specific document**:
   ```
   Get the document with ID "your-document-id"
   ```

4. **Ask a question**:
   ```
   What is our remote work policy?
   ```

## Development Workflow

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=outline_mcp_server

# Run specific test
uv run pytest tests/test_server.py::TestOutlineConfig::test_outline_config_valid
```

### Code Formatting
```bash
# Format code
uv run black .

# Check formatting
uv run black --check .

# Lint code
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

### Type Checking
```bash
uv run mypy .
```

### Pre-commit Hooks (Optional)
```bash
# Install pre-commit
uv add --dev pre-commit

# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## Troubleshooting

### Common Issues

1. **"Module not found" error**:
   ```bash
   # Ensure you're in the project directory
   cd outline-mcp-server
   # Reinstall dependencies
   uv sync
   ```

2. **API authentication error**:
   - Verify your API token is correct
   - Check token permissions in Outline settings
   - Ensure token hasn't expired

3. **Claude Desktop not detecting server**:
   - Check the absolute path in `claude_desktop_config.json`
   - Verify the server runs successfully with `uv run outline_mcp_server.py`
   - Restart Claude Desktop completely

4. **Permission denied on UV**:
   ```bash
   # Make sure UV is in your PATH
   echo $PATH
   # Reinstall UV if needed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
uv run outline_mcp_server.py
```

### Manual Testing

Test individual functions:
```bash
# Test API connection
uv run python -c "
import asyncio
import os
from outline_mcp_server import OutlineConfig
config = OutlineConfig(api_token=os.getenv('OUTLINE_API_TOKEN'))
print('Config created successfully')
"
```

## Next Steps

1. **Customize the server** - Add more tools or modify existing ones
2. **Add resource support** - Implement MCP resources for document content
3. **Add prompt support** - Create reusable prompt templates
4. **Extend API coverage** - Add support for more Outline API endpoints
5. **Add caching** - Implement response caching for better performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run tests and linting
5. Submit a pull request

## Support

- Check the README.md for detailed documentation
- Run `uv run pytest -v` to see detailed test output
- Enable debug logging for troubleshooting
- Check GitHub issues for known problems

## Additional Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [Outline API Documentation](https://www.getoutline.com/developers)
- [UV Package Manager Documentation](https://docs.astral.sh/uv/)
