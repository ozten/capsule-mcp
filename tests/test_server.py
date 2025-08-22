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
        assert "create_note" in tool_names
        assert "update_note" in tool_names


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


def test_create_note_for_party(client, headers, monkeypatch):
    """Test creating a note for a party."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the Capsule API response for note creation
    async def mock_create_note(*args, **kwargs):
        # Verify the request
        assert args[0] == "POST"
        assert "entries" in args[1]
        assert "json" in kwargs
        assert "entry" in kwargs["json"]
        entry = kwargs["json"]["entry"]
        assert entry["type"] == "note"
        assert entry["content"] == "Important meeting notes"
        assert entry["party"]["id"] == 12345
        
        # Return mock created note
        return {
            "entry": {
                "id": 99999,
                "type": "note",
                "content": "Important meeting notes",
                "party": {"id": 12345, "name": "John Doe"},
                "createdAt": "2024-01-01T10:00:00Z"
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_create_note)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_note",
                    "arguments": {
                        "content": "Important meeting notes",
                        "party_id": 12345,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "entry" in data
        assert data["entry"]["id"] == 99999
        assert data["entry"]["content"] == "Important meeting notes"


def test_create_note_validates_single_entity(client, headers, monkeypatch):
    """Test that create_note requires exactly one entity."""
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
        # Test with no entity provided
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_note",
                    "arguments": {
                        "content": "Test note",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result.get("result", {}).get("isError") is True
        
        # Test with multiple entities provided
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_note",
                    "arguments": {
                        "content": "Test note",
                        "party_id": 123,
                        "opportunity_id": 456,
                    },
                },
                "id": 2,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result.get("result", {}).get("isError") is True


def test_update_note(client, headers, monkeypatch):
    """Test updating a note."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the Capsule API response for note update
    async def mock_update_note(*args, **kwargs):
        # Verify the request
        assert args[0] == "PUT"
        assert "entries/99999" in args[1]
        assert "json" in kwargs
        assert "entry" in kwargs["json"]
        entry = kwargs["json"]["entry"]
        assert entry["content"] == "Updated meeting notes with action items"
        
        # Return mock updated note
        return {
            "entry": {
                "id": 99999,
                "type": "note",
                "content": "Updated meeting notes with action items",
                "party": {"id": 12345, "name": "John Doe"},
                "updatedAt": "2024-01-02T10:00:00Z"
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_update_note)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_note",
                    "arguments": {
                        "note_id": 99999,
                        "content": "Updated meeting notes with action items",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "entry" in data
        assert data["entry"]["id"] == 99999
        assert data["entry"]["content"] == "Updated meeting notes with action items"


def test_add_tag_to_entity(client, headers, monkeypatch):
    """Test adding a tag to an entity."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_add_tag(method, endpoint, **kwargs):
        assert method == "POST"
        assert endpoint == "parties/12345/tags"
        assert "json" in kwargs
        assert "tag" in kwargs["json"]
        assert kwargs["json"]["tag"]["id"] == 100
        
        # Return mock success response
        return {"message": "Tag added successfully"}
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_add_tag)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "add_tag_to_entity",
                    "arguments": {
                        "entity": "parties",
                        "entity_id": 12345,
                        "tag_id": 100,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data["message"] == "Tag added successfully"


def test_remove_tag_from_entity(client, headers, monkeypatch):
    """Test removing a tag from an entity."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_remove_tag(method, endpoint, **kwargs):
        assert method == "DELETE"
        assert endpoint == "opportunities/5678/tags/200"
        
        # Return mock success response (typically empty for DELETE)
        return {}
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_remove_tag)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remove_tag_from_entity",
                    "arguments": {
                        "entity": "opportunities",
                        "entity_id": 5678,
                        "tag_id": 200,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data == {}


def test_bulk_tag_entities(client, headers, monkeypatch):
    """Test bulk tagging entities."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Track calls
    call_count = 0
    
    # Mock the capsule_request function
    async def mock_bulk_tag(method, endpoint, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # Should make 2 entities × 2 tags = 4 calls
        assert method == "POST"
        assert endpoint in ["kases/111/tags", "kases/222/tags"]
        assert "json" in kwargs
        assert "tag" in kwargs["json"]
        assert kwargs["json"]["tag"]["id"] in [10, 20]
        
        # Return mock success response
        return {"message": "Tag added"}
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_bulk_tag)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "bulk_tag_entities",
                    "arguments": {
                        "entity": "kases",
                        "entity_ids": [111, 222],
                        "tag_ids": [10, 20],
                        "operation": "add",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data["operation"] == "add"
        assert data["entity_type"] == "kases"
        assert data["total_operations"] == 4
        assert data["success_count"] == 4
        assert data["failure_count"] == 0
        assert len(data["successful"]) == 4


def test_bulk_tag_entities_remove(client, headers, monkeypatch):
    """Test bulk removing tags from entities."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Track calls
    call_count = 0
    
    # Mock the capsule_request function
    async def mock_bulk_untag(method, endpoint, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # Should make 1 entity × 3 tags = 3 calls
        assert method == "DELETE"
        assert endpoint in ["parties/333/tags/30", "parties/333/tags/31", "parties/333/tags/32"]
        
        # Simulate one failure
        if call_count == 2:
            raise Exception("Tag not found")
        
        return {}
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_bulk_untag)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "bulk_tag_entities",
                    "arguments": {
                        "entity": "parties",
                        "entity_ids": [333],
                        "tag_ids": [30, 31, 32],
                        "operation": "remove",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data["operation"] == "remove"
        assert data["entity_type"] == "parties"
        assert data["total_operations"] == 3
        assert data["success_count"] == 2
        assert data["failure_count"] == 1
        assert len(data["successful"]) == 2
        assert len(data["failed"]) == 1
        assert data["failed"][0]["error"] == "Tag not found"


def test_create_opportunity(client, headers, monkeypatch):
    """Test creating an opportunity."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_create_opportunity(method, endpoint, **kwargs):
        assert method == "POST"
        assert endpoint == "opportunities"
        assert "json" in kwargs
        assert "opportunity" in kwargs["json"]
        opp = kwargs["json"]["opportunity"]
        assert opp["name"] == "New Enterprise Deal"
        assert opp["party"]["id"] == 12345
        assert opp["milestone"]["id"] == 100
        assert opp["owner"]["id"] == 5
        assert opp["value"]["amount"] == 50000
        assert opp["value"]["currency"] == "USD"
        assert opp["probability"] == 75
        
        # Return mock created opportunity
        return {
            "opportunity": {
                "id": 99999,
                "name": "New Enterprise Deal",
                "party": {"id": 12345, "name": "Acme Corp"},
                "milestone": {"id": 100, "name": "Qualified"},
                "owner": {"id": 5, "name": "John Seller"},
                "value": {"amount": 50000, "currency": "USD"},
                "probability": 75,
                "expectedCloseOn": "2024-12-31",
                "createdAt": "2024-01-01T10:00:00Z"
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_create_opportunity)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_opportunity",
                    "arguments": {
                        "name": "New Enterprise Deal",
                        "party_id": 12345,
                        "milestone_id": 100,
                        "owner_id": 5,
                        "value": 50000,
                        "currency": "USD",
                        "expected_close_on": "2024-12-31",
                        "probability": 75,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "opportunity" in data
        assert data["opportunity"]["id"] == 99999
        assert data["opportunity"]["name"] == "New Enterprise Deal"
        assert data["opportunity"]["value"]["amount"] == 50000


def test_create_opportunity_validates_owner_or_team(client, headers, monkeypatch):
    """Test that create_opportunity requires either owner_id or team_id."""
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
        # Test with neither owner_id nor team_id
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_opportunity",
                    "arguments": {
                        "name": "Test Opportunity",
                        "party_id": 12345,
                        "milestone_id": 100,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result.get("result", {}).get("isError") is True
        error_text = result["result"]["content"][0]["text"]
        assert "Either owner_id or team_id must be provided" in error_text


def test_update_opportunity(client, headers, monkeypatch):
    """Test updating an opportunity."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_update_opportunity(method, endpoint, **kwargs):
        assert method == "PUT"
        assert endpoint == "opportunities/99999"
        assert "json" in kwargs
        assert "opportunity" in kwargs["json"]
        opp = kwargs["json"]["opportunity"]
        assert opp["name"] == "Updated Enterprise Deal"
        assert opp["probability"] == 90
        assert opp["value"]["amount"] == 75000
        assert "milestone" in opp
        assert opp["milestone"]["id"] == 200
        
        # Return mock updated opportunity
        return {
            "opportunity": {
                "id": 99999,
                "name": "Updated Enterprise Deal",
                "party": {"id": 12345, "name": "Acme Corp"},
                "milestone": {"id": 200, "name": "Negotiation"},
                "owner": {"id": 5, "name": "John Seller"},
                "value": {"amount": 75000, "currency": "USD"},
                "probability": 90,
                "expectedCloseOn": "2024-11-30",
                "updatedAt": "2024-01-02T10:00:00Z"
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_update_opportunity)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_opportunity",
                    "arguments": {
                        "opportunity_id": 99999,
                        "name": "Updated Enterprise Deal",
                        "milestone_id": 200,
                        "value": 75000,
                        "probability": 90,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "opportunity" in data
        assert data["opportunity"]["id"] == 99999
        assert data["opportunity"]["name"] == "Updated Enterprise Deal"
        assert data["opportunity"]["probability"] == 90
        assert data["opportunity"]["value"]["amount"] == 75000


def test_update_opportunity_validates_required_fields(client, headers, monkeypatch):
    """Test that update_opportunity requires at least one field."""
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
        # Test with no fields to update
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_opportunity",
                    "arguments": {
                        "opportunity_id": 99999,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result.get("result", {}).get("isError") is True
        error_text = result["result"]["content"][0]["text"]
        assert "At least one field must be provided to update" in error_text


def test_add_party_to_opportunity(client, headers, monkeypatch):
    """Test adding a party to an opportunity."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_add_party(method, endpoint, **kwargs):
        assert method == "POST"
        assert endpoint == "opportunities/12345/parties"
        assert "json" in kwargs
        assert "party" in kwargs["json"]
        assert kwargs["json"]["party"]["id"] == 67890
        
        # Return mock success response
        return {"message": "Party added to opportunity successfully"}
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_add_party)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "add_party_to_opportunity",
                    "arguments": {
                        "opportunity_id": 12345,
                        "party_id": 67890,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data["message"] == "Party added to opportunity successfully"


def test_remove_party_from_opportunity(client, headers, monkeypatch):
    """Test removing a party from an opportunity."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_remove_party(method, endpoint, **kwargs):
        assert method == "DELETE"
        assert endpoint == "opportunities/12345/parties/67890"
        
        # Return mock success response (typically empty for DELETE)
        return {}
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_remove_party)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "remove_party_from_opportunity",
                    "arguments": {
                        "opportunity_id": 12345,
                        "party_id": 67890,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data == {}


def test_create_task(client, headers, monkeypatch):
    """Test creating a task."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_create_task(method, endpoint, **kwargs):
        assert method == "POST"
        assert endpoint == "tasks"
        assert "json" in kwargs
        assert "task" in kwargs["json"]
        task = kwargs["json"]["task"]
        assert task["description"] == "Follow up with client"
        assert task["dueOn"] == "2024-12-31"
        assert task["dueTime"] == "14:30"
        assert task["owner"]["id"] == 5
        assert task["party"]["id"] == 12345
        assert task["status"] == "OPEN"
        
        # Return mock created task
        return {
            "task": {
                "id": 99999,
                "description": "Follow up with client",
                "dueOn": "2024-12-31",
                "dueTime": "14:30",
                "status": "OPEN",
                "owner": {"id": 5, "name": "John Doe"},
                "party": {"id": 12345, "name": "Acme Corp"},
                "createdAt": "2024-01-01T10:00:00Z"
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_create_task)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "description": "Follow up with client",
                        "due_on": "2024-12-31",
                        "due_time": "14:30",
                        "owner_id": 5,
                        "party_id": 12345,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "task" in data
        assert data["task"]["id"] == 99999
        assert data["task"]["description"] == "Follow up with client"


def test_create_task_validates_single_entity(client, headers, monkeypatch):
    """Test that create_task only allows one entity association."""
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
        # Test with multiple entity associations
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "description": "Test task",
                        "due_on": "2024-12-31",
                        "party_id": 123,
                        "opportunity_id": 456,  # Can't have both
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result.get("result", {}).get("isError") is True
        error_text = result["result"]["content"][0]["text"]
        assert "Only one of party_id, opportunity_id, or case_id can be set" in error_text


def test_update_task(client, headers, monkeypatch):
    """Test updating a task."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_update_task(method, endpoint, **kwargs):
        assert method == "PUT"
        assert endpoint == "tasks/99999"
        assert "json" in kwargs
        assert "task" in kwargs["json"]
        task = kwargs["json"]["task"]
        assert task["description"] == "Updated follow up"
        assert task["status"] == "PENDING"
        assert task["dueOn"] == "2025-01-15"
        
        # Return mock updated task
        return {
            "task": {
                "id": 99999,
                "description": "Updated follow up",
                "dueOn": "2025-01-15",
                "status": "PENDING",
                "owner": {"id": 5, "name": "John Doe"},
                "updatedAt": "2024-01-02T10:00:00Z"
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_update_task)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_task",
                    "arguments": {
                        "task_id": 99999,
                        "description": "Updated follow up",
                        "due_on": "2025-01-15",
                        "status": "PENDING",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "task" in data
        assert data["task"]["id"] == 99999
        assert data["task"]["description"] == "Updated follow up"
        assert data["task"]["status"] == "PENDING"


def test_complete_task(client, headers, monkeypatch):
    """Test completing a task."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_complete_task(method, endpoint, **kwargs):
        assert method == "PUT"
        assert endpoint == "tasks/99999"
        assert "json" in kwargs
        assert "task" in kwargs["json"]
        task = kwargs["json"]["task"]
        assert task["status"] == "COMPLETED"
        
        # Return mock completed task
        return {
            "task": {
                "id": 99999,
                "description": "Follow up with client",
                "status": "COMPLETED",
                "completedAt": "2024-01-02T15:00:00Z",
                "completedBy": {"id": 5, "name": "John Doe"}
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_complete_task)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "complete_task",
                    "arguments": {
                        "task_id": 99999,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "task" in data
        assert data["task"]["id"] == 99999
        assert data["task"]["status"] == "COMPLETED"
        assert "completedAt" in data["task"]


def test_set_custom_field_value(client, headers, monkeypatch):
    """Test setting a custom field value on an entity."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_set_field(method, endpoint, **kwargs):
        assert method == "PUT"
        assert endpoint == "parties/12345/fields/100"
        assert "json" in kwargs
        assert "field" in kwargs["json"]
        field = kwargs["json"]["field"]
        assert field["id"] == 100
        assert field["value"] == "Custom Value"
        
        # Return mock success response
        return {
            "party": {
                "id": 12345,
                "name": "Test Party",
                "fields": [
                    {"id": 100, "value": "Custom Value", "definition": {"name": "Industry"}}
                ]
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_set_field)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "set_custom_field_value",
                    "arguments": {
                        "entity": "parties",
                        "entity_id": 12345,
                        "field_id": 100,
                        "value": "Custom Value",
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
        assert data["party"]["fields"][0]["value"] == "Custom Value"


def test_update_custom_field_values(client, headers, monkeypatch):
    """Test updating multiple custom field values."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_update_fields(method, endpoint, **kwargs):
        assert method == "PUT"
        assert endpoint == "opportunities/5678/fields"
        assert "json" in kwargs
        assert "fields" in kwargs["json"]
        fields = kwargs["json"]["fields"]
        assert len(fields) == 3
        assert fields[0]["id"] == 101
        assert fields[0]["value"] == "Technology"
        assert fields[1]["id"] == 102
        assert fields[1]["value"] == 5000
        assert fields[2]["id"] == 103
        assert fields[2]["value"] == "2024-12-31"
        
        # Return mock success response
        return {
            "opportunity": {
                "id": 5678,
                "name": "Test Opportunity",
                "fields": [
                    {"id": 101, "value": "Technology"},
                    {"id": 102, "value": 5000},
                    {"id": 103, "value": "2024-12-31"}
                ]
            }
        }
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_update_fields)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_custom_field_values",
                    "arguments": {
                        "entity": "opportunities",
                        "entity_id": 5678,
                        "fields": [
                            {"id": 101, "value": "Technology"},
                            {"id": 102, "value": 5000},
                            {"id": 103, "value": "2024-12-31"}
                        ],
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert "opportunity" in data
        assert len(data["opportunity"]["fields"]) == 3


def test_clear_custom_field_value(client, headers, monkeypatch):
    """Test clearing a custom field value."""
    import sys
    
    # Enable writes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    
    # Remove the module from cache to force reimport with new env var
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_clear_field(method, endpoint, **kwargs):
        assert method == "DELETE"
        assert endpoint == "kases/9999/fields/200"
        
        # Return mock success response (typically empty for DELETE)
        return {}
    
    # Re-create the app to pick up the environment change
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_clear_field)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "clear_custom_field_value",
                    "arguments": {
                        "entity": "kases",
                        "entity_id": 9999,
                        "field_id": 200,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data == {}


def test_delete_party(client, headers, monkeypatch):
    """Test deleting a party."""
    import sys
    
    # Enable both writes and deletes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    monkeypatch.setenv("ENABLE_CAPSULECRM_DELETES", "true")
    
    # Remove the module from cache to force reimport with new env vars
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_delete_party(method, endpoint, **kwargs):
        assert method == "DELETE"
        assert endpoint == "parties/12345"
        
        # Return mock success response (typically empty for DELETE)
        return {}
    
    # Re-create the app to pick up the environment changes
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_delete_party)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "delete_party",
                    "arguments": {
                        "party_id": 12345,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data == {}


def test_delete_opportunity(client, headers, monkeypatch):
    """Test deleting an opportunity."""
    import sys
    
    # Enable both writes and deletes before importing
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    monkeypatch.setenv("ENABLE_CAPSULECRM_DELETES", "true")
    
    # Remove the module from cache to force reimport with new env vars
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Mock the capsule_request function
    async def mock_delete_opportunity(method, endpoint, **kwargs):
        assert method == "DELETE"
        assert endpoint == "opportunities/99999"
        
        # Return mock success response (typically empty for DELETE)
        return {}
    
    # Re-create the app to pick up the environment changes
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    # Mock after reimporting
    import capsule_mcp.server
    monkeypatch.setattr(capsule_mcp.server, "capsule_request", mock_delete_opportunity)
    
    with TestClient(test_app) as test_client:
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "delete_opportunity",
                    "arguments": {
                        "opportunity_id": 99999,
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        payload = response.json()["result"]["content"][0]["text"]
        data = json.loads(payload)
        assert data == {}


def test_delete_party_not_available_without_deletes_enabled(client, headers, monkeypatch):
    """Test that delete_party is not available when ENABLE_CAPSULECRM_DELETES is false."""
    import sys
    
    # Enable writes but not deletes
    monkeypatch.setenv("ENABLE_CAPSULECRM_WRITES", "true")
    monkeypatch.setenv("ENABLE_CAPSULECRM_DELETES", "false")
    
    # Remove the module from cache to force reimport with new env vars
    if "capsule_mcp.server" in sys.modules:
        del sys.modules["capsule_mcp.server"]
    
    # Re-create the app to pick up the environment changes
    from capsule_mcp.server import create_app
    test_app = create_app()
    
    with TestClient(test_app) as test_client:
        # Get the list of available tools
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        # Check that delete tools are not in the list
        result = response.json()
        tools = result.get("result", {}).get("tools", [])
        tool_names = [tool["name"] for tool in tools]
        assert "delete_party" not in tool_names
        assert "delete_opportunity" not in tool_names
        # But write tools should still be available
        assert "create_party" in tool_names


def test_update_note_validates_required_fields(client, headers, monkeypatch):
    """Test that update_note validates required fields."""
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
        # Test with missing note_id
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_note",
                    "arguments": {
                        "content": "Test content",
                    },
                },
                "id": 1,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result.get("result", {}).get("isError") is True
        
        # Test with empty content
        response = test_client.post(
            "/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_note",
                    "arguments": {
                        "note_id": 123,
                        "content": "",
                    },
                },
                "id": 2,
            },
            headers=headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result.get("result", {}).get("isError") is True
        
