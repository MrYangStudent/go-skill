#!/usr/bin/env python3
"""
OpenAPI 3.0 Specification Generator

Generates OpenAPI 3.0.3 specification from endpoint analysis data.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional


def generate_openapi(endpoints_file: str, output_file: str, 
                     title: str = "API Documentation",
                     version: str = "1.0.0",
                     description: str = "Auto-generated API documentation") -> Dict[str, Any]:
    """Generate OpenAPI 3.0 specification."""
    
    # Load endpoints
    with open(endpoints_file, 'r', encoding='utf-8') as f:
        endpoints = json.load(f)
    
    # Build OpenAPI structure
    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": version,
            "description": description,
            "contact": {
                "name": "API Support"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8080",
                "description": "Development server"
            }
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        }
    }
    
    # Group endpoints by path
    paths: Dict[str, Dict[str, Any]] = {}
    
    for endpoint in endpoints:
        path = endpoint['path']
        method = endpoint['method'].lower()
        
        if path not in paths:
            paths[path] = {}
        
        # Create operation
        operation = {
            "summary": endpoint.get('description', f"{method.upper()} {path}"),
            "operationId": endpoint['handler_name'],
            "tags": [guess_tag_from_path(path)],
            "parameters": build_parameters(endpoint.get('params', [])),
            "responses": build_responses(endpoint),
            "security": [{"BearerAuth": []}]
        }
        
        # Add request body if present
        if endpoint.get('request_body'):
            operation["requestBody"] = build_request_body(endpoint['request_body'])
        
        paths[path][method] = operation
    
    openapi["paths"] = paths
    
    # Add common schemas
    openapi["components"]["schemas"] = {
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "example": "Error message"},
                "code": {"type": "integer", "example": 400}
            }
        },
        "Success": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "message": {"type": "string", "example": "Success"}
            }
        }
    }
    
    # Write output
    output_path = Path(output_file)
    if output_path.suffix == '.json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(openapi, f, indent=2, ensure_ascii=False)
    else:
        # Generate YAML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(generate_yaml(openapi))
    
    print(f"OpenAPI spec written to {output_file}")
    return openapi


def build_parameters(params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build OpenAPI parameters array."""
    result = []
    for param in params:
        result.append({
            "name": param.get('name', param.get('in', 'param')),
            "in": param.get('in', 'query'),
            "required": param.get('required', 'true') == 'true',
            "schema": param.get('schema', {"type": "string"}),
            "description": param.get('description', '')
        })
    return result


def build_responses(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """Build OpenAPI responses object."""
    responses = {
        "200": {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Success"
                    }
                }
            }
        },
        "400": {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Error"
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Error"
                    }
                }
            }
        },
        "404": {
            "description": "Not found",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Error"
                    }
                }
            }
        },
        "500": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Error"
                    }
                }
            }
        }
    }
    return responses


def build_request_body(body_type: str) -> Dict[str, Any]:
    """Build OpenAPI request body."""
    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "$ref": f"#/components/schemas/{body_type}"
                }
            }
        }
    }


def guess_tag_from_path(path: str) -> str:
    """Guess tag from URL path."""
    parts = path.strip('/').split('/')
    if len(parts) > 1 and parts[0] not in ['api', 'v1', 'v2']:
        return parts[0].title()
    elif len(parts) > 2:
        return parts[1].title()
    return "General"


def generate_yaml(data: Dict[str, Any], indent: int = 0) -> str:
    """Simple dict to YAML converter."""
    lines = []
    prefix = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(generate_yaml(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}  -")
                    for k, v in item.items():
                        lines.append(f"{prefix}    {k}: {json.dumps(v)}")
                else:
                    lines.append(f"{prefix}  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{prefix}{key}: {str(value).lower()}")
        elif isinstance(value, str):
            if '\n' in value or len(value) > 50:
                lines.append(f"{prefix}{key}: |")
                for line in value.split('\n'):
                    lines.append(f"{prefix}  {line}")
            else:
                lines.append(f"{prefix}{key}: {value}")
        elif value is None:
            lines.append(f"{prefix}{key}: null")
        else:
            lines.append(f"{prefix}{key}: {value}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate OpenAPI 3.0 spec")
    parser.add_argument("endpoints_file", help="JSON file with endpoint data")
    parser.add_argument("-o", "--output", default="openapi.yaml", help="Output file")
    parser.add_argument("--title", default="API Documentation", help="API title")
    parser.add_argument("--version", default="1.0.0", help="API version")
    
    args = parser.parse_args()
    generate_openapi(args.endpoints_file, args.output, args.title, args.version)


if __name__ == "__main__":
    main()
