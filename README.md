# Outline MCP Server

A Model Context Protocol (MCP) server that provides access to [Outline](https://www.getoutline.com/) documents and collections. This server focuses on reading operations, allowing you to search, list, and retrieve documents from your Outline knowledge base.

## Features

### Document Operations
- **Search Documents**: Search through your documents using keywords with various filters
- **Get Document**: Retrieve full document content by ID
- **List Documents**: List documents with filtering options (by collection, user, etc.)
- **Answer Questions**: Use AI to answer natural language questions about your documents
- **Export Documents**: Export documents as Markdown
- **List Drafts**: View your draft documents
- **Recently Viewed**: See recently viewed documents

### Collection Operations
- **List Collections**: Browse all available collections
- **Get Collection**: Retrieve collection details
- **Collection Structure**: Get the hierarchical document structure within collections

## Installation

### Prerequisites

- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/) package manager
- An Outline API token

### Setup

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup the project**:
   ```bash
   git clone <repository-url>
   cd outline-mcp-server
   uv sync
   ```

3. **Get your Outline API token**:
   - Go to your Outline workspace
   - Navigate to **Settings → API & Apps**
   - Create a new API token
   - Copy the token (it starts with `ol_api_`)

4. **Set environment variables**:
   ```bash
   export OUTLINE_API_TOKEN="your_api_token_here"
   # Optional: if you're using a self-hosted instance
   export OUTLINE_BASE_URL="https://your-outline-instance.com/api"
   ```

## Usage

### Running the Server

#### Development Mode
Test your server with the MCP Inspector:
```bash
uv run mcp dev outline_mcp_server.py
```

#### Direct Execution
```bash
uv run outline_mcp_server.py
```

### Claude Desktop Integration

To use this server with Claude Desktop, add it to your Claude Desktop configuration:

1. **Open Claude Desktop configuration**:
   ```bash
   # macOS
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # Linux
   code ~/.config/Claude/claude_desktop_config.json
   ```

2. **Add the server configuration**:
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
           "OUTLINE_API_TOKEN": "your_api_token_here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Available Tools

### 🔍 search_documents
Search for documents using keywords.

**Parameters:**
- `query` (required): Search query string
- `collection_id` (optional): UUID of collection to search within
- `user_id` (optional): Filter by documents edited by specific user
- `status_filter` (optional): Filter by status (draft, archived, published)
- `date_filter` (optional): Filter by date (day, week, month, year)
- `limit` (optional): Number of results (1-100, default 25)
- `offset` (optional): Pagination offset (default 0)

**Example:**
```
Search for documents containing "hiring policy" in the HR collection
```

### 📄 get_document
Retrieve a document by its ID.

**Parameters:**
- `document_id` (required): Document UUID or urlId
- `share_id` (optional): Share UUID if accessing via share link

**Example:**
```
Get the document with ID "hDYep1TPAM"
```

### 📋 list_documents
List documents with various filters.

**Parameters:**
- `collection_id` (optional): Filter by collection UUID
- `user_id` (optional): Filter by user UUID
- `parent_document_id` (optional): Filter by parent document UUID
- `template` (optional): Filter template documents (true/false)
- `limit` (optional): Number of results (1-100, default 25)
- `offset` (optional): Pagination offset (default 0)
- `sort` (optional): Sort field (default updatedAt)
- `direction` (optional): Sort direction - ASC or DESC (default DESC)

### 🤖 answer_question
Ask natural language questions about your documents using AI.

**Parameters:**
- `question` (required): Natural language question
- `collection_id` (optional): Search within specific collection
- `document_id` (optional): Search within specific document
- `user_id` (optional): Filter by user
- `status_filter` (optional): Filter by document status
- `date_filter` (optional): Filter by date range

**Example:**
```
What is our remote work policy?
```

### 📥 export_document
Export a document as Markdown.

**Parameters:**
- `document_id` (required): Document UUID or urlId to export

### 📁 list_collections
List all available collections.

**Parameters:**
- `query` (optional): Search collections by name
- `limit` (optional): Number of results (1-100, default 25)
- `offset` (optional): Pagination offset (default 0)
- `sort` (optional): Sort field (default updatedAt)
- `direction` (optional): Sort direction (ASC or DESC)

### 📁 get_collection
Retrieve collection details by ID.

**Parameters:**
- `collection_id` (required): Collection UUID

### 🗂️ get_collection_documents
Get the hierarchical document structure for a collection.

**Parameters:**
- `collection_id` (required): Collection UUID

### 📝 list_draft_documents
List draft documents belonging to the current user.

**Parameters:**
- `collection_id` (optional): Filter by collection
- `date_filter` (optional): Filter by date (day, week, month, year)
- `limit` (optional): Number of results (default 25)
- `offset` (optional): Pagination offset

### 👁️ list_recently_viewed_documents
List recently viewed documents.

**Parameters:**
- `limit` (optional): Number of results (default 25)
- `offset` (optional): Pagination offset
- `sort` (optional): Sort field (default updatedAt)
- `direction` (optional): Sort direction

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OUTLINE_API_TOKEN` | Yes | - | Your Outline API token |
| `OUTLINE_BASE_URL` | No | `https://app.getoutline.com/api` | Base URL for Outline API |

### API Token Scopes

The API token should have the following scopes:
- `documents.read` - To read document content
- `documents.search` - To search documents
- `collections.read` - To access collection information

## Development

### Setting Up Development Environment

1. **Install dependencies**:
   ```bash
   uv sync --dev
   ```

2. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

3. **Run tests**:
   ```bash
   uv run pytest
   ```

4. **Format code**:
   ```bash
   uv run black .
   uv run ruff check --fix .
   ```

5. **Type checking**:
   ```bash
   uv run mypy .
   ```

### Project Structure

```
outline-mcp-server/
├── outline_mcp_server.py      # Main server implementation
├── pyproject.toml             # Project configuration
├── README.md                  # This file
├── LICENSE                    # MIT License
├── .env.example              # Environment variables example
├── tests/                    # Test files
│   ├── __init__.py
│   ├── test_server.py
│   └── test_outline_api.py
└── .github/                  # GitHub workflows
    └── workflows/
        └── ci.yml
```

## Troubleshooting

### Common Issues

1. **Authentication Error**:
   - Verify your API token is correct
   - Check that the token has the necessary scopes
   - Ensure the token is not expired

2. **Connection Issues**:
   - Verify the base URL is correct for your Outline instance
   - Check network connectivity
   - Ensure firewall settings allow outbound HTTPS connections

3. **Permission Errors**:
   - Verify your user has access to the documents/collections you're trying to access
   - Check that the API token has the required permissions

### Debugging

Enable debug logging by setting the log level:
```bash
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
uv run outline_mcp_server.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Format your code (`uv run black . && uv run ruff check --fix .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Python SDK for MCP
- [Outline](https://www.getoutline.com/) - The knowledge base this server connects to
- [Claude Desktop](https://claude.ai/download) - AI assistant that supports MCP

## Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Search existing [GitHub issues](https://github.com/yourusername/outline-mcp-server/issues)
3. Create a new issue with detailed information about the problem

## Changelog

### v0.1.0 (Initial Release)
- Document search functionality
- Document retrieval by ID
- Document listing with filters
- AI-powered question answering
- Collection management
- Draft document listing
- Recently viewed documents
- Document export as Markdown
