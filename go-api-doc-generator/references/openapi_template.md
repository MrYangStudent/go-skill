# OpenAPI 3.0 Specification Template

This is a reference template for OpenAPI 3.0.3 specification structure.

## Document Structure

```yaml
openapi: 3.0.3
info:
  title: API Name
  version: 1.0.0
  description: |
    API description here
  contact:
    name: API Support
    email: support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8080
    description: Development server
  - url: https://api.example.com
    description: Production server

paths:
  /resource:
    get:
      summary: List resources
      operationId: listResources
      tags:
        - Resources
      security:
        - BearerAuth: []
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceList'
        '401':
          $ref: '#/components/responses/Unauthorized'

    post:
      summary: Create a resource
      operationId: createResource
      tags:
        - Resources
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateResourceRequest'
      responses:
        '201':
          description: Resource created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'
        '400':
          $ref: '#/components/responses/BadRequest'

  /resource/{id}:
    get:
      summary: Get a resource
      operationId: getResource
      tags:
        - Resources
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'
        '404':
          $ref: '#/components/responses/NotFound'

    put:
      summary: Update a resource
      operationId: updateResource
      tags:
        - Resources
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateResourceRequest'
      responses:
        '200':
          description: Resource updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'

    delete:
      summary: Delete a resource
      operationId: deleteResource
      tags:
        - Resources
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Resource deleted
        '404':
          $ref: '#/components/responses/NotFound'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    Resource:
      type: object
      properties:
        id:
          type: string
          example: "123"
        name:
          type: string
          example: "My Resource"
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time
      required:
        - id
        - name

    ResourceList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Resource'
        total:
          type: integer
          example: 100
        limit:
          type: integer
          example: 10
        offset:
          type: integer
          example: 0

    CreateResourceRequest:
      type: object
      properties:
        name:
          type: string
          example: "New Resource"
        description:
          type: string
          example: "Description here"
      required:
        - name

    UpdateResourceRequest:
      type: object
      properties:
        name:
          type: string
        description:
          type: string

    Error:
      type: object
      properties:
        error:
          type: string
          example: "Error message"
        code:
          type: integer
          example: 400
        details:
          type: object

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    NotFound:
      description: Not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

tags:
  - name: Resources
    description: Resource management endpoints
  - name: Auth
    description: Authentication endpoints
  - name: Health
    description: Health check endpoints
```

## Common Patterns

### Path Parameters

```yaml
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
          description: User ID
```

### Query Parameters

```yaml
parameters:
  - name: search
    in: query
    schema:
      type: string
    description: Search term
  - name: status
    in: query
    schema:
      type: string
      enum: [active, inactive, pending]
  - name: limit
    in: query
    schema:
      type: integer
      minimum: 1
      maximum: 100
      default: 20
```

### Request Body

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name:
            type: string
          email:
            type: string
            format: email
        required:
          - name
          - email
```

### Authentication

```yaml
security:
  - BearerAuth: []

# Or for specific endpoints
security:
  - ApiKeyAuth: []
```

## Go-Specific Tips

### Handler Registration Patterns

```go
// gorilla/mux
router.HandleFunc("/users/{id}", getUser).Methods("GET")
router.HandleFunc("/users", createUser).Methods("POST")

// chi
router.Get("/users/{id}", getUser)
router.Post("/users", createUser)

// Gin
r.GET("/users/:id", getUser)
r.POST("/users", createUser)
```

### JSON Tags

```go
type User struct {
    ID    string `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email,omitempty"`
}
```

### Common Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request body |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Server error |
