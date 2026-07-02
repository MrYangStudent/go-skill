---
name: go-api-doc-generator
description: |
  Generates OpenAPI 3.0 documentation, Postman collections, and curl commands
  from Go HTTP handlers. This skill should be used when users want to document
  their Go web APIs, create API references, or generate testing scripts.
triggers:
  - generate API docs
  - create OpenAPI spec
  - export Postman collection
  - generate curl commands
  - API documentation
  - 生成 API 文档
  - 生成 OpenAPI
---

# Go API Documentation Generator

Generate comprehensive API documentation for Go HTTP projects including OpenAPI 3.0 specs, Postman collections, and curl command examples.

## Workflow

### Step 1: Discover HTTP Handlers

Scan the Go project to identify all HTTP endpoints:

```bash
# Find all files containing HTTP method handlers
rg -t go "func\s+\w+\s*\(w\s+\w+\.ResponseWriter,\s*r\s+\*\.Request\)" --no-heading -o

# Find mux.HandleFunc patterns
rg -t go "\.HandleFunc\(\"" --no-heading

# Find gorilla/mux, chi, gin patterns
rg -t go "( gorilla/mux|github\.com/go-chi|github\.com/gin)" --type go --files-with-matches
```

### Step 2: Analyze Handler Signatures

Extract endpoint metadata from handler functions:

1. **HTTP Method**: Look for `r.Method`, `r.Method == "GET/POST/PUT/DELETE/PATCH"`
2. **Path Pattern**: Parse mux route registration or URL paths
3. **Parameters**: 
   - Path params: `{id}`, `:id` in routes
   - Query params: `r.URL.Query().Get("name")`
   - Header params: `r.Header.Get("X-Token")`
4. **Request Body**: Parse struct types from `json.NewDecoder(r.Body)`
5. **Response**: Identify response structs and status codes

### Step 3: Generate OpenAPI 3.0 Spec

Use the provided template in `references/openapi_template.md` or generate programmatically:

```yaml
openapi: 3.0.3
info:
  title: {ProjectName} API
  version: 1.0.0
  description: Auto-generated API documentation
paths:
  /endpoint:
    get:
      summary: Endpoint description
      parameters: [...]
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema: {...}
```

### Step 4: Generate Postman Collection

Create a Postman v2.1 collection JSON with:
- Collection metadata
- Folders for logical grouping
- Request items with method, URL, headers, body
- Example responses

### Step 5: Generate curl Commands

For each endpoint, generate curl commands with:
- Method and URL
- Common headers (Content-Type, Authorization)
- Request body (if applicable)
- Query parameters

## Bundled Resources

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/analyze_handlers.py` | Parse Go files to extract handler signatures |
| `scripts/generate_openapi.py` | Generate OpenAPI 3.0 JSON/YAML from analysis |
| `scripts/generate_postman.py` | Generate Postman collection JSON |
| `scripts/generate_curl.py` | Generate curl command examples |

### References

| File | Purpose |
|------|---------|
| `references/openapi_template.md` | OpenAPI 3.0 specification template |
| `references/postman_template.md` | Postman collection structure |
| `references/common_headers.md` | Standard HTTP headers reference |

### Assets

| File | Purpose |
|------|---------|
| `assets/openapi_base.yaml` | Base OpenAPI document with common schemas |

## Output Formats

### OpenAPI 3.0
- Format: YAML or JSON
- File: `openapi.yaml` or `openapi.json`
- Standards: OpenAPI 3.0.3 specification

### Postman Collection v2.1
- Format: JSON
- File: `postman_collection.json`
- Import: Postman app → Import → Select file

### curl Commands
- Format: Shell script or Markdown
- File: `curl_commands.sh` or `api_reference.md`
- Usage: Copy-paste or shell execution

## Example Usage

```
# Generate all documentation for current project
Analyze Go project → Generate OpenAPI → Generate Postman → Generate curl

# Generate specific format only
Generate OpenAPI spec only
Generate Postman collection only
Generate curl commands only
```

## Common Go Web Frameworks

### gorilla/mux
```go
router := mux.NewRouter()
router.HandleFunc("/users/{id}", getUser).Methods("GET")
router.HandleFunc("/users", createUser).Methods("POST")
```

### go-chi
```go
router := chi.NewRouter()
router.Get("/users/{id}", getUser)
router.Post("/users", createUser)
```

### Gin
```go
r := gin.Default()
r.GET("/users/:id", getUser)
r.POST("/users", createUser)
```

### net/http (stdlib)
```go
http.HandleFunc("/users", handleUsers)
http.ListenAndServe(":8080", nil)
```

## Notes

- Handle both synchronous and asynchronous handlers
- Support middleware chain documentation
- Include authentication/authorization context
- Document error response schemas
