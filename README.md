# Go Engineering Skills (go-skill)

[English](./README.md) | [中文](./README_zh.md)

A comprehensive engineering skill set covering the complete development lifecycle from code development, testing, quality review to documentation generation. Includes 24 skills for Go engineering, tooling, and project management.

## Core Skills

### go-project-rules / project-rules-init

**Project Governance & Initialization**, establishing entity-driven development to prevent context loss across sessions.

| Skill | Name | Description |
|-------|------|-------------|
| [go-project-rules](./go-project-rules/) | Project Governance Rules | progress sync, README sync, commit checks, verification loop |
| [go-full-dev-workflow](./go-full-dev-workflow/) | Full Development Workflow | Integrates 14 specialized skills for end-to-end development |
| [project-rules-init](./project-rules-init/) | Project Rules Initializer | Entity map (ARCHITECTURE.md), progress tracking (progress.md), rule self-check |

### context-compressor / github-trend-monitor

**Context Compression & Trend Monitoring**, intelligent context compression and GitHub trend tracking.

| Skill | Name | Description |
|-------|------|-------------|
| [context-compressor](./context-compressor/) | Context Compressor | Content-type aware compression, tiered hot/cold storage, session stats |
| [github-trend-monitor](./github-trend-monitor/) | GitHub Trend Monitor | Trend scraping, AI brief generation, email reporting, spike detection |

### prompt-master

**Prompt Master**, structured prompt engineering based on Andrew Ng's course.

| Skill | Name | Description |
|-------|------|-------------|
| [prompt-master](./prompt-master/) | Prompt Master | Conversational prompt construction, optimization, and templates |

## Complete Skills List

### Development Workflow

| Skill | Name | Description |
|-------|------|-------------|
| [go-project-rules](./go-project-rules/) | Project Governance Rules | progress sync, README sync, commit checks, verification loop |
| [go-full-dev-workflow](./go-full-dev-workflow/) | Full Development Workflow | Requirements → Implementation → Testing → Review → Documentation → Verification |
| [go-incremental-dev](./go-incremental-dev/) | Incremental Development | Incremental iteration from requirements to implementation, context protection, feature manifest |
| [feature-development-workflow](./feature-development-workflow/) | Feature Development Workflow | Requirements analysis, TDD/BDD, micro-module iterative delivery |

### Test Generation

| Skill | Name | Description |
|-------|------|-------------|
| [go-test-generator](./go-test-generator/) | Test Generator | Unit tests, concurrency tests, edge cases, Mock writing |

### Utility Functions

| Skill | Name | Description |
|-------|------|-------------|
| [go-utility-functions](./go-utility-functions/) | Go Utility Functions | HTTP client, signing, crypto, sorting, time formatting, generic slice/map conversion, pagination, retry |
| [go-minimal-code](./go-minimal-code/) | Code Minimalizer | YAGNI principle enforcement, over-engineering detection, stdlib-first |

### Code Review

| Skill | Name | Description |
|-------|------|-------------|
| [go-error-handling-reviewer](./go-error-handling-reviewer/) | Error Handling Reviewer | error wrapping checks, panic protection, parameter validation audit |
| [go-concurrency-reviewer](./go-concurrency-reviewer/) | Go Concurrency Reviewer | race condition detection, goroutine leak protection, channel safety |
| [go-dependency-reviewer](./go-dependency-reviewer/) | Dependency Reviewer | third-party dependency necessity, security, version pinning review |
| [go-performance-reviewer](./go-performance-reviewer/) | Performance Reviewer | timeout settings, resource closure, memory allocation, sync.Pool |
| [go-security-reviewer](./go-security-reviewer/) | Security Reviewer | sensitive data, SQL/command injection, dependency vulnerabilities |
| [go-database-reviewer](./go-database-reviewer/) | Database Reviewer | connection pool, transaction handling, query efficiency, N+1 detection |
| [go-logging-reviewer](./go-logging-reviewer/) | Logging Reviewer | log levels, sanitization, structured logging, context |
| [go-context-propagation-reviewer](./go-context-propagation-reviewer/) | Context Propagation Reviewer | chain completeness, timeout settings, cancellation, header propagation |
| [go-api-design-reviewer](./go-api-design-reviewer/) | API Design Reviewer | RESTful compliance, HTTP semantics, naming consistency, versioning |

### Documentation Generation

| Skill | Name | Description |
|-------|------|-------------|
| [go-doc-generator](./go-doc-generator/) | Documentation Generator | GoDoc comments, README, AI-friendly example blocks |
| [go-api-doc-generator](./go-api-doc-generator/) | API Documentation Generator | OpenAPI 3.0 specs, Postman collections, curl commands |

