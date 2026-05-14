#!/usr/bin/env python3
"""
Postman Collection Generator

Generates Postman v2.1 collection JSON from endpoint analysis data.
"""

import json
import argparse
from typing import Dict, Any, List
from pathlib import Path


def generate_postman(endpoints_file: str, output_file: str,
                    collection_name: str = "API Collection") -> Dict[str, Any]:
    """Generate Postman collection v2.1."""
    
    # Load endpoints
    with open(endpoints_file, 'r', encoding='utf-8') as f:
        endpoints = json.load(f)
    
    # Group endpoints by first path segment
    folders: Dict[str, List[Dict]] = {}
    for endpoint in endpoints:
        path = endpoint['path']
        tag = guess_folder_from_path(path)
        
        if tag not in folders:
            folders[tag] = []
        folders[tag].append(endpoint)
    
    # Build collection structure
    collection = {
        "info": {
            "name": collection_name,
            "description": "Auto-generated Postman collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": "http://localhost:8080"
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
    
    # Add folders
    for folder_name, items in folders.items():
        folder = {
            "name": folder_name,
            "item": [build_request(item) for item in items]
        }
        collection["item"].append(folder)
    
    # Add auth folder
    collection["item"].append({
        "name": "Auth",
        "item": [
            build_auth_request()
        ]
    })
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"Postman collection written to {output_file}")
    return collection


def build_request(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """Build a Postman request item."""
    
    request = {
        "name": endpoint.get('description', f"{endpoint['method']} {endpoint['path']}"),
        "request": {
            "method": endpoint['method'],
            "header": build_headers(endpoint),
            "url": {
                "raw": f"{{{{baseUrl}}}}{endpoint['path']}",
                "host": ["{{baseUrl}}"],
                "path": endpoint['path'].strip('/').split('/')
            },
            "description": f"Handler: {endpoint['handler_name']}\nFile: {endpoint['file_path']}:{endpoint['line_number']}"
        }
    }
    
    # Add query params
    params = endpoint.get('params', [])
    query_params = [p for p in params if p.get('in') == 'query']
    if query_params:
        request["request"]["url"]["query"] = [
            {"key": p['name'], "value": "", "description": p.get('description', '')}
            for p in query_params
        ]
    
    # Add request body
    if endpoint.get('request_body'):
        request["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(generate_example_body(endpoint['request_body']), indent=2),
            "options": {
                "raw": {"language": "json"}
            }
        }
    
    # Add response examples
    request["response"] = [
        build_response_example(endpoint)
    ]
    
    return request


def build_headers(endpoint: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build request headers."""
    headers = [
        {"key": "Content-Type", "value": "application/json"},
        {"key": "Accept", "value": "application/json"}
    ]
    return headers


def build_auth_request() -> Dict[str, Any]:
    """Build a sample auth request."""
    return {
        "name": "Sample Auth",
        "request": {
            "method": "POST",
            "header": [
                {"key": "Content-Type", "value": "application/json"}
            ],
            "url": {
                "raw": "{{baseUrl}}/auth/login",
                "host": ["{{baseUrl}}"],
                "path": ["auth", "login"]
            },
            "body": {
                "mode": "raw",
                "raw": json.dumps({
                    "username": "example",
                    "password": "password123"
                }, indent=2)
            }
        },
        "response": []
    }


def build_response_example(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """Build a response example."""
    return {
        "name": "Success Response",
        "originalRequest": {
            "method": endpoint['method'],
            "header": [
                {"key": "Content-Type", "value": "application/json"}
            ],
            "url": {
                "raw": f"{{{{baseUrl}}}}{endpoint['path']}",
                "host": ["{{baseUrl}}"],
                "path": endpoint['path'].strip('/').split('/')
            }
        },
        "status": "OK",
        "code": 200,
        "_postman_previewlanguage": "json",
        "header": [
            {"key": "Content-Type", "value": "application/json"}
        ],
        "cookie": [],
        "body": json.dumps({"data": {}, "message": "Success"}, indent=2)
    }


def generate_example_body(body_type: str) -> Dict[str, Any]:
    """Generate example request body based on type."""
    examples = {
        "RequestBody": {
            "field1": "value1",
            "field2": "value2"
        },
        "CreateRequest": {
            "name": "example",
            "description": "Example resource"
        },
        "UpdateRequest": {
            "id": "123",
            "name": "updated_name"
        },
        "LoginRequest": {
            "username": "user@example.com",
            "password": "password123"
        }
    }
    return examples.get(body_type, {"example": "value"})


def guess_folder_from_path(path: str) -> str:
    """Guess folder name from URL path."""
    parts = path.strip('/').split('/')
    
    # Skip common prefixes
    skip_prefixes = ['api', 'v1', 'v2', 'rest']
    filtered_parts = [p for p in parts if p not in skip_prefixes]
    
    if not filtered_parts:
        return "General"
    
    # Group by first segment
    first = filtered_parts[0]
    
    # Handle special cases
    if first in ['auth', 'login', 'oauth']:
        return "Auth"
    if first in ['health', 'status', 'ping']:
        return "Health"
    
    return first.title()


def main():
    parser = argparse.ArgumentParser(description="Generate Postman collection")
    parser.add_argument("endpoints_file", help="JSON file with endpoint data")
    parser.add_argument("-o", "--output", default="postman_collection.json", help="Output file")
    parser.add_argument("--name", default="API Collection", help="Collection name")
    
    args = parser.parse_args()
    generate_postman(args.endpoints_file, args.output, args.name)


if __name__ == "__main__":
    main()
