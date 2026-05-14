# Postman Collection v2.1 Template

This is a reference template for Postman Collection v2.1 structure.

## Collection Structure

```json
{
  "info": {
    "name": "API Collection",
    "description": "API documentation collection",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8080"
    },
    {
      "key": "token",
      "value": ""
    }
  ],
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{token}}",
        "type": "string"
      }
    ]
  },
  "item": []
}
```

## Folder Structure

```json
{
  "name": "Resources",
  "item": [
    {
      "name": "List Resources",
      "request": {...}
    },
    {
      "name": "Create Resource",
      "request": {...}
    }
  ]
}
```

## Request Item Structure

```json
{
  "name": "Get User",
  "request": {
    "auth": {
      "type": "bearer",
      "bearer": [
        {
          "key": "token",
          "value": "{{token}}",
          "type": "string"
        }
      ]
    },
    "method": "GET",
    "header": [
      {
        "key": "Content-Type",
        "value": "application/json"
      },
      {
        "key": "Accept",
        "value": "application/json"
      }
    ],
    "url": {
      "raw": "{{baseUrl}}/users/123",
      "host": ["{{baseUrl}}"],
      "path": ["users", "123"],
      "query": [
        {
          "key": "include",
          "value": "profile",
          "disabled": false
        }
      ]
    },
    "body": {
      "mode": "raw",
      "raw": "{\n  \"name\": \"John\"\n}",
      "options": {
        "raw": {
          "language": "json"
        }
      }
    },
    "description": "Get a user by ID"
  },
  "response": [
    {
      "name": "Success",
      "originalRequest": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/users/123",
          "host": ["{{baseUrl}}"],
          "path": ["users", "123"]
        }
      },
      "status": "OK",
      "code": 200,
      "header": [
        {
          "key": "Content-Type",
          "value": "application/json"
        }
      ],
      "body": "{\n  \"id\": \"123\",\n  \"name\": \"John Doe\",\n  \"email\": \"john@example.com\"\n}"
    }
  ]
}
```

## Import to Postman

1. Open Postman
2. Click "Import" button
3. Select the generated JSON file
4. Configure environment variables:
   - `baseUrl`: Your API base URL
   - `token`: Your authentication token

## Environment Setup

Create an environment with these variables:

```json
{
  "id": "api-environment",
  "name": "API Environment",
  "values": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8080",
      "enabled": true
    },
    {
      "key": "token",
      "value": "your_jwt_token_here",
      "enabled": true
    }
  ]
}
```

## Pre-request Scripts

Add authentication:

```javascript
// Set auth token
if (pm.environment.get("token")) {
    pm.request.headers.add({
        key: "Authorization",
        value: "Bearer " + pm.environment.get("token")
    });
}
```

## Test Scripts

Add response validation:

```javascript
pm.test("Status code is 200", function() {
    pm.response.to.have.status(200);
});

pm.test("Response has data", function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property("data");
});
```

## Common HTTP Headers

| Header | Value | Use Case |
|--------|-------|----------|
| Content-Type | application/json | JSON request body |
| Accept | application/json | Request JSON response |
| Authorization | Bearer {token} | JWT authentication |
| X-API-Key | {api_key} | API key authentication |
| X-Request-ID | {uuid} | Request tracing |

## Collection Runner

Run all requests in sequence:

1. Select collection
2. Click "Run collection"
3. Configure iteration count and delay
4. Select environment
5. Click "Run"

## Generating from OpenAPI

Postman can import OpenAPI specs directly:

1. Postman → Import
2. Select OpenAPI file
3. Choose "Generate a collection"
4. Customize generated collection

## Export Options

- Format: Collection v2.1
- Options:
  - Indent JSON (2 or 4 spaces)
  - Include auth in collection
  - Include environments
