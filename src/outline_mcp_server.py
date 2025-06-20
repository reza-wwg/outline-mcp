#!/usr/bin/env python3
"""
Outline MCP Server

A Model Context Protocol server that provides access to Outline documents and collections.
This server focuses on reading operations like searching, listing, and retrieving documents.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

import httpx
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OutlineConfig:
    """Configuration for Outline API connection."""

    api_token: str
    base_url: str = "https://app.getoutline.com/api"

    def __post_init__(self):
        if not self.api_token:
            raise ValueError("OUTLINE_API_TOKEN environment variable is required")


@dataclass
class AppContext:
    """Application context containing shared resources."""

    outline_config: OutlineConfig
    http_client: httpx.AsyncClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with shared HTTP client and configuration."""
    # Get configuration from environment
    api_token = os.getenv("OUTLINE_API_TOKEN")
    if not api_token:
        raise ValueError("OUTLINE_API_TOKEN environment variable is required")

    base_url = os.getenv("OUTLINE_BASE_URL", "https://app.getoutline.com/api")

    outline_config = OutlineConfig(api_token=api_token, base_url=base_url)

    # Create shared HTTP client
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    timeout = httpx.Timeout(30.0, connect=10.0)

    async with httpx.AsyncClient(
        headers=headers, timeout=timeout, follow_redirects=True
    ) as http_client:
        logger.info("Outline MCP Server initialized")
        try:
            yield AppContext(outline_config=outline_config, http_client=http_client)
        finally:
            logger.info("Outline MCP Server shutting down")


# Initialize the MCP server
mcp = FastMCP("Outline", lifespan=app_lifespan)


