"""Tests for the Capsule CRM MCP server."""

from typing import Dict
import json
import pytest
from fastapi.testclient import TestClient

from capsule_mcp.server import create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a fresh FastAPI test client for each test."""
    test_app = create_app()
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def mock_capsule_response(monkeypatch):
    """Mock the Capsule API response."""

    async def mock_request(*args, **kwargs):
        return {"parties": [{"id": 1, "firstName": "Test", "lastName": "User"}]}

    monkeypatch.setattr("capsule_mcp.server.capsule_request", mock_request)


@pytest.fixture
def headers() -> Dict[str, str]:
    """Return standard headers for requests."""
    return {
        "Accept": "application/json, text/event-stream",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_mcp_schema(client, headers):
    """Test listing tools via the MCP endpoint."""
    response = client.post(
        "/mcp/",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        headers=headers,
    )
    assert response.status_code == 200

    tools = response.json()["result"]["tools"]
    assert len(tools) > 0

    tool_names = {tool["name"] for tool in tools}
    expected_tools = {
        "list_contacts",
        "search_contacts",
        "list_recent_contacts",
        "get_contact",
        "list_opportunities",
        "list_open_opportunities",
        "get_opportunity",
        "list_cases",
        "search_cases",
        "get_case",
        "list_tasks",
        "get_task",
        "list_entries",
        "get_entry",
        "list_projects",
        "get_project",
        "list_tags",
        "get_tag",
        "list_users",
        "get_user",
        "list_pipelines",
        "list_stages",
        "list_milestones",
        "list_custom_fields",
        "list_products",
        "list_categories",
        "list_currencies",
    }
    assert expected_tools.issubset(tool_names)


def test_list_contacts(client, mock_capsule_response, headers):
    """Test the list_contacts tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_contacts",
                "arguments": {"page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200

    payload = response.json()["result"]["content"][0]["text"]
    data = json.loads(payload)
    assert "parties" in data
    assert len(data["parties"]) > 0
    assert data["parties"][0]["firstName"] == "Test"


def test_search_contacts(client, mock_capsule_response, headers):
    """Test the search_contacts tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_contacts",
                "arguments": {"keyword": "test", "page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200

    payload = response.json()["result"]["content"][0]["text"]
    data = json.loads(payload)
    assert "parties" in data
    assert len(data["parties"]) > 0


def test_list_open_opportunities(client, mock_capsule_response, headers):
    """Test the list_open_opportunities tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_open_opportunities",
                "arguments": {"page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


def test_invalid_tool(client, headers):
    """Invalid tool names should return an error result."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "invalid_tool", "arguments": {}},
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["result"]["isError"] is True


def test_missing_required_args(client, headers):
    """Missing arguments should produce an error result."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "search_contacts", "arguments": {}},
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["result"]["isError"] is True


def test_print_routes(client):
    """Ensure that the MCP endpoint is registered."""
    routes = [route.path for route in client.app.routes if hasattr(route, "path")]
    assert "/mcp" in routes


def test_debug_post_to_mcp(client, headers):
    """Verify the MCP schema can be retrieved."""
    response = client.post(
        "/mcp/",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data and "tools" in data["result"]


def test_mcp_redirect(client, headers):
    """Requests to /mcp should redirect to /mcp/."""
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        follow_redirects=True,
        headers=headers,
    )
    assert response.status_code == 200


# New tool tests
def test_list_recent_contacts(client, mock_capsule_response, headers):
    """Test the list_recent_contacts tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_recent_contacts",
                "arguments": {"page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


def test_list_opportunities(client, mock_capsule_response, headers):
    """Test the list_opportunities tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_opportunities",
                "arguments": {"page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


def test_list_cases(client, mock_capsule_response, headers):
    """Test the list_cases tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_cases",
                "arguments": {"page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


def test_list_tasks(client, mock_capsule_response, headers):
    """Test the list_tasks tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_tasks",
                "arguments": {"page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


def test_list_entries(client, mock_capsule_response, headers):
    """Test the list_entries tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_entries",
                "arguments": {"page": 1, "per_page": 10},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


def test_get_contact(client, mock_capsule_response, headers):
    """Test the get_contact tool."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_contact",
                "arguments": {"contact_id": 1},
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


def test_list_configuration_tools(client, mock_capsule_response, headers):
    """Test configuration tools that don't require parameters."""
    tools = [
        "list_pipelines",
        "list_stages",
        "list_milestones",
        "list_custom_fields",
        "list_currencies",
    ]

    for tool_name in tools:
        response = client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {},
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200, f"Tool {tool_name} failed"


def test_since_parameter(client, mock_capsule_response, headers):
    """Test tools that support the 'since' parameter."""
    response = client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_contacts",
                "arguments": {
                    "page": 1,
                    "per_page": 10,
                    "since": "2024-01-01T00:00:00Z",
                },
            },
            "id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Write Operation Tests
# ---------------------------------------------------------------------------


def test_create_party_not_available_when_writes_disabled(client, headers):
    """Test that create_party tool is not available when writes are disabled."""
    import os
    # Ensure writes are disabled (default)
    os.environ.pop("ENABLE_CAPSULECRM_WRITES", None)
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers=headers,
        )
        assert response.status_code == 200
        
        tools = response.json()["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        assert "create_party" not in tool_names


def test_create_party_available_when_writes_enabled(client, headers, monkeypatch):
    """Test that create_party tool is available when writes are enabled."""
    import os
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Re-import and create the app
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers=headers,
        )
        assert response.status_code == 200
        
        tools = response.json()["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        assert "create_party" in tool_names
        assert "update_party" in tool_names
        assert "create_tag" in tool_names


def test_create_party_person(client, headers, monkeypatch):
    """Test creating a person party."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the Capsule API response for party creation
    async def mock_create_party(*args, **kwargs):
        # Verify the request body structure
        assert "json" in kwargs
        assert "party" in kwargs["json"]
        party = kwargs["json"]["party"]
        assert party["type"] == "person"
        assert party["firstName"] == "John"
        assert party["lastName"] == "Doe"
        
        # Return mock created party
        return {
            "party": {
                "id": 12345,
                "type": "person",
                "firstName": "John",
                "lastName": "Doe",
                "emailAddresses": [{"type": "Work", "address": "john@example.com"}],
                "createdAt": "2024-01-01T00:00:00Z",
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_create_party)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_party",
                    "arguments": {
                        "type": "person",
                        "firstName": "John",
                        "lastName": "Doe",
                        "emailAddress": "john@example.com",
                        "jobTitle": "Software Engineer",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "party" in data
        assert data["party"]["id"] == 12345
        assert data["party"]["firstName"] == "John"


def test_create_party_organisation(client, headers, monkeypatch):
    """Test creating an organisation party."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the Capsule API response for party creation
    async def mock_create_org(*args, **kwargs):
        # Verify the request body structure
        assert "json" in kwargs
        assert "party" in kwargs["json"]
        party = kwargs["json"]["party"]
        assert party["type"] == "organisation"
        assert party["name"] == "Acme Corp"
        
        # Return mock created party
        return {
            "party": {
                "id": 67890,
                "type": "organisation",
                "name": "Acme Corp",
                "websites": [{"type": "Work", "service": "URL", "address": "https://acme.com"}],
                "createdAt": "2024-01-01T00:00:00Z",
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_create_org)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_party",
                    "arguments": {
                        "type": "organisation",
                        "name": "Acme Corp",
                        "website": "https://acme.com",
                        "about": "Leading provider of widgets",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "party" in data
        assert data["party"]["id"] == 67890
        assert data["party"]["name"] == "Acme Corp"


def test_update_party(client, headers, monkeypatch):
    """Test updating a party."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the Capsule API response for party update
    async def mock_update_party(*args, **kwargs):
        # Verify the request
        assert args[0] == "PUT"
        assert "parties/12345" in args[1]
        assert "json" in kwargs
        assert "party" in kwargs["json"]
        party = kwargs["json"]["party"]
        
        # Return mock updated party
        return {
            "party": {
                "id": 12345,
                "type": "person",
                "firstName": party.get("firstName", "John"),
                "lastName": party.get("lastName", "Doe"),
                "jobTitle": party.get("jobTitle", "Updated Title"),
                "emailAddresses": party.get("emailAddresses", []),
                "updatedAt": "2024-01-02T00:00:00Z",
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_update_party)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_party",
                    "arguments": {
                        "party_id": 12345,
                        "jobTitle": "Updated Title",
                        "emailAddress": "john.updated@example.com",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "party" in data
        assert data["party"]["id"] == 12345
        assert data["party"]["jobTitle"] == "Updated Title"


def test_update_party_validates_required_id(client, headers, monkeypatch):
    """Test that update_party requires party_id."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_party",
                    "arguments": {
                        "firstName": "Test",  # No party_id provided
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        # Should have an error due to missing party_id
        assert result.get("result", {}).get("isError") is True or "error" in result


def test_create_tag_for_parties(client, headers, monkeypatch):
    """Test creating a tag for parties."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the Capsule API response for tag creation
    async def mock_create_tag(*args, **kwargs):
        # Verify the request body structure
        assert "json" in kwargs
        assert "tag" in kwargs["json"]
        tag = kwargs["json"]["tag"]
        assert tag["name"] == "Important Customer"
        assert tag["dataTag"] is False
        
        # Return mock created tag
        return {
            "tag": {
                "id": 12345,
                "name": "Important Customer",
                "description": "High value customers",
                "dataTag": False
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_create_tag)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_tag",
                    "arguments": {
                        "entity": "parties",
                        "name": "Important Customer",
                        "description": "High value customers",
                        "dataTag": False,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "tag" in data
        assert data["tag"]["id"] == 12345
        assert data["tag"]["name"] == "Important Customer"


def test_create_tag_validates_entity(client, headers, monkeypatch):
    """Test that create_tag validates entity type."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_tag",
                    "arguments": {
                        "entity": "invalid_entity",
                        "name": "Test Tag",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        # Check for error in response - MCP returns isError: true for validation errors
        assert result.get("result", {}).get("isError") is True
        error_text = result["result"]["content"][0]["text"]
        assert "invalid_entity" in error_text
