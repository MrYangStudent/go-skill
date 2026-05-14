# Common HTTP Headers Reference

## Standard Request Headers

### Content-Type

Indicates the media type of the request body.

| Value | Use Case |
|-------|----------|
| `application/json` | JSON data (most common) |
| `application/xml` | XML data |
| `application/x-www-form-urlencoded` | Form data |
| `multipart/form-data` | File uploads |
| `text/plain` | Plain text |

### Accept

Indicates acceptable response media types.

| Value | Use Case |
|-------|----------|
| `application/json` | JSON response |
| `application/xml` | XML response |
| `*/*` | Any media type |

### Authorization

Provides authentication credentials.

| Type | Format | Example |
|------|--------|---------|
| Bearer | `Bearer {token}` | `Authorization: Bearer eyJhbGci...` |
| Basic | `Basic {base64}` | `Authorization: Basic dXNlcjpwYXNz` |
| API Key | Header name + value | `X-API-Key: your_api_key` |

### Custom Headers

| Header | Description | Example |
|--------|-------------|---------|
| `X-Request-ID` | Request tracing ID | `X-Request-ID: abc-123` |
| `X-Correlation-ID` | Correlation ID for distributed tracing | `X-Correlation-ID: corr-456` |
| `X-Forwarded-For` | Original client IP | `X-Forwarded-For: 192.168.1.1` |
| `X-API-Key` | API key authentication | `X-API-Key: your_api_key` |
| `User-Agent` | Client identifier | `User-Agent: MyApp/1.0` |
| `Accept-Language` | Preferred languages | `Accept-Language: en-US,zh-CN` |
| `Accept-Encoding` | Acceptable encodings | `Accept-Encoding: gzip, deflate` |

## Standard Response Headers

### Content-Type

```http
Content-Type: application/json; charset=utf-8
```

### Content-Length

```http
Content-Length: 1234
```

### Cache-Control

| Value | Description |
|-------|-------------|
| `no-cache` | Don't cache |
| `no-store` | Don't store |
| `max-age=3600` | Cache for 1 hour |
| `private` | Only browser caches |
| `public` | Any cache can store |

### CORS Headers

| Header | Description | Example |
|--------|-------------|---------|
| `Access-Control-Allow-Origin` | Allowed origins | `Access-Control-Allow-Origin: *` |
| `Access-Control-Allow-Methods` | Allowed methods | `Access-Control-Allow-Methods: GET, POST` |
| `Access-Control-Allow-Headers` | Allowed headers | `Access-Control-Allow-Headers: Content-Type` |
| `Access-Control-Max-Age` | Preflight cache time | `Access-Control-Max-Age: 86400` |

### Rate Limiting

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Max requests per window |
| `X-RateLimit-Remaining` | Remaining requests |
| `X-RateLimit-Reset` | Reset timestamp |
| `Retry-After` | Wait time (after 429) |

## Common Status Codes

### 2xx Success

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 202 | Accepted | Async processing started |
| 204 | No Content | Successful DELETE |

### 4xx Client Errors

| Code | Meaning | Use Case |
|------|---------|----------|
| 400 | Bad Request | Invalid request body |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | Wrong HTTP method |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limited |

### 5xx Server Errors

| Code | Meaning | Use Case |
|------|---------|----------|
| 500 | Internal Server Error | Unexpected error |
| 502 | Bad Gateway | Upstream error |
| 503 | Service Unavailable | Server down |
| 504 | Gateway Timeout | Upstream timeout |

## curl Examples

### Basic GET

```bash
curl -X GET "http://localhost:8080/api/users"
```

### GET with Headers

```bash
curl -X GET "http://localhost:8080/api/users" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN"
```

### GET with Query Parameters

```bash
curl -X GET "http://localhost:8080/api/users?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

### GET with Path Parameter

```bash
curl -X GET "http://localhost:8080/api/users/123" \
  -H "Authorization: Bearer $TOKEN"
```

### POST with JSON Body

```bash
curl -X POST "http://localhost:8080/api/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username": "john", "email": "john@example.com"}'
```

### PUT with JSON Body

```bash
curl -X PUT "http://localhost:8080/api/users/123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username": "john_updated"}'
```

### DELETE

```bash
curl -X DELETE "http://localhost:8080/api/users/123" \
  -H "Authorization: Bearer $TOKEN"
```

### With Pretty Output

```bash
curl -s "http://localhost:8080/api/users" | jq .
```

### With Verbose Output

```bash
curl -v -X GET "http://localhost:8080/api/users" 2>&1
```

### Save Response to File

```bash
curl -s -X GET "http://localhost:8080/api/users" -o users.json
```

### Upload File

```bash
curl -X POST "http://localhost:8080/api/upload" \
  -F "file=@/path/to/file.txt"
```