### Project Management & Tools

| Skill | Name | Description |
|-------|------|-------------|
| [project-rules-init](./project-rules-init/) | Project Rules Initializer | Language detection, entity map generation (ARCHITECTURE.md), progress tracking (progress.md), rule self-check |
| [skill-auditor](./skill-auditor/) | Skill Auditor | Skill compliance checking, frontmatter validation, naming convention audit |
| [skill-sync-manager](./skill-sync-manager/) | Skill Sync Manager | Auto-enable/disable skills based on project language |

### General Tools

| Skill | Name | Description |
|-------|------|-------------|
| [context-compressor](./context-compressor/) | Context Compressor | Intelligent tool output and conversation compression, tiered hot/cold storage, 7 content types detection |
| [github-trend-monitor](./github-trend-monitor/) | GitHub Trend Monitor | Auto-scrape trending repos, AI-generated briefs, email daily reports, star spike detection |
| [prompt-master](./prompt-master/) | Prompt Master | Six-step structured framework, brainstorming, AI review, writing workflow |

## Features

- **Full Lifecycle Coverage**: Requirements analysis → Code implementation → Test verification → Quality review → Documentation → Deployment
- **Entity-Driven Development**: ARCHITECTURE.md tracks every module/function's purpose and description, preventing context loss across sessions
- **AI-Friendly**: All documentation includes AI-Usage comment blocks for Cline/Cursor tool learning
- **Zero External Dependencies**: Uses only Go standard library
- **Strict Standards**: Follows Go official best practices (gofmt, go vet, race detector)
- **Modular Design**: Each skill can be used independently or in combination

## go-full-dev-workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 0: Project Governance                │
├─────────────────────────────────────────────────────────────────┤
│  project-rules-init (first run) / go-project-rules               │
│  - Project init: generate entity map + progress tracking + rules │
│  - Session init: read ARCHITECTURE.md & progress.md to restore   │
│  - Progress sync (progress.md entity kanban)                     │
│  - Architecture sync (README.md updates)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 1: Preparation & Documentation       │
├─────────────────────────────────────────────────────────────────┤
│  feature-development-workflow  →  Requirements clarification   │
│  go-doc-generator                 →  Project structure, docs       │
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
│  go-test-generator                                                 │
│  - Happy path tests                                             │
│  - Edge case tests                                              │
│  - Error path tests                                             │
│  - Concurrency safety tests                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Stage 4: Quality Review                    │
├─────────────────────────────────────────────────────────────────┤
│  go-error-handling-reviewer     →  Error handling                  │
│  go-concurrency-reviewer     →  Concurrency safety              │
│  go-dependency-reviewer         →  Dependency management           │
│  go-performance-reviewer        →  Performance                     │
│  go-security-reviewer           →  Security                        │
│  go-database-reviewer            →  Database operations            │
│  go-logging-reviewer            →  Logging standards               │
│  go-context-propagation-reviewer→  Context propagation             │
│  go-api-design-reviewer         →  API design                      │
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

First run `project-rules-init` to establish the project governance foundation:

```
"initialize project rules"
"project rules init"
"set up entity map"
```

Automatically generates:
- ARCHITECTURE.md — defines every module/function's purpose by development phase
- progress.md — entity-level progress tracking and change log
- `.codebuddy/rules/` — three RULE.mdc governance files

Subsequent sessions use `go-project-rules` for ongoing governance:

```
"sync progress"
"project rules"
```

First-time use automatically loads governance rules:
- Read ARCHITECTURE.md to restore entity awareness
- Read progress.md to understand current progress
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

Use `feature-development-workflow` for new features, or `go-incremental-dev` for incremental iterations:

```
"develop new feature"
"feature workflow"
"start development"
"incremental dev"
```

#### 2. Code Review

Execute quality reviews as needed:

```bash
# Error handling review
go-error-handling-reviewer

# Concurrency safety review
go-concurrency-reviewer

# Performance review
go-performance-reviewer

# Security review
go-security-reviewer

# Dependency review
go-dependency-reviewer

# Database review
go-database-reviewer

# Logging review
go-logging-reviewer

# Context review
go-context-propagation-reviewer

# API design review
go-api-design-reviewer
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

- **Rule 1**: Session initialization (read ARCHITECTURE.md, progress.md)
- **Rule 2**: Progress sync (progress.md entity kanban)
- **Rule 3**: Architecture changes sync with README
- **Rule 4**: README consistency check before commit
- **Rule 5**: Full workflow after phase completion
- **Rule 6**: API modification verification loop
- **Rule 7**: Project extension constraints
- **Rule 8**: AI behavior self-check

#### go-full-dev-workflow

Integrates 14 specialized skills for end-to-end development, organized by stages:

- Stage 0: Project Governance (go-project-rules)
- Stage 1: Preparation & Documentation (feature-development-workflow, go-doc-generator)
- Stage 2: Code Implementation
- Stage 3: Test Generation (go-test-generator)
- Stage 4: Quality Review (9 review skills)
- Stage 5: Documentation Generation (go-api-doc-generator)
- Stage 6: Verification & Deployment

#### go-incremental-dev

Incremental development workflow for large-scale projects:

- Context protection: prevents forgetting implemented features across sessions
- Feature manifest: tracks every implemented module's interface and purpose
- Rollback safety: each step can revert to the last runnable state
- Change summary: outputs per-stage change summary

#### feature-development-workflow

Feature development workflow following TDD/BDD patterns:

- Requirements clarification and problem definition
- Task breakdown into verifiable micro-modules
- Design phase output templates
- Integration and verification

### go-test-generator

Test generation specialist:

- Happy path tests
- Edge case tests (nil, zero values, extreme values)
- Error path tests
- Concurrency safety tests
- Mock object writing

### go-minimal-code

Code Minimalizer, enforcing YAGNI principles:

- Over-engineering detection: identify unnecessary abstraction layers and interfaces
- Stdlib-first: prefer standard library over third-party dependencies
- Lazy initialization: load on demand instead of preloading
- Dead code cleanup: identify unused exports and functions

### Code Review Skills

| Skill | Coverage |
|-------|----------|
| go-error-handling-reviewer | error checks, panic protection, parameter validation |
| go-concurrency-reviewer | race condition, goroutine leak, channel safety |
| go-dependency-reviewer | necessity, stdlib alternatives, version pinning, vulnerabilities |
| go-performance-reviewer | timeout, resource closure, memory allocation, sync.Pool |
| go-security-reviewer | sensitive data, injection protection, auth, vulnerabilities |
| go-database-reviewer | connection pool, transactions, N+1 queries, indexes |
| go-logging-reviewer | log levels, sanitization, structured logging, context |
| go-context-propagation-reviewer | chain completeness, timeout, cancellation, header propagation |
| go-api-design-reviewer | RESTful, status codes, naming consistency, versioning |

### Documentation Skills

#### go-doc-generator

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

### Project Management & Tools

#### project-rules-init

Project Rules Initializer, establishing entity-driven development:

- Language/framework auto-detection (Go/Python/Node.js)
- Generates ARCHITECTURE.md entity map (defines every module/function's purpose by phase)
- Generates progress.md progress tracking (entity-level status, change log, blockers)
- Generates three RULE.mdc files under `.codebuddy/rules/` (project rules + phase rules + skills manifest)
- Rule self-check (8 checks: architecture file, progress file, phase definitions, entity traceability, skill coverage, etc.)
- **Core goal**: prevent context loss when AI sessions restart during multi-phase development

#### prompt-master

Prompt Master, based on Andrew Ng's AI Prompting for Everyone:

- Six-step structured framework: Role → Background → Purpose → Constraints → Output → Examples
- Brainstorming, AI review, writing workflow
- Sycophancy awareness and mitigation
- Image generation prompt optimization

#### github-trend-monitor

GitHub Trending Monitor:

- Auto-scrape GitHub Trending repositories
- AI-generated daily/weekly technology briefs
- Email delivery for daily and weekly reports
- Star spike detection and alerting
- Tech stack analysis and visualization dashboard

#### skill-auditor

Skill compliance auditing tool:

- Checks SKILL.md format: YAML frontmatter, name/description/triggers completeness
- Checks manifest.json structure consistency
- Checks skill directory naming conventions (language prefix, path standards)
- Outputs audit report (pass/warning/failed)

#### skill-sync-manager

Skill synchronization manager:

- Auto-enable/disable skills based on the current project's programming language
- Integrated via SessionStart hook ensures skills are always correct when switching projects
- Supports prefix-matching rules (e.g., go- prefix matches Go projects)

### General Tools

#### context-compressor

Intelligent tool output and conversation context compression:

- **7 content types detection**: JSON/code/lint/log/search/diff/text auto-detection
- **Smart routing compression**: Specialized compressors per type preserving critical information
- **Tiered storage (CCR)**: L1 Hot (Memory 15min) → L2 Cold (SQLite 2h) → L3 Removed
- **Session statistics**: Cumulative token savings, per-type stats, tier storage status, cost estimation
- **Cache management**: Hot/cold bidirectional promotion, eviction, and manual cleanup
- **8 MCP tools**: compress, retrieve, detect, stats, tier summary, cold query, cache clear, list cached

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
