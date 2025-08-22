"""Example Capsule CRM MCP Server.

This minimal server exposes read only Capsule CRM operations as Model Context
Protocol (MCP) tools.  It is intentionally simple so it can be used as a
reference implementation when integrating Capsule with AI assistants.

Run locally:
    uvicorn capsule_mcp.server:app --reload
"""

import os
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv

# Type definitions
EntityType = Literal["opportunities", "parties", "kases"]

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# Load variables from a .env file if present before reading any env vars
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CAPSULE_BASE_URL = os.getenv("CAPSULE_BASE_URL", "https://api.capsulecrm.com/api/v2")

# Capsule API token. For tests the ``PYTEST_CURRENT_TEST`` environment variable
# is set while requests are executed, so we lazily default to ``"test-token"``
# inside ``capsule_request`` rather than during import.
CAPSULE_API_TOKEN = os.getenv("CAPSULE_API_TOKEN")

# MCP API key for authenticating requests to the MCP endpoints
MCP_API_KEY = os.getenv("MCP_API_KEY")

# Enable write operations (create, update) to Capsule CRM
# Set to "true" to enable write tools, defaults to read-only mode
ENABLE_CAPSULECRM_WRITES = os.getenv("ENABLE_CAPSULECRM_WRITES", "false").lower() == "true"

# Enable delete operations (requires write operations to also be enabled)
# Set to "true" to enable delete tools, defaults to disabled for safety
# Note: Delete operations are irreversible - use with extreme caution
ENABLE_CAPSULECRM_DELETES = (
    os.getenv("ENABLE_CAPSULECRM_DELETES", "false").lower() == "true" 
    and ENABLE_CAPSULECRM_WRITES
)


# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------


async def capsule_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make a request to the Capsule CRM API."""
    url = f"{CAPSULE_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    token = CAPSULE_API_TOKEN
    if not token and os.getenv("PYTEST_CURRENT_TEST"):
        token = "test-token"
    if not token:
        raise RuntimeError(
            "CAPSULE_API_TOKEN env var is required – create one in Capsule → "
            "My Preferences → API Authentication and restart the server."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "capsule-mcp/0.1.0 (+https://github.com/fuzzylabs/capsule-mcp)",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.request(method, url, headers=headers, **kwargs)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.headers.get("content-type", "").startswith(
                "application/json"
            ):
                detail = exc.response.json()
            else:
                detail = exc.response.text
            raise RuntimeError(
                f"Capsule API error {exc.response.status_code}: {detail}"
            ) from None

        return response.json()


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

# Create the MCP server
mcp_auth = None

mcp = FastMCP(
    name="Capsule CRM MCP",
    auth=mcp_auth,
    json_response=True,
    stateless_http=True,
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def authenticate_request(request: Request):
    """Authenticate requests to MCP endpoints using API key."""
    # Skip authentication for tests
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    # Skip authentication if no API key is configured
    if not MCP_API_KEY:
        return

    # Only authenticate /mcp/ endpoints
    if not request.url.path.startswith("/mcp"):
        return

    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Use 'Authorization: Bearer <api_key>'",
        )

    # Validate Bearer token format
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use 'Authorization: Bearer <api_key>'",
        )

    provided_key = auth_header[7:]
    if provided_key != MCP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Return a new FastAPI application with the MCP routes mounted."""
    mcp_app = mcp.http_app(path="/")

    app = FastAPI(lifespan=mcp_app.lifespan)

    # Add authentication middleware
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        await authenticate_request(request)
        response = await call_next(request)
        return response

    app.mount("/mcp", mcp_app)

    @app.api_route("/mcp", methods=["GET", "POST"])
    async def mcp_redirect() -> RedirectResponse:
        """Redirect ``/mcp`` to ``/mcp/`` preserving the request method."""
        return RedirectResponse(url="/mcp/", status_code=307)

    return app


app = create_app()

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool
async def list_contacts(
    page: int = 1,
    per_page: int = 50,
    archived: bool = False,
    since: str = None,
) -> Dict[str, Any]:
    """Return a paginated list of contacts.

    Args:
        page: Page number (default: 1)
        per_page: Number of contacts per page (default: 50, max: 100)
        archived: Include archived contacts (default: false)
        since: Only return contacts modified since this date (ISO8601 format, e.g. '2024-01-01T00:00:00Z')
    """
    params = {
        "page": page,
        "perPage": per_page,
        "archived": str(archived).lower(),
    }
    if since:
        params["since"] = since

    return await capsule_request("GET", "parties", params=params)