async def make_outline_request(
    ctx: Context, endpoint: str, data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make a request to the Outline API.

    Args:
        ctx: MCP context containing the HTTP client
        endpoint: API endpoint (without base URL)
        data: Optional request data for POST requests

    Returns:
        JSON response from the API

    Raises:
        Exception: If the request fails
    """
    app_context = ctx.request_context.lifespan_context
    url = f"{app_context.outline_config.base_url}/{endpoint}"

    try:
        if data is None:
            data = {}

        response = await app_context.http_client.post(url, json=data)
        response.raise_for_status()

        json_response = response.json()

        if not json_response.get("ok", True):
            error_msg = json_response.get("error", "Unknown error")
            raise Exception(f"Outline API error: {error_msg}")

        return json_response

    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling {endpoint}: {e}")
        raise Exception(f"Failed to call Outline API: {e}")
    except Exception as e:
        logger.error(f"Error calling {endpoint}: {e}")
        raise


@mcp.tool()
async def search_documents(
    ctx: Context,
    query: str,
    collection_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    date_filter: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """
    Search for documents using keywords.

    Args:
        query: Search query string
        collection_id: Optional collection UUID to search within
        user_id: Optional user UUID - filter to documents edited by this user
        status_filter: Optional status filter (draft, archived, published)
        date_filter: Optional date filter (day, week, month, year)
        limit: Number of results to return (1-100, default 25)
        offset: Pagination offset (default 0)

    Returns:
        JSON string containing search results with document snippets and metadata
    """
    ctx.info(f"Searching documents for: {query}")

    request_data = {"query": query, "limit": min(max(limit, 1), 100), "offset": offset}

    if collection_id:
        request_data["collectionId"] = collection_id
    if user_id:
        request_data["userId"] = user_id
    if status_filter:
        request_data["statusFilter"] = status_filter
    if date_filter:
        request_data["dateFilter"] = date_filter

    response = await make_outline_request(ctx, "documents.search", request_data)

    # Format the response for better readability
    results = response.get("data", [])
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

    pagination = response.get("pagination", {})

    result_summary = {
        "query": query,
        "total_results": len(formatted_results),
        "results": formatted_results,
        "pagination": pagination,
    }

    import json

    return json.dumps(result_summary, indent=2)


@mcp.tool()
async def get_document(
    ctx: Context, document_id: str, share_id: Optional[str] = None
) -> str:
    """
    Retrieve a document by its ID.

    Args:
        document_id: Document UUID or urlId
        share_id: Optional share UUID if accessing via share link

    Returns:
        JSON string containing full document details including content
    """
    ctx.info(f"Retrieving document: {document_id}")

    request_data = {"id": document_id}
    if share_id:
        request_data["shareId"] = share_id

    response = await make_outline_request(ctx, "documents.info", request_data)

    doc = response.get("data", {})

    # Format the document data
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

    import json

    return json.dumps(formatted_doc, indent=2)


@mcp.tool()
async def list_documents(
    ctx: Context,
    collection_id: Optional[str] = None,
    user_id: Optional[str] = None,
    parent_document_id: Optional[str] = None,
    template: Optional[bool] = None,
    limit: int = 25,
    offset: int = 0,
    sort: str = "updatedAt",
    direction: str = "DESC",
) -> str:
    """
    List documents with various filters.

    Args:
        collection_id: Optional collection UUID to filter by
        user_id: Optional user UUID to filter by
        parent_document_id: Optional parent document UUID to filter by
        template: Optional filter for template documents
        limit: Number of results to return (1-100, default 25)
        offset: Pagination offset (default 0)
        sort: Sort field (default updatedAt)
        direction: Sort direction - ASC or DESC (default DESC)

    Returns:
        JSON string containing list of documents
    """
    ctx.info("Listing documents")

    request_data = {
        "limit": min(max(limit, 1), 100),
        "offset": offset,
        "sort": sort,
        "direction": direction,
    }

    if collection_id:
        request_data["collectionId"] = collection_id
    if user_id:
        request_data["userId"] = user_id
    if parent_document_id:
        request_data["parentDocumentId"] = parent_document_id
    if template is not None:
        request_data["template"] = template

    response = await make_outline_request(ctx, "documents.list", request_data)

    # Format the response
    documents = response.get("data", [])
    formatted_docs = []

    for doc in documents:
        formatted_doc = {
            "id": doc.get("id"),
            "title": doc.get("title"),
            "url_id": doc.get("urlId"),
            "emoji": doc.get("emoji"),
            "collection_id": doc.get("collectionId"),
            "parent_document_id": doc.get("parentDocumentId"),
            "template": doc.get("template"),
            "pinned": doc.get("pinned"),
            "revision": doc.get("revision"),
            "created_at": doc.get("createdAt"),
            "updated_at": doc.get("updatedAt"),
            "published_at": doc.get("publishedAt"),
            "created_by": doc.get("createdBy", {}).get("name"),
            "updated_by": doc.get("updatedBy", {}).get("name"),
        }
        formatted_docs.append(formatted_doc)

    pagination = response.get("pagination", {})

    result = {
        "total_documents": len(formatted_docs),
        "documents": formatted_docs,
        "pagination": pagination,
    }

    import json

    return json.dumps(result, indent=2)


@mcp.tool()
async def answer_question(
    ctx: Context,
    question: str,
    collection_id: Optional[str] = None,
    document_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    date_filter: Optional[str] = None,
) -> str:
    """
    Ask a natural language question about your documents using AI.
    Note: This requires "AI answers" to be enabled in your Outline workspace.

    Args:
        question: Natural language question to ask
        collection_id: Optional collection UUID to search within
        document_id: Optional document UUID to search within
        user_id: Optional user UUID to filter by
        status_filter: Optional status filter (draft, archived, published)
        date_filter: Optional date filter (day, week, month, year)

    Returns:
        JSON string containing the AI-generated answer and supporting documents
    """
    ctx.info(f"Answering question: {question}")

    request_data = {"query": question}

    if collection_id:
        request_data["collectionId"] = collection_id
    if document_id:
        request_data["documentId"] = document_id
    if user_id:
        request_data["userId"] = user_id
    if status_filter:
        request_data["statusFilter"] = status_filter
    if date_filter:
        request_data["dateFilter"] = date_filter

    response = await make_outline_request(ctx, "documents.answerQuestion", request_data)

    # Format the response
    search_result = response.get("search", {})
    documents = response.get("documents", [])

    formatted_docs = []
    for doc in documents:
        formatted_doc = {
            "id": doc.get("id"),
            "title": doc.get("title"),
            "url_id": doc.get("urlId"),
            "collection_id": doc.get("collectionId"),
            "created_at": doc.get("createdAt"),
            "updated_at": doc.get("updatedAt"),
        }
        formatted_docs.append(formatted_doc)

    result = {
        "question": question,
        "answer": search_result.get("answer"),
        "supporting_documents": formatted_docs,
        "search_metadata": {
            "id": search_result.get("id"),
            "query": search_result.get("query"),
            "source": search_result.get("source"),
            "created_at": search_result.get("createdAt"),
        },
    }

    import json

    return json.dumps(result, indent=2)


@mcp.tool()
async def export_document(ctx: Context, document_id: str) -> str:
    """
    Export a document as Markdown.

    Args:
        document_id: Document UUID or urlId to export

    Returns:
        The document content in Markdown format
    """
    ctx.info(f"Exporting document: {document_id}")

    request_data = {"id": document_id}
    response = await make_outline_request(ctx, "documents.export", request_data)

    return response.get("data", "")


@mcp.tool()
async def list_collections(
    ctx: Context,
    query: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
    sort: str = "updatedAt",
    direction: str = "DESC",
) -> str:
    """
    List all collections.

    Args:
        query: Optional search query to filter collections by name
        limit: Number of results to return (1-100, default 25)
        offset: Pagination offset (default 0)
        sort: Sort field (default updatedAt)
        direction: Sort direction - ASC or DESC (default DESC)

    Returns:
        JSON string containing list of collections
    """
    ctx.info("Listing collections")

    request_data = {
        "limit": min(max(limit, 1), 100),
        "offset": offset,
        "sort": sort,
        "direction": direction,
    }

    if query:
        request_data["query"] = query

    response = await make_outline_request(ctx, "collections.list", request_data)

    # Format the response
    collections = response.get("data", [])
    formatted_collections = []

    for collection in collections:
        formatted_collection = {
            "id": collection.get("id"),
            "name": collection.get("name"),
            "description": collection.get("description"),
            "url_id": collection.get("urlId"),
            "color": collection.get("color"),
            "icon": collection.get("icon"),
            "permission": collection.get("permission"),
            "sharing": collection.get("sharing"),
            "created_at": collection.get("createdAt"),
            "updated_at": collection.get("updatedAt"),
        }
        formatted_collections.append(formatted_collection)

    pagination = response.get("pagination", {})

    result = {
        "total_collections": len(formatted_collections),
        "collections": formatted_collections,
        "pagination": pagination,
    }

    import json

    return json.dumps(result, indent=2)


@mcp.tool()
async def get_collection(ctx: Context, collection_id: str) -> str:
    """
    Retrieve a collection by its ID.

    Args:
        collection_id: Collection UUID to retrieve

    Returns:
        JSON string containing collection details
    """
    ctx.info(f"Retrieving collection: {collection_id}")

    request_data = {"id": collection_id}
    response = await make_outline_request(ctx, "collections.info", request_data)

    collection = response.get("data", {})

    # Format the collection data
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

    import json

    return json.dumps(formatted_collection, indent=2)


@mcp.tool()
async def get_collection_documents(ctx: Context, collection_id: str) -> str:
    """
    Retrieve the document structure/navigation tree for a collection.

    Args:
        collection_id: Collection UUID to get documents for

    Returns:
        JSON string containing the hierarchical document structure
    """
    ctx.info(f"Retrieving document structure for collection: {collection_id}")

    request_data = {"id": collection_id}
    response = await make_outline_request(ctx, "collections.documents", request_data)

    documents = response.get("data", [])

    result = {"collection_id": collection_id, "document_tree": documents}

    import json

    return json.dumps(result, indent=2)


@mcp.tool()
async def list_draft_documents(
    ctx: Context,
    collection_id: Optional[str] = None,
    date_filter: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
    sort: str = "updatedAt",
    direction: str = "DESC",
) -> str:
    """
    List all draft documents belonging to the current user.

    Args:
        collection_id: Optional collection UUID to search within
        date_filter: Optional date filter (day, week, month, year)
        limit: Number of results to return (1-100, default 25)
        offset: Pagination offset (default 0)
        sort: Sort field (default updatedAt)
        direction: Sort direction - ASC or DESC (default DESC)

    Returns:
        JSON string containing list of draft documents
    """
    ctx.info("Listing draft documents")

    request_data = {
        "limit": min(max(limit, 1), 100),
        "offset": offset,
        "sort": sort,
        "direction": direction,
    }

    if collection_id:
        request_data["collectionId"] = collection_id
    if date_filter:
        request_data["dateFilter"] = date_filter

    response = await make_outline_request(ctx, "documents.drafts", request_data)

    # Format the response
    documents = response.get("data", [])
    formatted_docs = []

    for doc in documents:
        formatted_doc = {
            "id": doc.get("id"),
            "title": doc.get("title"),
            "url_id": doc.get("urlId"),
            "emoji": doc.get("emoji"),
            "collection_id": doc.get("collectionId"),
            "parent_document_id": doc.get("parentDocumentId"),
            "template": doc.get("template"),
            "revision": doc.get("revision"),
            "created_at": doc.get("createdAt"),
            "updated_at": doc.get("updatedAt"),
            "created_by": doc.get("createdBy", {}).get("name"),
            "updated_by": doc.get("updatedBy", {}).get("name"),
        }
        formatted_docs.append(formatted_doc)

    pagination = response.get("pagination", {})

    result = {
        "total_drafts": len(formatted_docs),
        "draft_documents": formatted_docs,
        "pagination": pagination,
    }

    import json

    return json.dumps(result, indent=2)


@mcp.tool()
async def list_recently_viewed_documents(
    ctx: Context,
    limit: int = 25,
    offset: int = 0,
    sort: str = "updatedAt",
    direction: str = "DESC",
) -> str:
    """
    List all documents recently viewed by the current user.

    Args:
        limit: Number of results to return (1-100, default 25)
        offset: Pagination offset (default 0)
        sort: Sort field (default updatedAt)
        direction: Sort direction - ASC or DESC (default DESC)

    Returns:
        JSON string containing list of recently viewed documents
    """
    ctx.info("Listing recently viewed documents")

    request_data = {
        "limit": min(max(limit, 1), 100),
        "offset": offset,
        "sort": sort,
        "direction": direction,
    }

    response = await make_outline_request(ctx, "documents.viewed", request_data)

    # Format the response
    documents = response.get("data", [])
    formatted_docs = []

    for doc in documents:
        formatted_doc = {
            "id": doc.get("id"),
            "title": doc.get("title"),
            "url_id": doc.get("urlId"),
            "emoji": doc.get("emoji"),
            "collection_id": doc.get("collectionId"),
            "parent_document_id": doc.get("parentDocumentId"),
            "template": doc.get("template"),
            "revision": doc.get("revision"),
            "created_at": doc.get("createdAt"),
            "updated_at": doc.get("updatedAt"),
            "published_at": doc.get("publishedAt"),
            "created_by": doc.get("createdBy", {}).get("name"),
            "updated_by": doc.get("updatedBy", {}).get("name"),
        }
        formatted_docs.append(formatted_doc)

    pagination = response.get("pagination", {})

    result = {
        "total_viewed": len(formatted_docs),
        "recently_viewed_documents": formatted_docs,
        "pagination": pagination,
    }

    import json

    return json.dumps(result, indent=2)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
