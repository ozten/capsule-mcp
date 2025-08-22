# Write Operations Roadmap for Capsule CRM MCP Server

## Overview
This document outlines the roadmap for implementing write operations in the Capsule CRM MCP server. Currently, the server is primarily read-only with limited write capabilities controlled by the `ENABLE_CAPSULECRM_WRITES` environment variable.

## Current State

### ✅ Implemented Write Operations (8 tools)
- **create_party** - Create contacts (persons or organisations)
- **update_party** - Update existing contacts with partial updates
- **create_tag** - Create tags for parties, opportunities, or cases
- **create_note** - Add notes to parties, opportunities, or projects
- **update_note** - Update content of existing notes
- **add_tag_to_entity** - Apply existing tags to entities
- **remove_tag_from_entity** - Remove tags from entities
- **bulk_tag_entities** - Apply/remove multiple tags to/from multiple entities

### 📖 Existing Read Operations
The server currently has 27 read-only tools covering:
- Contacts/Parties (list, search, get)
- Opportunities (list, get)
- Cases/Projects (list, search, get)
- Tasks (list, get)
- Timeline Entries (list, get)
- Tags (list, get)
- Users (list, get)
- Configuration items (pipelines, stages, milestones, custom fields)
- Products and Categories
- Currencies

## Priority 1: Core Business Objects (High Impact)

### 1. Opportunities Management
**Tools to implement:**
- `create_opportunity` - Create new sales opportunities
- `update_opportunity` - Update opportunity details, value, stage
- `delete_opportunity` - Remove opportunities
- `add_party_to_opportunity` - Associate additional contacts
- `add_product_to_opportunity` - Add line items/products

**Rationale:** Opportunities are central to CRM sales workflows and have the highest business impact.

### 2. Tasks Management
**Tools to implement:**
- `create_task` - Create tasks with due dates and assignments
- `update_task` - Update task details and status
- `complete_task` - Mark tasks as complete
- `delete_task` - Remove tasks

**Rationale:** Tasks drive daily workflows and user productivity.

### 3. Projects (Cases) Management
**Tools to implement:**
- `create_project` - Create new projects/cases
- `update_project` - Update project details and status
- `delete_project` - Remove projects
- `add_party_to_project` - Associate contacts with projects

**Rationale:** Projects/cases are essential for support and project management workflows.

## Priority 2: Communication & Collaboration (Medium Impact)

### 4. Timeline/Notes Management
**Tools to implement:**
- ✅ `create_note` - Add notes to parties, opportunities, or projects
- ✅ `update_note` - Update existing note content
- `delete_note` - Remove notes (if supported)
- `create_email_entry` - Log email communications (if supported)
- `create_call_entry` - Log phone calls (if supported)
- `create_meeting_entry` - Log meetings (if supported)
- `add_attachment` - Attach files to entries

**Rationale:** Communication logging is crucial for team collaboration and history tracking.

### 5. Relationship Management
**Tools to implement:**
- ✅ `create_tag` - Create new tags for entities
- ✅ `add_tag_to_entity` - Apply existing tags to entities
- ✅ `remove_tag_from_entity` - Remove tags from entities
- ✅ `bulk_tag_entities` - Apply/remove tags to/from multiple entities
- ✅ `update_party` - Update party details (partially implemented)
- `update_custom_fields` - Set custom field values on entities

**Rationale:** Enables better organization and segmentation of CRM data.

## Priority 3: Configuration & Setup (Lower Impact)

### 6. Product Catalog Management
**Tools to implement:**
- `create_product` - Add new products (if API supports)
- `update_product` - Modify product details
- `create_category` - Create product categories

**Rationale:** Less frequently changed but important for opportunity management.

### 7. Pipeline Configuration
**Tools to implement:**
- `create_milestone` - Add opportunity milestones (if API supports)
- `create_custom_field` - Define custom fields (if API supports)

**Rationale:** Usually one-time setup but valuable for customization.

## Priority 4: Bulk Operations (Advanced)

### 8. Batch Operations
**Tools to implement:**
- `bulk_create_parties` - Import multiple contacts
- `bulk_update_parties` - Mass update contacts
- `bulk_tag_entities` - Apply tags to multiple entities

**Rationale:** Efficiency features for power users and data migrations.

## Implementation Considerations

### Security & Safety
1. **Validation**: All write operations must validate input thoroughly
2. **Error Handling**: Provide clear, actionable error messages
3. **Idempotency**: Where possible, make operations idempotent
4. **Audit Trail**: Consider logging all write operations
5. **Rate Limiting**: Respect Capsule API rate limits

### Technical Patterns
1. **Consistent Naming**: Use `create_`, `update_`, `delete_` prefixes
2. **Optional Types**: Use `Optional[str]` for nullable fields
3. **Entity Types**: Reuse the `EntityType` literal for consistency
4. **Response Format**: Return full created/updated objects
5. **Test Coverage**: Each write operation needs comprehensive tests

### User Experience
1. **Progressive Enhancement**: Start with create operations, then update, then delete
2. **Helpful Defaults**: Provide sensible defaults where applicable
3. **Batch Where Useful**: Consider batch operations for common bulk tasks
4. **Clear Documentation**: Update README and CLAUDE.md with each addition

## Testing Strategy

Each write operation should have tests for:
1. **Availability**: Only when `ENABLE_CAPSULECRM_WRITES=true`
2. **Success Cases**: Valid inputs create/update/delete correctly
3. **Validation**: Invalid inputs return clear error messages
4. **API Interaction**: Correct request format sent to Capsule API
5. **Error Handling**: API errors are caught and reported clearly

## Rollout Plan

### Phase 1 (Completed ✅)
- ✅ create_party - Create new contacts
- ✅ update_party - Update existing contacts
- ✅ create_tag - Create tags for entities
- ✅ create_note - Add notes to entities
- ✅ update_note - Update existing notes
- ✅ add_tag_to_entity - Apply tags to entities
- ✅ remove_tag_from_entity - Remove tags from entities
- ✅ bulk_tag_entities - Bulk tag operations
- ✅ Environment variable control

### Phase 2 (Next Priority - Core Business Objects)
- create_opportunity - Create sales opportunities
- update_opportunity - Update opportunity details
- create_task - Create tasks with assignments
- update_task - Update task details
- complete_task - Mark tasks complete

### Phase 3 (Projects & Advanced Operations)
- create_project - Create projects/cases
- update_project - Update project details
- add_party_to_opportunity - Associate contacts with opportunities
- add_party_to_project - Associate contacts with projects

### Phase 4 (Custom Fields & Delete Operations)
- update_custom_fields - Manage custom field values
- delete_party - Remove contacts (with safety checks)
- delete_opportunity - Remove opportunities
- delete_tag - Remove unused tags
- delete_note - Remove notes

### Phase 5 (Advanced Features)
- Bulk operations (bulk_create, bulk_update)
- Attachment handling
- Email/call/meeting entry logging
- Advanced search and filtering

## Success Metrics

- **Coverage**: Percentage of Capsule API write endpoints exposed
- **Safety**: Zero data loss incidents
- **Usability**: Clear error messages and intuitive parameters
- **Performance**: Efficient API usage and error handling
- **Documentation**: Complete and accurate for all operations

## Notes

- The Capsule API uses "kases" for cases/projects endpoints despite the UI rename
- Some configuration items may be read-only via API (e.g., pipelines, stages)
- Attachment handling requires multi-step process (upload, then attach)
- Consider implementing "dry run" mode for testing write operations safely