@mcp.tool
async def search_contacts(
    keyword: str,
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Fuzzy search contacts by name, email, or organisation."""
    params = {"q": keyword, "page": page, "perPage": per_page}
    return await capsule_request("GET", "parties/search", params=params)


@mcp.tool
async def list_recent_contacts(
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Return contacts sorted by most recently contacted/updated."""
    filter_data = {
        "filter": {
            "conditions": [{"field": "type", "operator": "is", "value": "person"}],
            "orderBy": [{"field": "lastContactedOn", "direction": "descending"}],
        },
        "page": page,
        "perPage": per_page,
    }
    return await capsule_request("POST", "parties/filters/results", json=filter_data)


# ---------------------------------------------------------------------------
# Write Operations (only available when ENABLE_CAPSULECRM_WRITES=true)
# ---------------------------------------------------------------------------

# Define the create_party function separately so it can be conditionally registered
async def create_party(
    type: Literal["person", "organisation"],
    firstName: Optional[str] = None,
    lastName: Optional[str] = None,
    name: Optional[str] = None,
    title: Optional[str] = None,
    jobTitle: Optional[str] = None,
    emailAddress: Optional[str] = None,
    phoneNumber: Optional[str] = None,
    website: Optional[str] = None,
    about: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new contact (person or organisation) in Capsule CRM.
    
    Args:
        type: Type of party - either "person" or "organisation"
        firstName: First name (required for person)
        lastName: Last name (required for person)
        name: Organisation name (required for organisation)
        title: Title/salutation for person (e.g., Mr, Ms, Dr)
        jobTitle: Job title for person
        emailAddress: Primary email address
        phoneNumber: Primary phone number
        website: Website URL
        about: Notes or description about the contact
        
    Returns:
        The created party object with its assigned ID and details
    """
    # Build the party object based on type
    party_data = {"type": type}
    
    if type == "person":
        if not firstName:
            raise ValueError("Field 'firstName' is required for person type (got: None or empty)")
        if not lastName:
            raise ValueError("Field 'lastName' is required for person type (got: None or empty)")
        party_data["firstName"] = firstName
        party_data["lastName"] = lastName
        if title:
            party_data["title"] = title
        if jobTitle:
            party_data["jobTitle"] = jobTitle
    elif type == "organisation":
        if not name:
            raise ValueError("Field 'name' is required for organisation type (got: None or empty)")
        party_data["name"] = name
    else:
        raise ValueError(f"Field 'type' must be either 'person' or 'organisation' (got: {type})")
    
    # Add optional contact details
    if emailAddress:
        party_data["emailAddresses"] = [{"type": "Work", "address": emailAddress}]
    
    if phoneNumber:
        party_data["phoneNumbers"] = [{"type": "Work", "number": phoneNumber}]
    
    if website:
        party_data["websites"] = [{"type": "Work", "service": "URL", "address": website}]
    
    if about:
        party_data["about"] = about
    
    # Send the request to create the party
    request_body = {"party": party_data}
    return await capsule_request("POST", "parties", json=request_body)

# Define the create_tag function separately so it can be conditionally registered
async def create_tag(
    entity: EntityType,
    name: str,
    description: Optional[str] = None,
    dataTag: bool = False,
) -> Dict[str, Any]:
    """Create a new tag for parties, opportunities, or cases.
    
    Args:
        entity: Entity type - "parties", "opportunities", or "kases" 
        name: Name of the tag (required)
        description: Optional description of the tag
        dataTag: Whether this is a data tag (default: false)
        
    Returns:
        The created tag object with its assigned ID
    """
    if entity not in ["parties", "opportunities", "kases"]:
        raise ValueError(f"Field 'entity' must be 'parties', 'opportunities', or 'kases' (got: {entity})")
    
    if not name or not name.strip():
        raise ValueError("Field 'name' is required and cannot be empty")
    
    # Build the tag object
    tag_data = {
        "name": name.strip(),
        "dataTag": dataTag
    }
    
    if description:
        tag_data["description"] = description.strip()
    
    # Send the request to create the tag
    request_body = {"tag": tag_data}
    return await capsule_request("POST", f"{entity}/tags", json=request_body)

# Define the update_party function separately so it can be conditionally registered
async def update_party(
    party_id: int,
    firstName: Optional[str] = None,
    lastName: Optional[str] = None,
    name: Optional[str] = None,
    title: Optional[str] = None,
    jobTitle: Optional[str] = None,
    about: Optional[str] = None,
    emailAddress: Optional[str] = None,
    emailId: Optional[int] = None,
    phoneNumber: Optional[str] = None,
    phoneId: Optional[int] = None,
    website: Optional[str] = None,
    websiteId: Optional[int] = None,
) -> Dict[str, Any]:
    """Update an existing contact (person or organisation) in Capsule CRM.
    
    Only provided fields will be updated. Fields not included remain unchanged.
    
    Args:
        party_id: ID of the party to update (required)
        firstName: Updated first name (for person)
        lastName: Updated last name (for person)
        name: Updated organisation name (for organisation)
        title: Updated title/salutation (for person)
        jobTitle: Updated job title (for person)
        about: Updated notes/description
        emailAddress: Email address to add or update
        emailId: ID of existing email to update (if updating specific email)
        phoneNumber: Phone number to add or update
        phoneId: ID of existing phone to update (if updating specific phone)
        website: Website URL to add or update
        websiteId: ID of existing website to update (if updating specific website)
        
    Returns:
        The updated party object with all current details
    """
    if not party_id:
        raise ValueError("Field 'party_id' is required")
    
    # Build the update data - only include fields that were provided
    party_data = {}
    
    # Basic fields
    if firstName is not None:
        party_data["firstName"] = firstName
    if lastName is not None:
        party_data["lastName"] = lastName
    if name is not None:
        party_data["name"] = name
    if title is not None:
        party_data["title"] = title
    if jobTitle is not None:
        party_data["jobTitle"] = jobTitle
    if about is not None:
        party_data["about"] = about
    
    # Handle contact details - these are arrays that can be added/updated
    if emailAddress is not None:
        email_entry = {"type": "Work", "address": emailAddress}
        if emailId:
            email_entry["id"] = emailId  # Update existing
        party_data["emailAddresses"] = [email_entry]
    
    if phoneNumber is not None:
        phone_entry = {"type": "Work", "number": phoneNumber}
        if phoneId:
            phone_entry["id"] = phoneId  # Update existing
        party_data["phoneNumbers"] = [phone_entry]
    
    if website is not None:
        website_entry = {"type": "Work", "service": "URL", "address": website}
        if websiteId:
            website_entry["id"] = websiteId  # Update existing
        party_data["websites"] = [website_entry]
    
    if not party_data:
        raise ValueError("At least one field to update must be provided")
    
    # Send the update request
    request_body = {"party": party_data}
    return await capsule_request("PUT", f"parties/{party_id}", json=request_body)

# Define the create_note function separately so it can be conditionally registered
async def create_note(
    content: str,
    party_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a note and attach it to a party, opportunity, or project.
    
    Exactly one of party_id, opportunity_id, or project_id must be provided.
    
    Args:
        content: The note content/text (required)
        party_id: ID of the party (contact) to attach the note to
        opportunity_id: ID of the opportunity to attach the note to
        project_id: ID of the project (case) to attach the note to
        
    Returns:
        The created note entry with its assigned ID and details
    """
    if not content or not content.strip():
        raise ValueError("Field 'content' is required and cannot be empty")
    
    # Count how many entity IDs were provided
    entity_count = sum([
        party_id is not None,
        opportunity_id is not None,
        project_id is not None
    ])
    
    if entity_count == 0:
        raise ValueError(
            "Exactly one of party_id, opportunity_id, or project_id must be provided"
        )
    elif entity_count > 1:
        raise ValueError(
            "Only one of party_id, opportunity_id, or project_id can be provided"
        )
    
    # Build the entry object
    entry_data = {
        "type": "note",
        "activityType": -1,  # Standard note type
        "content": content.strip()
    }
    
    # Add the appropriate entity association
    if party_id:
        entry_data["party"] = {"id": party_id}
    elif opportunity_id:
        entry_data["opportunity"] = {"id": opportunity_id}
    elif project_id:
        entry_data["kase"] = {"id": project_id}  # API uses "kase" for projects
    
    # Send the request to create the note
    request_body = {"entry": entry_data}
    return await capsule_request("POST", "entries", json=request_body)

# Define the update_note function separately so it can be conditionally registered
async def update_note(
    note_id: int,
    content: str,
) -> Dict[str, Any]:
    """Update the content of an existing note.
    
    Args:
        note_id: ID of the note/entry to update (required)
        content: Updated note content/text (required)
        
    Returns:
        The updated note entry with its details
    """
    if not note_id:
        raise ValueError("Field 'note_id' is required")
    
    if not content or not content.strip():
        raise ValueError("Field 'content' is required and cannot be empty")
    
    # Build the update data
    entry_data = {
        "content": content.strip()
    }
    
    # Send the update request
    request_body = {"entry": entry_data}
    return await capsule_request("PUT", f"entries/{note_id}", json=request_body)

# Define the add_tag_to_entity function separately so it can be conditionally registered
async def add_tag_to_entity(
    entity: EntityType,
    entity_id: int,
    tag_id: int,
) -> Dict[str, Any]:
    """Apply an existing tag to a party, opportunity, or case.
    
    Args:
        entity: Entity type - "parties", "opportunities", or "kases"
        entity_id: ID of the entity to tag
        tag_id: ID of the tag to apply
        
    Returns:
        Success response from the API
    """
    # Validate entity type
    valid_entities = ["parties", "opportunities", "kases"]
    if entity not in valid_entities:
        raise ValueError(f"entity must be one of: {', '.join(valid_entities)}")
    
    # Apply the tag
    request_body = {"tag": {"id": tag_id}}
    return await capsule_request("POST", f"{entity}/{entity_id}/tags", json=request_body)


# Define the remove_tag_from_entity function separately so it can be conditionally registered
async def remove_tag_from_entity(
    entity: EntityType,
    entity_id: int,
    tag_id: int,
) -> Dict[str, Any]:
    """Remove a tag from a party, opportunity, or case.
    
    Args:
        entity: Entity type - "parties", "opportunities", or "kases"
        entity_id: ID of the entity to untag
        tag_id: ID of the tag to remove
        
    Returns:
        Success response from the API (typically empty with 204 status)
    """
    # Validate entity type
    valid_entities = ["parties", "opportunities", "kases"]
    if entity not in valid_entities:
        raise ValueError(f"entity must be one of: {', '.join(valid_entities)}")
    
    # Remove the tag
    return await capsule_request("DELETE", f"{entity}/{entity_id}/tags/{tag_id}")


# Define the bulk_tag_entities function separately so it can be conditionally registered
async def bulk_tag_entities(
    entity: EntityType,
    entity_ids: List[int],
    tag_ids: List[int],
    operation: Literal["add", "remove"] = "add",
) -> Dict[str, Any]:
    """Apply or remove multiple tags to/from multiple entities at once.
    
    Args:
        entity: Entity type - "parties", "opportunities", or "kases"
        entity_ids: List of entity IDs to tag/untag
        tag_ids: List of tag IDs to apply/remove
        operation: Whether to "add" or "remove" the tags (default: "add")
        
    Returns:
        Summary of successful and failed operations
    """
    # Validate entity type
    valid_entities = ["parties", "opportunities", "kases"]
    if entity not in valid_entities:
        raise ValueError(f"entity must be one of: {', '.join(valid_entities)}")
    
    if not entity_ids:
        raise ValueError("entity_ids must contain at least one ID")
    
    if not tag_ids:
        raise ValueError("tag_ids must contain at least one tag ID")
    
    # Track results
    results = {
        "operation": operation,
        "entity_type": entity,
        "successful": [],
        "failed": [],
        "total_operations": len(entity_ids) * len(tag_ids)
    }
    
    # Perform operations
    for entity_id in entity_ids:
        for tag_id in tag_ids:
            try:
                if operation == "add":
                    request_body = {"tag": {"id": tag_id}}
                    await capsule_request("POST", f"{entity}/{entity_id}/tags", json=request_body)
                else:  # remove
                    await capsule_request("DELETE", f"{entity}/{entity_id}/tags/{tag_id}")
                
                results["successful"].append({
                    "entity_id": entity_id,
                    "tag_id": tag_id
                })
            except Exception as e:
                results["failed"].append({
                    "entity_id": entity_id,
                    "tag_id": tag_id,
                    "error": str(e)
                })
    
    results["success_count"] = len(results["successful"])
    results["failure_count"] = len(results["failed"])
    
    return results


# Define the create_opportunity function separately so it can be conditionally registered
async def create_opportunity(
    name: str,
    party_id: int,
    milestone_id: int,
    description: Optional[str] = None,
    owner_id: Optional[int] = None,
    team_id: Optional[int] = None,
    value: Optional[float] = None,
    currency: Optional[str] = None,
    expected_close_on: Optional[str] = None,
    probability: Optional[int] = None,
    duration_basis: Optional[Literal["FIXED", "HOUR", "DAY", "WEEK", "MONTH", "QUARTER", "YEAR"]] = None,
    duration: Optional[int] = None,
    lost_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new sales opportunity.
    
    Args:
        name: Name/title of the opportunity (required)
        party_id: ID of the main contact/party for this opportunity (required)
        milestone_id: ID of the pipeline stage/milestone (required)
        description: Detailed description of the opportunity
        owner_id: ID of the user who owns this opportunity (required unless team_id is provided)
        team_id: ID of the team that owns this opportunity (required unless owner_id is provided)
        value: Monetary value of the opportunity
        currency: Currency code (e.g., "USD", "EUR", "GBP")
        expected_close_on: Expected close date (ISO8601 format, e.g., "2024-12-31")
        probability: Win probability percentage (0-100)
        duration_basis: Basis for duration calculation
        duration: Duration value (used with duration_basis)
        lost_reason: Reason if opportunity is lost
        
    Returns:
        The created opportunity object with its assigned ID
    """
    # Validate that either owner_id or team_id is provided
    if not owner_id and not team_id:
        raise ValueError("Either owner_id or team_id must be provided")
    
    # Build the opportunity data
    opportunity_data = {
        "name": name,
        "party": {"id": party_id},
        "milestone": {"id": milestone_id},
    }
    
    # Add optional fields
    if description:
        opportunity_data["description"] = description
    
    if owner_id:
        opportunity_data["owner"] = {"id": owner_id}
    elif team_id:
        opportunity_data["team"] = {"id": team_id}
    
    # Handle value and currency together
    if value is not None:
        value_data = {"amount": value}
        if currency:
            value_data["currency"] = currency
        opportunity_data["value"] = value_data
    
    if expected_close_on:
        opportunity_data["expectedCloseOn"] = expected_close_on
    
    if probability is not None:
        opportunity_data["probability"] = probability
    
    if duration_basis:
        opportunity_data["durationBasis"] = duration_basis
        if duration is not None:
            opportunity_data["duration"] = duration
    
    if lost_reason:
        opportunity_data["lostReason"] = lost_reason
    
    # Send the request to create the opportunity
    request_body = {"opportunity": opportunity_data}
    return await capsule_request("POST", "opportunities", json=request_body)


# Define the update_opportunity function separately so it can be conditionally registered
async def update_opportunity(
    opportunity_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    milestone_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    team_id: Optional[int] = None,
    value: Optional[float] = None,
    currency: Optional[str] = None,
    expected_close_on: Optional[str] = None,
    probability: Optional[int] = None,
    duration_basis: Optional[Literal["FIXED", "HOUR", "DAY", "WEEK", "MONTH", "QUARTER", "YEAR"]] = None,
    duration: Optional[int] = None,
    closed_on: Optional[str] = None,
    lost_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing opportunity with partial updates.
    
    Args:
        opportunity_id: ID of the opportunity to update (required)
        name: Updated name/title of the opportunity
        description: Updated description
        milestone_id: ID of the new pipeline stage/milestone
        owner_id: ID of the new owner
        team_id: ID of the new team
        value: Updated monetary value
        currency: Updated currency code
        expected_close_on: Updated expected close date (ISO8601 format)
        probability: Updated win probability percentage (0-100)
        duration_basis: Updated duration basis
        duration: Updated duration value
        closed_on: Date the opportunity was closed (ISO8601 format)
        lost_reason: Updated/set lost reason
        
    Returns:
        The updated opportunity object
    """
    # Build the update data - only include provided fields
    opportunity_data = {}
    
    if name is not None:
        opportunity_data["name"] = name
    
    if description is not None:
        opportunity_data["description"] = description
    
    if milestone_id is not None:
        opportunity_data["milestone"] = {"id": milestone_id}
    
    # Handle owner/team updates
    if owner_id is not None:
        opportunity_data["owner"] = {"id": owner_id}
        # Clear team if setting owner
        if "team" not in opportunity_data:
            opportunity_data["team"] = None
    elif team_id is not None:
        opportunity_data["team"] = {"id": team_id}
        # Clear owner if setting team
        if "owner" not in opportunity_data:
            opportunity_data["owner"] = None
    
    # Handle value updates
    if value is not None or currency is not None:
        # Get current opportunity to preserve existing value/currency if not updating both
        if value is not None:
            value_data = {"amount": value}
            if currency:
                value_data["currency"] = currency
            opportunity_data["value"] = value_data
    
    if expected_close_on is not None:
        opportunity_data["expectedCloseOn"] = expected_close_on
    
    if probability is not None:
        opportunity_data["probability"] = probability
    
    if duration_basis is not None:
        opportunity_data["durationBasis"] = duration_basis
        if duration is not None:
            opportunity_data["duration"] = duration
    
    if closed_on is not None:
        opportunity_data["closedOn"] = closed_on
    
    if lost_reason is not None:
        opportunity_data["lostReason"] = lost_reason
    
    # Ensure we have something to update
    if not opportunity_data:
        raise ValueError("At least one field must be provided to update")
    
    # Send the update request
    request_body = {"opportunity": opportunity_data}
    return await capsule_request("PUT", f"opportunities/{opportunity_id}", json=request_body)


# Define the add_party_to_opportunity function separately so it can be conditionally registered
async def add_party_to_opportunity(
    opportunity_id: int,
    party_id: int,
) -> Dict[str, Any]:
    """Associate an additional party (contact) with an opportunity.
    
    This allows you to link multiple contacts to a single opportunity beyond
    the primary party. Useful for tracking all stakeholders involved in a deal.
    
    Args:
        opportunity_id: ID of the opportunity to add the party to (required)
        party_id: ID of the party (contact) to associate with the opportunity (required)
        
    Returns:
        Success response from the API
    """
    # Build the request to add the party
    request_body = {"party": {"id": party_id}}
    
    # Send the request to add the party to the opportunity
    return await capsule_request("POST", f"opportunities/{opportunity_id}/parties", json=request_body)


# Define the remove_party_from_opportunity function separately so it can be conditionally registered
async def remove_party_from_opportunity(
    opportunity_id: int,
    party_id: int,
) -> Dict[str, Any]:
    """Remove an additional party (contact) from an opportunity.
    
    This removes the association between a party and an opportunity. Note that
    you cannot remove the primary party from an opportunity.
    
    Args:
        opportunity_id: ID of the opportunity to remove the party from (required)
        party_id: ID of the party (contact) to remove from the opportunity (required)
        
    Returns:
        Success response from the API (typically empty with 204 status)
    """
    # Send the request to remove the party from the opportunity
    return await capsule_request("DELETE", f"opportunities/{opportunity_id}/parties/{party_id}")


# Define the create_task function separately so it can be conditionally registered
async def create_task(
    description: str,
    due_on: str,
    detail: Optional[str] = None,
    due_time: Optional[str] = None,
    category: Optional[str] = None,
    owner_id: Optional[int] = None,
    party_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    case_id: Optional[int] = None,
    status: Optional[Literal["OPEN", "PENDING"]] = "OPEN",
) -> Dict[str, Any]:
    """Create a new task.
    
    Args:
        description: Short description of the task (required)
        due_on: Due date in ISO8601 format (e.g., "2024-12-31") (required)
        detail: Detailed information about the task
        due_time: Due time in HH:MM format (e.g., "14:30")
        category: Task category/type
        owner_id: ID of the user who owns this task
        party_id: ID of the contact/party this task relates to
        opportunity_id: ID of the opportunity this task relates to
        case_id: ID of the case/project this task relates to
        status: Initial status - "OPEN" or "PENDING" (default: "OPEN")
        
    Returns:
        The created task object with its assigned ID
        
    Note:
        Only one of party_id, opportunity_id, or case_id can be set.
    """
    # Validate that only one entity is linked
    entity_count = sum(1 for x in [party_id, opportunity_id, case_id] if x is not None)
    if entity_count > 1:
        raise ValueError("Only one of party_id, opportunity_id, or case_id can be set")
    
    # Build the task data
    task_data = {
        "description": description,
        "dueOn": due_on,
    }
    
    # Add optional fields
    if detail:
        task_data["detail"] = detail
    
    if due_time:
        task_data["dueTime"] = due_time
    
    if category:
        task_data["category"] = category
    
    if owner_id:
        task_data["owner"] = {"id": owner_id}
    
    if status:
        task_data["status"] = status
    
    # Add entity association
    if party_id:
        task_data["party"] = {"id": party_id}
    elif opportunity_id:
        task_data["opportunity"] = {"id": opportunity_id}
    elif case_id:
        task_data["case"] = {"id": case_id}
    
    # Send the request to create the task
    request_body = {"task": task_data}
    return await capsule_request("POST", "tasks", json=request_body)


# Define the update_task function separately so it can be conditionally registered
async def update_task(
    task_id: int,
    description: Optional[str] = None,
    detail: Optional[str] = None,
    due_on: Optional[str] = None,
    due_time: Optional[str] = None,
    category: Optional[str] = None,
    owner_id: Optional[int] = None,
    party_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    case_id: Optional[int] = None,
    status: Optional[Literal["OPEN", "COMPLETED", "PENDING"]] = None,
    completed_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing task with partial updates.
    
    Args:
        task_id: ID of the task to update (required)
        description: Updated short description
        detail: Updated detailed information
        due_on: Updated due date in ISO8601 format
        due_time: Updated due time in HH:MM format
        category: Updated category/type
        owner_id: ID of the new owner
        party_id: ID of the contact/party to associate
        opportunity_id: ID of the opportunity to associate
        case_id: ID of the case/project to associate
        status: Updated status - "OPEN", "COMPLETED", or "PENDING"
        completed_at: Completion timestamp (ISO8601 format) when marking as completed
        
    Returns:
        The updated task object
        
    Note:
        Only one of party_id, opportunity_id, or case_id can be set.
        Setting status to "COMPLETED" will automatically set completed_at if not provided.
    """
    # Build the update data - only include provided fields
    task_data = {}
    
    if description is not None:
        task_data["description"] = description
    
    if detail is not None:
        task_data["detail"] = detail
    
    if due_on is not None:
        task_data["dueOn"] = due_on
    
    if due_time is not None:
        task_data["dueTime"] = due_time
    
    if category is not None:
        task_data["category"] = category
    
    if owner_id is not None:
        task_data["owner"] = {"id": owner_id}
    
    if status is not None:
        task_data["status"] = status
        # If marking as completed and no completion time provided, API will use current time
        if status == "COMPLETED" and completed_at:
            task_data["completedAt"] = completed_at
    
    # Handle entity association updates
    entity_updates = []
    if party_id is not None:
        entity_updates.append(("party", party_id))
    if opportunity_id is not None:
        entity_updates.append(("opportunity", opportunity_id))
    if case_id is not None:
        entity_updates.append(("case", case_id))
    
    # Validate that only one entity is being set
    if len(entity_updates) > 1:
        raise ValueError("Only one of party_id, opportunity_id, or case_id can be set")
    
    # Apply entity update
    if entity_updates:
        entity_type, entity_id = entity_updates[0]
        if entity_id:
            task_data[entity_type] = {"id": entity_id}
        else:
            # Setting to None/0 clears the association
            task_data[entity_type] = None
            # Clear other entity types when setting a new one
            if entity_type != "party":
                task_data["party"] = None
            if entity_type != "opportunity":
                task_data["opportunity"] = None
            if entity_type != "case":
                task_data["case"] = None
    
    # Ensure we have something to update
    if not task_data:
        raise ValueError("At least one field must be provided to update")
    
    # Send the update request
    request_body = {"task": task_data}
    return await capsule_request("PUT", f"tasks/{task_id}", json=request_body)


# Define the complete_task function separately so it can be conditionally registered
async def complete_task(
    task_id: int,
    completed_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark a task as completed.
    
    This is a convenience function that sets the task status to COMPLETED.
    
    Args:
        task_id: ID of the task to complete (required)
        completed_at: Optional completion timestamp (ISO8601 format).
                     If not provided, current time will be used.
        
    Returns:
        The updated task object with completed status
    """
    # Use update_task to set status to COMPLETED
    return await update_task(
        task_id=task_id,
        status="COMPLETED",
        completed_at=completed_at
    )


# Define the set_custom_field_value function separately so it can be conditionally registered
async def set_custom_field_value(
    entity: EntityType,
    entity_id: int,
    field_id: int,
    value: Any,
) -> Dict[str, Any]:
    """Set a custom field value on an entity.
    
    Sets or updates a single custom field value on a party, opportunity, or case.
    
    Args:
        entity: Entity type - "parties", "opportunities", or "kases"
        entity_id: ID of the entity to set the field value on
        field_id: ID of the custom field definition
        value: The value to set (string, number, date, or boolean depending on field type)
        
    Returns:
        The updated entity with the custom field value set
    """
    # Validate entity type
    valid_entities = ["parties", "opportunities", "kases"]
    if entity not in valid_entities:
        raise ValueError(f"entity must be one of: {', '.join(valid_entities)}")
    
    # Build the field data
    field_data = {
        "field": {
            "id": field_id,
            "value": value
        }
    }
    
    # Send the request to set the field value
    return await capsule_request("PUT", f"{entity}/{entity_id}/fields/{field_id}", json=field_data)


# Define the update_custom_field_values function separately so it can be conditionally registered
async def update_custom_field_values(
    entity: EntityType,
    entity_id: int,
    fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Update multiple custom field values on an entity.
    
    Sets or updates multiple custom field values in a single operation.
    
    Args:
        entity: Entity type - "parties", "opportunities", or "kases"
        entity_id: ID of the entity to update field values on
        fields: List of field updates, each containing:
                - id: The field definition ID
                - value: The value to set
                
    Returns:
        The updated entity with all custom field values set
        
    Example:
        fields=[
            {"id": 123, "value": "Custom Value"},
            {"id": 456, "value": 1000},
            {"id": 789, "value": "2024-12-31"}
        ]
    """
    # Validate entity type
    valid_entities = ["parties", "opportunities", "kases"]
    if entity not in valid_entities:
        raise ValueError(f"entity must be one of: {', '.join(valid_entities)}")
    
    if not fields:
        raise ValueError("fields list must contain at least one field update")
    
    # Format fields for the API
    formatted_fields = []
    for field in fields:
        if "id" not in field or "value" not in field:
            raise ValueError("Each field must have 'id' and 'value' properties")
        formatted_fields.append({
            "id": field["id"],
            "value": field["value"]
        })
    
    # Build the request body
    request_body = {"fields": formatted_fields}
    
    # Send the request to update all field values
    # Note: This endpoint typically updates the entity with the new field values
    return await capsule_request("PUT", f"{entity}/{entity_id}/fields", json=request_body)


# Define the clear_custom_field_value function separately so it can be conditionally registered
async def clear_custom_field_value(
    entity: EntityType,
    entity_id: int,
    field_id: int,
) -> Dict[str, Any]:
    """Clear a custom field value from an entity.
    
    Removes the value of a custom field, effectively unsetting it.
    
    Args:
        entity: Entity type - "parties", "opportunities", or "kases"
        entity_id: ID of the entity to clear the field value from
        field_id: ID of the custom field definition to clear
        
    Returns:
        Success response from the API
    """
    # Validate entity type
    valid_entities = ["parties", "opportunities", "kases"]
    if entity not in valid_entities:
        raise ValueError(f"entity must be one of: {', '.join(valid_entities)}")
    
    # Send the request to clear the field value
    return await capsule_request("DELETE", f"{entity}/{entity_id}/fields/{field_id}")


# Define the delete_party function separately so it can be conditionally registered
async def delete_party(
    party_id: int,
) -> Dict[str, Any]:
    """Permanently delete a party (contact or organisation) from Capsule CRM.
    
    ⚠️ WARNING: This operation is IRREVERSIBLE. The party and all associated data
    will be permanently deleted. This includes:
    - All contact information
    - All notes and timeline entries
    - All custom field values
    - All tags and associations
    
    Args:
        party_id: ID of the party to delete (required)
        
    Returns:
        Success response from the API (typically empty with 204 status)
    """
    # Send the delete request
    return await capsule_request("DELETE", f"parties/{party_id}")


# Register the write tools conditionally based on environment variable
if ENABLE_CAPSULECRM_WRITES:
    mcp.tool(create_party)
    mcp.tool(update_party)
    mcp.tool(create_tag)
    mcp.tool(create_note)
    mcp.tool(update_note)
    mcp.tool(add_tag_to_entity)
    mcp.tool(remove_tag_from_entity)
    mcp.tool(bulk_tag_entities)
    mcp.tool(create_opportunity)
    mcp.tool(update_opportunity)
    mcp.tool(add_party_to_opportunity)
    mcp.tool(remove_party_from_opportunity)
    mcp.tool(create_task)
    mcp.tool(update_task)
    mcp.tool(complete_task)
    mcp.tool(set_custom_field_value)
    mcp.tool(update_custom_field_values)
    mcp.tool(clear_custom_field_value)

# Register delete tools only when explicitly enabled
if ENABLE_CAPSULECRM_DELETES:
    mcp.tool(delete_party)


@mcp.tool
async def list_opportunities(
    page: int = 1,
    per_page: int = 50,
    since: str = None,
    embed: str = "tags,fields",
) -> Dict[str, Any]:
    """Return a paginated list of opportunities.

    Args:
        page: Page number (default: 1)
        per_page: Number of opportunities per page (default: 50, max: 100)
        since: Only return opportunities modified since this date (ISO8601 format, e.g. '2024-01-01T00:00:00Z')
        embed: Comma-separated list of data to embed (default: "tags,fields")
    """
    params = {
        "page": page,
        "perPage": per_page,
    }
    if since:
        params["since"] = since
    if embed:
        params["embed"] = embed

    return await capsule_request("GET", "opportunities", params=params)


@mcp.tool
async def list_open_opportunities(
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Return open opportunities using filters API for proper filtering and sorting."""
    filter_data = {
        "filter": {
            "conditions": [
                {"field": "milestone", "operator": "is not", "value": "won"},
                {"field": "milestone", "operator": "is not", "value": "lost"},
            ],
            "orderBy": [{"field": "expectedCloseOn", "direction": "ascending"}],
        },
        "page": page,
        "perPage": per_page,
    }
    return await capsule_request(
        "POST", "opportunities/filters/results", json=filter_data
    )


# Cases/Support
@mcp.tool
async def list_cases(
    page: int = 1,
    per_page: int = 50,
    since: str = None,
    embed: str = "tags,fields,opportunity",
) -> Dict[str, Any]:
    """Return a paginated list of support cases.

    Args:
        page: Page number (default: 1)
        per_page: Number of cases per page (default: 50, max: 100)
        since: Only return cases modified since this date (ISO8601 format)
        embed: Comma-separated list of data to embed
            (default: "tags,fields,opportunity")
    """
    params = {
        "page": page,
        "perPage": per_page,
    }
    if since:
        params["since"] = since
    if embed:
        params["embed"] = embed

    return await capsule_request("GET", "kases", params=params)


@mcp.tool
async def search_cases(
    keyword: str,
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Search support cases by keyword."""
    params = {"q": keyword, "page": page, "perPage": per_page}
    return await capsule_request("GET", "kases/search", params=params)


@mcp.tool
async def get_case(case_id: int, embed: str = "tags,fields,opportunity") -> Dict[str, Any]:
    """Get detailed information about a specific support case.
    
    Args:
        case_id: The ID of the support case to retrieve
        embed: Comma-separated list of data to embed
            (default: "tags,fields,opportunity")
    """
    params = {"embed": embed} if embed else {}
    return await capsule_request("GET", f"kases/{case_id}", params=params)


# Tasks
@mcp.tool
async def list_tasks(
    page: int = 1,
    per_page: int = 50,
    since: str = None,
) -> Dict[str, Any]:
    """Return a paginated list of tasks.

    Args:
        page: Page number (default: 1)
        per_page: Number of tasks per page (default: 50, max: 100)
        since: Only return tasks modified since this date (ISO8601 format)
    """
    params = {
        "page": page,
        "perPage": per_page,
    }
    if since:
        params["since"] = since

    return await capsule_request("GET", "tasks", params=params)


@mcp.tool
async def get_task(task_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific task."""
    return await capsule_request("GET", f"tasks/{task_id}")


# Timeline Entries
@mcp.tool
async def list_entries(
    page: int = 1,
    per_page: int = 50,
    since: str = None,
) -> Dict[str, Any]:
    """Return timeline entries (notes, emails, calls, etc.).

    Args:
        page: Page number (default: 1)
        per_page: Number of entries per page (default: 50, max: 100)
        since: Only return entries modified since this date (ISO8601 format)
    """
    params = {
        "page": page,
        "perPage": per_page,
    }
    if since:
        params["since"] = since

    return await capsule_request("GET", "entries", params=params)


@mcp.tool
async def get_entry(entry_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific timeline entry."""
    return await capsule_request("GET", f"entries/{entry_id}")


# Projects
@mcp.tool
async def list_projects(
    page: int = 1,
    per_page: int = 50,
    since: str = None,
    embed: str = "tags,fields,opportunity",
) -> Dict[str, Any]:
    """Return a paginated list of projects.

    Args:
        page: Page number (default: 1)
        per_page: Number of projects per page (default: 50, max: 100)
        since: Only return projects modified since this date (ISO8601 format)
        embed: Comma-separated list of data to embed (default: "tags,fields,opportunity")
    """
    params = {
        "page": page,
        "perPage": per_page,
    }
    if since:
        params["since"] = since
    if embed:
        params["embed"] = embed

    return await capsule_request("GET", "projects", params=params)


@mcp.tool
async def get_project(project_id: int, embed: str = "tags,fields,opportunity") -> Dict[str, Any]:
    """Get detailed information about a specific project.
    
    Args:
        project_id: The ID of the project to retrieve
        embed: Comma-separated list of data to embed (default: "tags,fields,opportunity")
    """
    params = {"embed": embed} if embed else {}
    return await capsule_request("GET", f"projects/{project_id}", params=params)


# Tags
@mcp.tool
async def list_tags(
    entity: EntityType = "opportunities",
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Return a paginated list of tags for a specific entity.
    
    Args:
        entity: Entity type to get tags for. Must be one of: "opportunities", "parties", "kases" (default: "opportunities")
        page: Page number (default: 1)
        per_page: Number of tags per page (default: 50, max: 100)
    """
    params = {
        "page": page,
        "perPage": per_page,
    }
    return await capsule_request("GET", f"{entity}/tags", params=params)


@mcp.tool
async def get_tag(tag_id: int, entity: EntityType = "opportunities") -> Dict[str, Any]:
    """Get detailed information about a specific tag for an entity.
    
    Args:
        tag_id: The ID of the tag to retrieve
        entity: Entity type the tag belongs to. Must be one of: "opportunities", "parties", "kases" (default: "opportunities")
    """
    return await capsule_request("GET", f"{entity}/tags/{tag_id}")


# Users
@mcp.tool
async def list_users(
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Return a paginated list of users."""
    params = {
        "page": page,
        "perPage": per_page,
    }
    return await capsule_request("GET", "users", params=params)


@mcp.tool
async def get_user(user_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific user."""
    return await capsule_request("GET", f"users/{user_id}")


# Individual Contact Operations
@mcp.tool
async def get_contact(contact_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific contact."""
    return await capsule_request("GET", f"parties/{contact_id}")


@mcp.tool
async def get_opportunity(opportunity_id: int, embed: str = "tags,fields") -> Dict[str, Any]:
    """Get detailed information about a specific opportunity.
    
    Args:
        opportunity_id: The ID of the opportunity to retrieve
        embed: Comma-separated list of data to embed (default: "tags,fields")
    """
    params = {"embed": embed} if embed else {}
    return await capsule_request("GET", f"opportunities/{opportunity_id}", params=params)

# Configuration Tools
@mcp.tool
async def list_pipelines() -> Dict[str, Any]:
    """Return a list of sales pipelines."""
    return await capsule_request("GET", "pipelines")


@mcp.tool
async def list_stages() -> Dict[str, Any]:
    """Return a list of pipeline stages."""
    return await capsule_request("GET", "stages")


@mcp.tool
async def list_milestones() -> Dict[str, Any]:
    """Return a list of opportunity milestones."""
    return await capsule_request("GET", "milestones")


@mcp.tool
async def list_custom_fields() -> Dict[str, Any]:
    """Return a list of custom field definitions."""
    return await capsule_request("GET", "fieldDefinitions")


# Product Catalog
@mcp.tool
async def list_products(
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Return a paginated list of products."""
    params = {
        "page": page,
        "perPage": per_page,
    }
    return await capsule_request("GET", "products", params=params)


@mcp.tool
async def list_categories(
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Return a paginated list of product categories."""
    params = {
        "page": page,
        "perPage": per_page,
    }
    return await capsule_request("GET", "categories", params=params)


# System Information
@mcp.tool
async def list_currencies() -> Dict[str, Any]:
    """Return a list of supported currencies."""
    return await capsule_request("GET", "currencies")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Run as MCP server via stdio
    mcp.run("stdio")
