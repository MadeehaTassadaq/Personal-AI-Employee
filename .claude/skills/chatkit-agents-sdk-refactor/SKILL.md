---
name: chatkit-agents-sdk-refactor
description: Restructures an existing Todo AI Chatbot repository into a clean, production-ready monorepo by separating ChatKit frontend and Agents SDK backend into distinct folders, removing redundant files, and enforcing a minimal, scalable architecture aligned with ChatKit, MCP, and OpenAI Agents SDK. Ensures the backend remains fully stateless and production-deployable.
---

# ChatKit + Agents SDK Production Refactor

This skill restructures an existing Todo AI Chatbot repository into a clean, production-ready monorepo by:
1. Separating ChatKit frontend and Agents SDK backend into distinct folders
2. Removing redundant, experimental, or non-production files
3. Enforcing a minimal, scalable architecture aligned with ChatKit, MCP, and OpenAI Agents SDK
4. Ensuring the backend remains fully stateless and production-deployable

## Prerequisites

Before running this refactor, ensure the following:
- Repository contains mixed frontend/backend code that needs separation
- ChatKit packages are installed (`openai-chatkit`)
- OpenAI Agents SDK is installed (`openai-agents`)
- MCP SDK is installed (`mcp`)
- Backup of the repository exists (this is a destructive operation)

## Pre-Refactor Validation

1. **Check repository structure**:
   - Verify current directory organization
   - Identify mixed frontend/backend files
   - Locate legacy UI components
   - Identify test scripts, playgrounds, or demo files

2. **Verify dependencies**:
   - Confirm `openai-chatkit`, `openai-agents`, and `mcp` are in requirements
   - Check that SQLModel/PostgreSQL dependencies are properly configured

## Refactor Process

### Phase 1: Repository Structure Cleanup

1. **Create new directory structure**:
   ```
   project-root/
   ├── frontend/
   │   ├── chatkit/
   │   │   ├── components/
   │   │   ├── lib/
   │   │   └── pages/
   │   └── package.json
   ├── backend/
   │   ├── agents/
   │   ├── mcp_tools/
   │   ├── api/
   │   ├── models/
   │   ├── services/
   │   ├── database/
   │   ├── tests/
   │   └── pyproject.toml
   ├── shared/
   │   └── types/
   └── README.md
   ```

2. **Identify files to move**:
   - Frontend UI components → `frontend/chatkit/components/`
   - ChatKit client code → `frontend/chatkit/lib/`
   - API routes → `backend/api/`
   - Agent implementations → `backend/agents/`
   - MCP tools → `backend/mcp_tools/`
   - Data models → `backend/models/`
   - Services → `backend/services/`
   - Database code → `backend/database/`

3. **Identify files to remove**:
   - Experimental playground files
   - Legacy UI components not using ChatKit
   - Duplicate configuration files
   - Demo scripts
   - Test files for removed functionality

### Phase 2: Frontend Restructuring

1. **Move frontend files** to `frontend/` directory:
   - All React/Vue/Angular components related to chat functionality
   - Client-side ChatKit integration code
   - Frontend state management
   - UI assets and styles

2. **Restructure to use ChatKit**:
   - Replace custom chat UI with ChatKit components
   - Implement ChatKit client connection
   - Update authentication to work with ChatKit
   - Ensure real-time messaging via ChatKit protocol

3. **Update frontend dependencies**:
   - Add ChatKit client SDK
   - Remove legacy UI dependencies
   - Update build configuration for new structure

### Phase 3: Backend Restructuring

1. **Move backend files** to `backend/` directory:
   - All Python files related to API, agents, and data processing
   - Database models and schemas
   - Agent implementations using OpenAI Agents SDK
   - MCP tool definitions
   - Authentication and middleware

2. **Restructure for stateless design**:
   - Ensure all state is stored in the database
   - Remove any in-memory state management
   - Verify all API endpoints are stateless
   - Update session management to be stateless

3. **Integrate with MCP**:
   - Ensure all task operations are exposed as MCP tools
   - Verify tools follow MCP specification
   - Update authentication to work with MCP context injection

4. **Update backend dependencies**:
   - Ensure `openai-agents`, `mcp`, and `openai-chatkit` are properly configured
   - Update `pyproject.toml` or `requirements.txt`
   - Verify database dependencies (SQLModel, PostgreSQL)

### Phase 4: Configuration and Environment

1. **Update configuration files**:
   - Separate frontend and backend environment variables
   - Update API endpoints to reflect new structure
   - Ensure CORS settings allow frontend/backend communication

2. **Update deployment configurations**:
   - Modify Docker configurations if present
   - Update CI/CD pipelines
   - Update any orchestration files (Kubernetes, etc.)

### Phase 5: Testing and Validation

1. **Verify functionality**:
   - Test ChatKit integration end-to-end
   - Verify all MCP tools work correctly
   - Ensure agent functionality is preserved
   - Confirm authentication works across frontend/backend

2. **Run tests**:
   - Execute backend unit tests
   - Run integration tests
   - Verify frontend builds and runs correctly

## Post-Refactor Validation

1. **Check new structure**:
   - Confirm all files are in appropriate directories
   - Verify no functionality was lost during migration
   - Ensure dependencies are properly configured

2. **Test production readiness**:
   - Verify stateless backend design
   - Confirm scalability of the architecture
   - Test error handling and logging
   - Verify security measures are in place

## Rollback Plan

If issues arise after refactoring:
1. Restore from backup if available
2. Verify all functionality before committing changes
3. Test in staging environment before production deployment