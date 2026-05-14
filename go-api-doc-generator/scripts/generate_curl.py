#!/usr/bin/env python3
"""
curl Command Generator

Generates curl command examples from endpoint analysis data.
"""

import json
import argparse
from typing import Dict, Any, List
from pathlib import Path


def generate_curl(endpoints_file: str, output_file: str,
                  base_url: str = "http://localhost:8080") -> str:
    """Generate curl commands."""
    
    # Load endpoints
    with open(endpoints_file, 'r', encoding='utf-8') as f:
        endpoints = json.load(f)
    
    commands = []
    
    # Header
    commands.append("#!/bin/bash")
    commands.append("")
    commands.append("#" + "=" * 70)
    commands.append("# Auto-generated curl commands")
    commands.append(f"# Base URL: {base_url}")
    commands.append("#" + "=" * 70)
    commands.append("")
    
    # Environment variables
    commands.append("# Configuration")
    commands.append(f'BASE_URL="{base_url}"')
    commands.append('TOKEN="${TOKEN:-your_token_here}"')
    commands.append("")
    
    # Group by path
    current_folder = None
    for endpoint in endpoints:
        folder = guess_folder_from_path(endpoint['path'])
        
        if folder != current_folder:
            commands.append("")
            commands.append(f"# {'=' * 50}")
            commands.append(f"# {folder.upper()}")
            commands.append(f"# {'=' * 50}")
            commands.append("")
            current_folder = folder
        
        # Generate curl command
        command = generate_single_curl(endpoint, base_url)
        commands.append(command)
        commands.append("")
    
    # Write output
    content = '\n'.join(commands)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"curl commands written to {output_file}")
    return content


def generate_single_curl(endpoint: Dict[str, Any], base_url: str) -> str:
    """Generate a single curl command."""
    
    lines = []
    
    # Comment with description
    desc = endpoint.get('description') or f"{endpoint['method']} {endpoint['path']}"
    lines.append(f"# {desc}")
    lines.append(f"# Handler: {endpoint['handler_name']} ({endpoint['file_path']}:{endpoint['line_number']})")
    
    # Function definition
    func_name = generate_function_name(endpoint)
    lines.append(f"{func_name}() {{")
    
    # Build curl command
    url = f"$BASE_URL{endpoint['path']}"
    curl_parts = [f'curl -X {endpoint["method"]}']
    
    # Headers
    curl_parts.append('  -H "Content-Type: application/json"')
    curl_parts.append('  -H "Accept: application/json"')
    curl_parts.append('  -H "Authorization: Bearer $TOKEN"')
    
    # Query parameters
    query_params = [p for p in endpoint.get('params', []) if p.get('in') == 'query']
    if query_params:
        query_string = '&'.join([f'{p["name"]}=${{{p["name"]}:-""}}' for p in query_params])
        url = f'{url}?{query_string}'
    
    # Path parameters - add examples
    path_params = [p for p in endpoint.get('params', []) if p.get('in') == 'path']
    if path_params:
        for p in path_params:
            lines.append(f'  # {p["name"]}: {p.get("description", "Path parameter")}')
            lines.append(f'  local {p["name"]}="${{{p["name"]}:-\"example\"}}"')
    
    # Request body
    if endpoint.get('request_body'):
        body = generate_example_body(endpoint['request_body'])
        curl_parts.append(f'  -d \'{json.dumps(body, indent=4)}\'')
    
    # URL
    curl_parts.append(f'  "{url}"')
    
    # Pretty print option
    curl_parts.append('  | jq .')
    
    # Combine
    lines.append('  curl -s \\')
    for i, part in enumerate(curl_parts[:-1]):
        lines.append(f'{part} \\')
    lines.append(curl_parts[-1])
    
    lines.append("}")
    lines.append("")
    lines.append(f"# Usage example:")
    lines.append(f"# {func_name}")
    
    return '\n'.join(lines)


def generate_function_name(endpoint: Dict[str, Any]) -> str:
    """Generate function name from endpoint."""
    path = endpoint['path'].strip('/').replace('/', '_')
    method = endpoint['method'].lower()
    
    # Clean up path
    path = path.replace('{', '').replace('}', '')
    path = path.replace(':', '_')
    path = path.replace('-', '_')
    
    # Remove leading numbers
    while path and path[0].isdigit():
        path = path[1:]
    
    return f"api_{method}_{path}" if path else f"api_{method}"


