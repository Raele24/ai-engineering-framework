---
name: dotnet-best-practices
description: "Enforces C#/.NET best practices covering XML documentation, primary constructors, dependency injection, ResourceManager localization, async/await, MSTest/Moq testing, and security."
version: "1.0.0"
source: "https://github.com/github/awesome-copilot"
license: "MIT"
category: "backend-engineering"
tier: "optional-backend"
platforms: [antigravity, copilot, claude-code, codex, gemini-cli]
requires_tools: [read_file, write_file, edit_file]
dependencies: []
security_scope: "workspace-write"
---

## Framework Provenance, Activation & Security

- **Upstream Source:** `https://github.com/github/awesome-copilot` (`MIT` License)
- **Original File Preserved:** [`UPSTREAM_SKILL.md`](./UPSTREAM_SKILL.md)
- **Category / Tier:** `backend-engineering` / `optional-backend` (Priority: `P1`)
- **Activation Conditions:** Workflow Phases `[9, 10]` (Progressive disclosure: loads on demand when relevant; `default_enabled: false`).
- **Security Scope:** `workspace-write`
- **Adaptation Note:** Standardized frontmatter. Original preserved in `UPSTREAM_SKILL.md`.

---

# .NET/C# Best Practices

Your task is to ensure .NET/C# code in ${selection} meets the best practices specific to this solution/project. This includes:

## Documentation & Structure

- Create comprehensive XML documentation comments for all public classes, interfaces, methods, and properties
- Include parameter descriptions and return value descriptions in XML comments
- Follow the established namespace structure: {Core|Console|App|Service}.{Feature}

## Design Patterns & Architecture

- Use primary constructor syntax for dependency injection (e.g., `public class MyClass(IDependency dependency)`)
- Implement the Command Handler pattern with generic base classes (e.g., `CommandHandler<TOptions>`)
- Use interface segregation with clear naming conventions (prefix interfaces with 'I')
- Follow the Factory pattern for complex object creation.

## Dependency Injection & Services

- Use constructor dependency injection with null checks via ArgumentNullException
- Register services with appropriate lifetimes (Singleton, Scoped, Transient)
- Use Microsoft.Extensions.DependencyInjection patterns
- Implement service interfaces for testability

## Resource Management & Localization

- Use ResourceManager for localized messages and error strings
- Separate LogMessages and ErrorMessages resource files
- Access resources via `_resourceManager.GetString("MessageKey")`

## Async/Await Patterns

- Use async/await for all I/O operations and long-running tasks
- Return Task or Task<T> from async methods
- Use ConfigureAwait(false) where appropriate
- Handle async exceptions properly

## Testing Standards

- Use MSTest framework with FluentAssertions for assertions
- Follow AAA pattern (Arrange, Act, Assert)
- Use Moq for mocking dependencies
- Test both success and failure scenarios
- Include null parameter validation tests

## Configuration & Settings

- Use strongly-typed configuration classes with data annotations
- Implement validation attributes (Required, NotEmptyOrWhitespace)
- Use IConfiguration binding for settings
- Support appsettings.json configuration files

## Semantic Kernel & AI Integration

- Use Microsoft.SemanticKernel for AI operations
- Implement proper kernel configuration and service registration
- Handle AI model settings (ChatCompletion, Embedding, etc.)
- Use structured output patterns for reliable AI responses

## Error Handling & Logging

- Use structured logging with Microsoft.Extensions.Logging
- Include scoped logging with meaningful context
- Throw specific exceptions with descriptive messages
- Use try-catch blocks for expected failure scenarios

## Performance & Security

- Use C# 12+ features and .NET 8 optimizations where applicable
- Implement proper input validation and sanitization
- Use parameterized queries for database operations
- Follow secure coding practices for AI/ML operations

## Code Quality

- Ensure SOLID principles compliance
- Avoid code duplication through base classes and utilities
- Use meaningful names that reflect domain concepts
- Keep methods focused and cohesive
- Implement proper disposal patterns for resources
