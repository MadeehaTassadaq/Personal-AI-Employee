---
name: code-modularity
description: Comprehensive approach to creating modular, maintainable code with clear separation of concerns, reusable components, and well-defined interfaces. Use when Claude needs to structure code with clean architecture, separate concerns, define clear boundaries between components, organize files into logical modules, or ensure code is testable and maintainable.
---

# Code Modularity

## Overview

This skill enables Claude to structure code following modular design principles with clear separation of concerns, well-defined interfaces, and reusable components. It helps create maintainable, scalable, and testable software architectures across different programming languages and frameworks.

## Core Principles

### 1. Separation of Concerns
- Divide code into distinct sections, each addressing a specific concern
- Keep business logic separate from presentation and data access layers
- Ensure each module has a single responsibility (SRP)

### 2. Loose Coupling
- Minimize dependencies between modules
- Use interfaces/abstractions instead of concrete implementations
- Implement dependency injection where appropriate

### 3. High Cohesion
- Group related functions and data together
- Ensure modules work internally as a unified unit
- Keep related functionality within the same module

## Modular Architecture Patterns

### Layered Architecture
- **Presentation Layer**: User interface and input handling
- **Business Logic Layer**: Core application logic and rules
- **Data Access Layer**: Database interactions and persistence
- **External Services Layer**: API calls and external integrations

### Component-Based Architecture
- Break functionality into reusable, self-contained components
- Define clear interfaces between components
- Ensure components can be developed and tested independently

### Module Organization
- Group related files in logical directories
- Use consistent naming conventions
- Separate configuration, constants, and utilities

## Best Practices

### File Structure
```
project/
├── src/
│   ├── models/          # Data structures and entities
│   ├── services/        # Business logic and operations
│   ├── controllers/     # Request handling and routing
│   ├── utils/           # Helper functions and utilities
│   ├── config/          # Configuration files
│   └── tests/           # Unit and integration tests
├── docs/                # Documentation
└── specs/               # Specifications
```

### Interface Design
- Define clear contracts between modules
- Use consistent parameter and return types
- Implement proper error handling at module boundaries

### Dependency Management
- Use dependency injection to manage module dependencies
- Avoid circular dependencies
- Prefer composition over inheritance

## Implementation Guidelines

### Creating New Modules
1. Identify the single responsibility of the module
2. Define a clear interface with minimal public methods
3. Ensure the module can be tested independently
4. Document the module's purpose and usage

### Refactoring Existing Code
1. Identify cohesive groups of functionality
2. Extract them into separate modules
3. Define interfaces between the new modules
4. Update dependencies to use the new structure

### Testing Modular Code
- Write unit tests for individual modules
- Create integration tests for module interactions
- Use mocks/stubs to isolate modules during testing
- Test interface contracts between modules

## Resources

### scripts/
Utility scripts for analyzing and refactoring code structure:
- `analyze_dependencies.py` - Identify circular dependencies
- `module_extractor.py` - Extract code into separate modules

### references/
Detailed architectural patterns and best practices:
- `design_patterns.md` - Common design patterns for modularity
- `clean_architecture.md` - Clean architecture principles
- `testing_strategies.md` - Testing approaches for modular code

### assets/
Template files for consistent module structure:
- `module_template.py` - Standard Python module template with interfaces, dependency injection, and documentation