def generate_example_body(body_type: str) -> Dict[str, Any]:
    """Generate example request body."""
    examples = {
        "RequestBody": {
            "field1": "value1",
            "field2": "value2"
        },
        "CreateUserRequest": {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secure_password"
        },
        "UpdateUserRequest": {
            "username": "john_updated",
            "email": "john_new@example.com"
        },
        "LoginRequest": {
            "username": "user@example.com",
            "password": "password123"
        },
        "CreatePostRequest": {
            "title": "My First Post",
            "content": "This is the content of my post",
            "tags": ["golang", "api"]
        },
        "SearchRequest": {
            "query": "search term",
            "limit": 10,
            "offset": 0
        }
    }
    return examples.get(body_type, {"example": "value"})


def guess_folder_from_path(path: str) -> str:
    """Guess folder name from URL path."""
    parts = path.strip('/').split('/')
    
    # Skip common prefixes
    skip_prefixes = ['api', 'v1', 'v2', 'rest']
    filtered_parts = [p for p in parts if p not in skip_prefixes and not p.startswith('{')]
    
    if not filtered_parts:
        return "general"
    
    first = filtered_parts[0]
    
    if first in ['auth', 'login', 'oauth', 'token']:
        return "auth"
    if first in ['health', 'status', 'ping']:
        return "health"
    if first in ['users', 'user']:
        return "users"
    if first in ['posts', 'post']:
        return "posts"
    
    return first


def generate_markdown(endpoints_file: str, output_file: str,
                     base_url: str = "http://localhost:8080") -> str:
    """Generate curl commands in Markdown format."""
    
    with open(endpoints_file, 'r', encoding='utf-8') as f:
        endpoints = json.load(f)
    
    lines = []
    lines.append(f"# API Reference\n")
    lines.append(f"**Base URL**: `{base_url}`\n")
    lines.append(f"**Authentication**: Bearer Token\n")
    lines.append("")
    
    # Group by path
    current_folder = None
    for endpoint in endpoints:
        folder = guess_folder_from_path(endpoint['path'])
        
        if folder != current_folder:
            lines.append(f"## {folder.title()}\n")
            current_folder = folder
        
        # Endpoint documentation
        lines.append(f"### `{endpoint['method']} {endpoint['path']}`\n")
        
        desc = endpoint.get('description')
        if desc:
            lines.append(f"{desc}\n")
        
        lines.append(f"**Handler**: `{endpoint['handler_name']}`\n")
        lines.append("")
        
        # Parameters
        params = endpoint.get('params', [])
        if params:
            lines.append("**Parameters:**\n")
            lines.append("| Name | In | Type | Description |")
            lines.append("|------|----|------|-------------|")
            for p in params:
                lines.append(f"| {p.get('name', 'param')} | {p.get('in', 'query')} | string | {p.get('description', '')} |")
            lines.append("")
        
        # Request body
        if endpoint.get('request_body'):
            lines.append(f"**Request Body** (`{endpoint['request_body']}`):\n")
            body = generate_example_body(endpoint['request_body'])
            lines.append("```json")
            lines.append(json.dumps(body, indent=2))
            lines.append("```\n")
        
        # curl command
        lines.append("**curl**:\n")
        lines.append("```bash")
        lines.append(generate_markdown_curl(endpoint, base_url))
        lines.append("```\n")
        lines.append("")
    
    content = '\n'.join(lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Markdown written to {output_file}")
    return content


def generate_markdown_curl(endpoint: Dict[str, Any], base_url: str) -> str:
    """Generate a curl command for Markdown."""
    
    url = f"{base_url}{endpoint['path']}"
    method = endpoint['method']
    
    parts = [f'curl -X {method} \\']
    parts.append(f'  "{url}" \\')
    parts.append('  -H "Content-Type: application/json" \\')
    parts.append('  -H "Authorization: Bearer $TOKEN"')
    
    if endpoint.get('request_body'):
        body = generate_example_body(endpoint['request_body'])
        parts.append('  -d \'{}\''.format(json.dumps(body).replace("'", "\\'")))
    
    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generate curl commands")
    parser.add_argument("endpoints_file", help="JSON file with endpoint data")
    parser.add_argument("-o", "--output", default="curl_commands.sh", help="Output file")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Base URL")
    parser.add_argument("--format", choices=["bash", "markdown"], default="bash",
                       help="Output format")
    
    args = parser.parse_args()
    
    if args.format == "bash":
        generate_curl(args.endpoints_file, args.output, args.base_url)
    else:
        output_md = args.output.replace('.sh', '.md')
        generate_markdown(args.endpoints_file, output_md, args.base_url)


if __name__ == "__main__":
    main()
