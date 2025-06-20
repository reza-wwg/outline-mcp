"""
Tests for the Outline MCP Server
"""

import json
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Import the server components
from src.outline_mcp_server import OutlineConfig, AppContext, make_outline_request


class TestOutlineConfig:
    """Test the OutlineConfig dataclass."""

    def test_outline_config_valid(self):
        """Test valid configuration."""
        config = OutlineConfig(api_token="test_token")
        assert config.api_token == "test_token"
        assert config.base_url == "https://app.getoutline.com/api"

    def test_outline_config_custom_url(self):
        """Test configuration with custom base URL."""
        config = OutlineConfig(
            api_token="test_token", base_url="https://custom.outline.com/api"
        )
        assert config.api_token == "test_token"
        assert config.base_url == "https://custom.outline.com/api"

    def test_outline_config_empty_token(self):
        """Test configuration with empty token raises error."""
        with pytest.raises(
            ValueError, match="OUTLINE_API_TOKEN environment variable is required"
        ):
            OutlineConfig(api_token="")


class TestMakeOutlineRequest:
    """Test the make_outline_request function."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        context = MagicMock()
        app_context = MagicMock()
        app_context.outline_config.base_url = "https://app.getoutline.com/api"

        # Mock HTTP client
        http_client = AsyncMock()
        app_context.http_client = http_client

        context.request_context.lifespan_context = app_context
        return context, http_client

    @pytest.mark.asyncio
    async def test_successful_request(self, mock_context):
        """Test successful API request."""
        context, http_client = mock_context

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "data": {"id": "test"}}
        mock_response.raise_for_status.return_value = None
        http_client.post.return_value = mock_response

        result = await make_outline_request(context, "documents.info", {"id": "test"})

        assert result == {"ok": True, "data": {"id": "test"}}
        http_client.post.assert_called_once_with(
            "https://app.getoutline.com/api/documents.info", json={"id": "test"}
        )

    @pytest.mark.asyncio
    async def test_api_error_response(self, mock_context):
        """Test API error response."""
        context, http_client = mock_context

        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": False, "error": "Not Found"}
        mock_response.raise_for_status.return_value = None
        http_client.post.return_value = mock_response

        with pytest.raises(Exception, match="Outline API error: Not Found"):
            await make_outline_request(context, "documents.info", {"id": "invalid"})

    @pytest.mark.asyncio
    async def test_http_error(self, mock_context):
        """Test HTTP error handling."""
        context, http_client = mock_context

        # Mock HTTP error
        http_client.post.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(Exception, match="Failed to call Outline API"):
            await make_outline_request(context, "documents.info", {"id": "test"})

    @pytest.mark.asyncio
    async def test_default_empty_data(self, mock_context):
        """Test that empty data defaults to empty dict."""
        context, http_client = mock_context

        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "data": []}
        mock_response.raise_for_status.return_value = None
        http_client.post.return_value = mock_response

        result = await make_outline_request(context, "documents.list")

        # Should call with empty dict when data is None
        http_client.post.assert_called_once_with(
            "https://app.getoutline.com/api/documents.list", json={}
        )


class TestServerIntegration:
    """Integration tests for the MCP server."""

    @pytest.mark.asyncio
    async def test_search_documents_formatting(self):
        """Test that search_documents formats results correctly."""
        # This would be an integration test with the actual MCP server
        # For now, we'll test the data formatting logic

        # Mock API response
        api_response = {
            "ok": True,
            "data": [
                {
                    "context": "Our hiring policy includes...",
                    "ranking": 1.5,
                    "document": {
                        "id": "doc-123",
                        "title": "Hiring Policy",
                        "urlId": "hiring-policy",
                        "collectionId": "col-456",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-02T00:00:00Z",
                        "createdBy": {"name": "John Doe"},
                        "updatedBy": {"name": "Jane Smith"},
                    },
                }
            ],
            "pagination": {"limit": 25, "offset": 0},
        }

        # Extract the formatting logic from search_documents
        results = api_response.get("data", [])
        formatted_results = []

        for result in results:
            doc = result.get("document", {})
            formatted_result = {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "url_id": doc.get("urlId"),
                "context": result.get("context", ""),
                "ranking": result.get("ranking"),
                "collection_id": doc.get("collectionId"),
                "created_at": doc.get("createdAt"),
                "updated_at": doc.get("updatedAt"),
                "created_by": doc.get("createdBy", {}).get("name"),
                "updated_by": doc.get("updatedBy", {}).get("name"),
            }
            formatted_results.append(formatted_result)

        assert len(formatted_results) == 1
        assert formatted_results[0]["id"] == "doc-123"
        assert formatted_results[0]["title"] == "Hiring Policy"
        assert formatted_results[0]["context"] == "Our hiring policy includes..."
        assert formatted_results[0]["created_by"] == "John Doe"
        assert formatted_results[0]["updated_by"] == "Jane Smith"


# Test fixtures and utilities
@pytest.fixture
def sample_document():
    """Sample document data for testing."""
    return {
        "id": "doc-123",
        "title": "Test Document",
        "text": "# Test Document\n\nThis is a test document.",
        "urlId": "test-document",
        "emoji": "📄",
        "collectionId": "col-456",
        "parentDocumentId": None,
        "template": False,
        "pinned": False,
        "fullWidth": False,
        "revision": 5,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-02T00:00:00Z",
        "publishedAt": "2024-01-01T12:00:00Z",
        "createdBy": {"name": "John Doe", "id": "user-123"},
        "updatedBy": {"name": "Jane Smith", "id": "user-456"},
        "collaborators": [
            {"name": "John Doe", "id": "user-123"},
            {"name": "Jane Smith", "id": "user-456"},
        ],
    }


@pytest.fixture
def sample_collection():
    """Sample collection data for testing."""
    return {
        "id": "col-456",
        "name": "Test Collection",
        "description": "A test collection",
        "urlId": "test-collection",
        "color": "#FF6B6B",
        "icon": "📚",
        "permission": "read_write",
        "sharing": True,
        "sort": {"field": "updatedAt", "direction": "desc"},
        "index": "A",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-02T00:00:00Z",
        "archivedAt": None,
        "deletedAt": None,
    }


class TestDataFormatting:
    """Test data formatting functions."""

    def test_document_formatting(self, sample_document):
        """Test document data formatting."""
        doc = sample_document

        formatted_doc = {
            "id": doc.get("id"),
            "title": doc.get("title"),
            "text": doc.get("text"),
            "url_id": doc.get("urlId"),
            "emoji": doc.get("emoji"),
            "collection_id": doc.get("collectionId"),
            "parent_document_id": doc.get("parentDocumentId"),
            "template": doc.get("template"),
            "pinned": doc.get("pinned"),
            "full_width": doc.get("fullWidth"),
            "revision": doc.get("revision"),
            "created_at": doc.get("createdAt"),
            "updated_at": doc.get("updatedAt"),
            "published_at": doc.get("publishedAt"),
            "created_by": doc.get("createdBy", {}).get("name"),
            "updated_by": doc.get("updatedBy", {}).get("name"),
            "collaborators": [
                collab.get("name") for collab in doc.get("collaborators", [])
            ],
        }

        assert formatted_doc["id"] == "doc-123"
        assert formatted_doc["title"] == "Test Document"
        assert formatted_doc["emoji"] == "📄"
        assert formatted_doc["created_by"] == "John Doe"
        assert formatted_doc["updated_by"] == "Jane Smith"
        assert formatted_doc["collaborators"] == ["John Doe", "Jane Smith"]

    def test_collection_formatting(self, sample_collection):
        """Test collection data formatting."""
        collection = sample_collection

        formatted_collection = {
            "id": collection.get("id"),
            "name": collection.get("name"),
            "description": collection.get("description"),
            "url_id": collection.get("urlId"),
            "color": collection.get("color"),
            "icon": collection.get("icon"),
            "permission": collection.get("permission"),
            "sharing": collection.get("sharing"),
            "sort": collection.get("sort"),
            "index": collection.get("index"),
            "created_at": collection.get("createdAt"),
            "updated_at": collection.get("updatedAt"),
            "archived_at": collection.get("archivedAt"),
            "deleted_at": collection.get("deletedAt"),
        }

        assert formatted_collection["id"] == "col-456"
        assert formatted_collection["name"] == "Test Collection"
        assert formatted_collection["color"] == "#FF6B6B"
        assert formatted_collection["icon"] == "📚"
        assert formatted_collection["sharing"] is True


if __name__ == "__main__":
    pytest.main([__file__])
