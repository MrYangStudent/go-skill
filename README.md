# Go Engineering Skills (go-skill)

A comprehensive Go language engineering skill set covering the complete development lifecycle from code development, testing, quality review to documentation generation.

## Core Skills

### go-project-rules

**Project Governance Rules**, ensuring project consistency, progress visibility, and standards enforcement.

| Skill | Name | Description |
|-------|------|-------------|
| [go-project-rules](./go-project-rules/) | Project Governance Rules | progress sync, README sync, commit checks, verification loop |
| [go-full-dev-workflow](./go-full-dev-workflow/) | Full Development Workflow | Integrates 13 skills for end-to-end development |

### prompt-master

**Prompt Master**, a conversational prompt engineering skill based on Andrew Ng's AI Prompting for Everyone course.

| Skill | Name | Description |
|-------|------|-------------|
| [prompt-master](./prompt-master/) | Prompt Master | Conversational prompt construction, optimization, and templates |

## Complete Skills List

### Development Workflow

| Skill | Name | Description |
|-------|------|-------------|
| [go-project-rules](./go-project-rules/) | Project Governance Rules | progress sync, README sync, commit checks, verification loop |
| [go-full-dev-workflow](./go-full-dev-workflow/) | Full Development Workflow | Requirements → Implementation → Testing → Review → Documentation → Verification |
| [feature-development-workflow](./feature-development-workflow/) | Feature Development Workflow | Requirements analysis, TDD/BDD, micro-module iterative delivery |

### Test Generation

| Skill | Name | Description |
|-------|------|-------------|
| [test-generator](./test-generator/) | Test Generator | Unit tests, concurrency tests, edge cases, Mock writing |

### Utility Functions

| Skill | Name | Description |
|-------|------|-------------|
| [go-utility-functions](./go-utility-functions/) | Go Utility Functions | HTTP client, signing, crypto, sorting, time formatting, generic slice/map conversion, pagination, retry |

### Code Review

| Skill | Name | Description |
|-------|------|-------------|
| [error-handling-reviewer](./error-handling-reviewer/) | Error Handling Reviewer | error wrapping checks, panic protection, parameter validation audit |
| [go-concurrency-reviewer](./go-concurrency-reviewer/) | Go Concurrency Reviewer | race condition detection, goroutine leak protection, channel safety |
| [dependency-reviewer](./dependency-reviewer/) | Dependency Reviewer | third-party dependency necessity, security, version pinning review |
| [performance-reviewer](./performance-reviewer/) | Performance Reviewer | timeout settings, resource closure, memory allocation, sync.Pool |
| [security-reviewer](./security-reviewer/) | Security Reviewer | sensitive data, SQL/command injection, dependency vulnerabilities |
| [database-reviewer](./database-reviewer/) | Database Reviewer | connection pool, transaction handling, query efficiency, N+1 detection |
| [logging-reviewer](./logging-reviewer/) | Logging Reviewer | log levels, sanitization, structured logging, context |
| [context-propagation-reviewer](./context-propagation-reviewer/) | Context Propagation Reviewer | chain completeness, timeout settings, cancellation, header propagation |
| [api-design-reviewer](./api-design-reviewer/) | API Design Reviewer | RESTful compliance, HTTP semantics, naming consistency, versioning |

### Documentation Generation

| Skill | Name | Description |
|-------|------|-------------|
| [doc-generator](./doc-generator/) | Documentation Generator | GoDoc comments, README, AI-friendly example blocks |
| [go-api-doc-generator](./go-api-doc-generator/) | API Documentation Generator | OpenAPI 3.0 specs, Postman collections, curl commands |

## Features

- **Full Lifecycle Coverage**: Requirements analysis → Code implementation → Test verification → Quality review → Documentation → Deployment
- **AI-Friendly**: All documentation includes AI-Usage comment blocks for Cline/Cursor tool learning
- **Zero External Dependencies**: Uses only Go standard library
- **Strict Standards**: Follows Go official best practices (gofmt, go vet, race detector)
- **Modular Design**: Each skill can be used independently or in combination

## go-full-dev-workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 0: Project Governance                │
├─────────────────────────────────────────────────────────────────┤
│  go-project-rules                                               │
│  - Session initialization (read README.md, project.md)           │
│  - Progress sync (project.md kanban management)                 │
│  - Architecture sync (README.md updates)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 1: Preparation & Documentation       │
├─────────────────────────────────────────────────────────────────┤
│  feature-development-workflow  →  Requirements clarification   │
│  doc-generator                 →  Project structure, docs       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 2: Code Implementation              │
├─────────────────────────────────────────────────────────────────┤
│  Code Implementation (following Go standards)                  │
│  - GoDoc comments                                              │
│  - Error handling                                              │
│  - Context propagation                                          │
│  - Logging                                                      │
│  - go-utility-functions (extract repeated logic into reusable) │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 3: Test Generation                   │
├─────────────────────────────────────────────────────────────────┤
│  test-generator                                                 │
│  - Happy path tests                                             │
│  - Edge case tests                                              │
│  - Error path tests                                             │
│  - Concurrency safety tests                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 4: Quality Review                    │
├─────────────────────────────────────────────────────────────────┤
│  error-handling-reviewer     →  Error handling                  │
│  go-concurrency-reviewer     →  Concurrency safety              │
│  dependency-reviewer         →  Dependency management           │
│  performance-reviewer        →  Performance                     │
│  security-reviewer           →  Security                        │
│  database-reviewer            →  Database operations            │
│  logging-reviewer            →  Logging standards               │
│  context-propagation-reviewer→  Context propagation             │
│  api-design-reviewer         →  API design                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 5: Documentation Generation          │
├─────────────────────────────────────────────────────────────────┤
│  go-api-doc-generator                                             │
│  - OpenAPI 3.0 specs                                             │
│  - Postman collections                                           │
│  - curl command examples                                        │
│  - API reference docs                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 6: Verification & Deployment         │
├─────────────────────────────────────────────────────────────────┤
│  go build                   →  Build check                     │
│  go test -race             →  Race detection                   │
│  go run                    →  Service startup                  │
│  API verification          →  Endpoint testing                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Project Initialization

Use `go-project-rules` for project initialization:

```
"initialize project"
"sync progress"
"project rules"
```

First-time use automatically loads governance rules:
- Read README.md to understand project architecture
- Read project.md to understand current progress
- Confirm next steps

### 2. Use Full Workflow

Execute the complete development workflow with one command:

```
"run full workflow"
"full development workflow"
"Go development workflow"
```

### 3. Step by Step

#### 1. Develop New Features

Use `feature-development-workflow`:

```
"develop new feature"
"feature workflow"
"start development"
```

#### 2. Code Review

Execute quality reviews as needed:

```bash
# Error handling review
error-handling-reviewer

# Concurrency safety review
go-concurrency-reviewer

# Performance review
performance-reviewer

# Security review
security-reviewer

# Dependency review
dependency-reviewer

# Database review
database-reviewer

# Logging review
logging-reviewer

# Context review
context-propagation-reviewer

# API design review
api-design-reviewer
```

#### 3. Test Generation

Generate complete test suites:

```
"generate tests"
"write unit tests"
```

#### 4. Documentation Generation

Generate API documentation:

```
"generate API docs"
"generate README"
```

## Skills Detail

### Core Workflow

#### go-project-rules

Project governance rules ensuring consistency:

- **Rule 1**: Session initialization (read README.md, project.md)
- **Rule 2**: Progress sync (project.md kanban)
- **Rule 3**: Architecture changes sync with README
- **Rule 4**: README consistency check before commit
- **Rule 5**: Full workflow after phase completion
- **Rule 6**: API modification verification loop
- **Rule 7**: Project extension constraints
- **Rule 8**: AI behavior self-check

#### go-full-dev-workflow

Integrates 13 specialized skills for end-to-end development:

- Stage 0: Project Governance (go-project-rules)
- Stage 1: Preparation & Documentation
- Stage 2: Code Implementation
- Stage 3: Test Generation
- Stage 4: Quality Review (9 review skills)
- Stage 5: Documentation Generation
- Stage 6: Verification & Deployment

### feature-development-workflow

Feature development workflow following TDD/BDD patterns:

- Requirements clarification and problem definition
- Task breakdown into verifiable micro-modules
- Design phase output templates
- Integration and verification

### test-generator

Test generation specialist:

- Happy path tests
- Edge case tests (nil, zero values, extreme values)
- Error path tests
- Concurrency safety tests
- Mock object writing

### Code Review Skills

| Skill | Coverage |
|-------|----------|
| error-handling-reviewer | error checks, panic protection, parameter validation |
| go-concurrency-reviewer | race condition, goroutine leak, channel safety |
| dependency-reviewer | necessity, stdlib alternatives, version pinning, vulnerabilities |
| performance-reviewer | timeout, resource closure, memory allocation, sync.Pool |
| security-reviewer | sensitive data, injection protection, auth, vulnerabilities |
| database-reviewer | connection pool, transactions, N+1 queries, indexes |
| logging-reviewer | log levels, sanitization, structured logging, context |
| context-propagation-reviewer | chain completeness, timeout, cancellation, header propagation |
| api-design-reviewer | RESTful, status codes, naming consistency, versioning |

### Documentation Skills

#### doc-generator

AI-friendly technical documentation:

- GoDoc style comments
- README chapter structure
- AI-Usage comment blocks
- Usage examples

#### go-api-doc-generator

API documentation generator:

- OpenAPI 3.0 specs (YAML/JSON)
- Postman Collection v2.1
- curl command examples
- Supports gorilla/mux, chi, Gin, net/http

## Code Standards

- All code formatted with `gofmt`
- Import grouping: stdlib → third-party → local packages
- Maximum line length: 120 characters
- Package names: lowercase, no underscores
- Error variables prefixed with `Err`
- Test files suffixed with `_test.go`

## Quality Checks

```bash
# Format check
gofmt -l .

# Static analysis
go vet ./...

# Race detection
go test -race ./...

# Test coverage
go test -cover ./...

# Vulnerability scanning
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

## Use Cases

- New project initialization and architecture design
- Complex business logic development
- Code quality audit and refactoring
- API documentation automation
- Team coding standards alignment

## License

MIT
