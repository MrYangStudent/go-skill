#!/usr/bin/env python3
"""
Go HTTP Handler Analyzer

Parses Go source files to extract HTTP endpoint definitions,
handler signatures, and documentation comments.
"""

import re
import os
import json
import argparse
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class Endpoint:
    """Represents a discovered HTTP endpoint."""
    path: str
    method: str
    handler_name: str
    file_path: str
    line_number: int
    description: str = ""
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    params: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = []


class GoHandlerAnalyzer:
    """Analyzes Go files to extract HTTP handler information."""
    
    # Regex patterns
    HANDLER_FUNC_PATTERN = re.compile(
        r'func\s+(\w+)\s*\([^)]*ResponseWriter[^)]*Request[^)]*\)\s*(?:error)?'
    )
    
    HTTP_METHOD_PATTERN = re.compile(
        r'\.(Get|Post|Put|Delete|Patch|Options|Head|HandleFunc|Handle)\s*\('
    )
    
    ROUTE_PATTERN = re.compile(
        r'["\']([^"\']+)["\']'
    )
    
    PARAM_PATTERN = re.compile(
        r'\{(\w+)\}|\:(\w+)'
    )
    
    TYPE_PATTERN = re.compile(
        r'(?:type|struct|interface)\s+(\w+)\s+'
    )
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.endpoints: List[Endpoint] = []
        
    def analyze(self) -> List[Endpoint]:
        """Scan all Go files and extract endpoints."""
        go_files = list(self.project_root.rglob("*.go"))
        
        for go_file in go_files:
            # Skip test files and vendor directories
            if "test" in go_file.name or "_test.go" in go_file.name:
                continue
            if "/vendor/" in str(go_file) or "\\vendor\\" in str(go_file):
                continue
                
            self._analyze_file(go_file)
            
        return self.endpoints
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Go file for HTTP handlers."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return
            
        lines = content.split('\n')
        
        # Track current handler function
        current_handler = None
        handler_line = 0
        
        for i, line in enumerate(lines, 1):
            # Check for handler function definition
            if match := self.HANDLER_FUNC_PATTERN.search(line):
                current_handler = match.group(1)
                handler_line = i
                
            # Check for route registration
            if current_handler and self.HTTP_METHOD_PATTERN.search(line):
                route = self._extract_route(line)
                method = self._extract_method(line)
                
                if route:
                    endpoint = Endpoint(
                        path=route,
                        method=method,
                        handler_name=current_handler,
                        file_path=str(file_path),
                        line_number=handler_line,
                        description=self._extract_description(lines, handler_line)
                    )
                    
                    # Extract parameters
                    endpoint.params = self._extract_params(line, route)
                    
                    # Look for request/response types in handler
                    endpoint.request_body = self._find_request_body(lines[handler_line:])
                    endpoint.response_body = self._find_response_body(lines[handler_line:])
                    
                    self.endpoints.append(endpoint)
                    current_handler = None
    
    def _extract_route(self, line: str) -> Optional[str]:
        """Extract route path from registration line."""
        # Handle mux.HandleFunc("/path", handler)
        if "HandleFunc" in line or "Handle(" in line:
            routes = self.ROUTE_PATTERN.findall(line)
            if routes:
                return routes[0]
        
        # Handle chi router style
        if match := self.ROUTE_PATTERN.search(line):
            return match.group(1)
            
        return None
    
    def _extract_method(self, line: str) -> str:
        """Extract HTTP method from registration line."""
        if ".Get(" in line:
            return "GET"
        elif ".Post(" in line:
            return "POST"
        elif ".Put(" in line:
            return "PUT"
        elif ".Delete(" in line:
            return "DELETE"
        elif ".Patch(" in line:
            return "PATCH"
        elif ".Options(" in line:
            return "OPTIONS"
        elif ".Head(" in line:
            return "HEAD"
        return "GET"  # Default for Handle/HandleFunc
    
    def _extract_params(self, line: str, route: str) -> List[Dict[str, str]]:
        """Extract path parameters from route."""
        params = []
        
        # Extract {param} or :param patterns
        for match in self.PARAM_PATTERN.finditer(route):
            param_name = match.group(1) or match.group(2)
            params.append({
                "name": param_name,
                "in": "path",
                "required": "true",
                "schema": {"type": "string"}
            })
            
        # Check for query parameters
        if "Query(" in line or "r.URL.Query()" in line:
            params.append({
                "name": "query_params",
                "in": "query",
                "description": "Query parameters"
            })
            
        return params
    
    def _extract_description(self, lines: List[str], handler_line: int) -> str:
        """Extract documentation comment before handler."""
        if handler_line > 1:
            # Look for comment above function
            comment_line = handler_line - 2
            if comment_line >= 0:
                line = lines[comment_line].strip()
                if line.startswith('//'):
                    return line.lstrip('//').strip()
        return ""
    
    def _find_request_body(self, lines: List[str]) -> Optional[str]:
        """Find request body type in handler."""
        body_pattern = re.compile(r'(json|yaml|xml)\.New(?:Decoder| unmarsh)\(r\.Body\)')
        struct_pattern = re.compile(r'struct\s*\{')
        
        for line in lines[:50]:  # Look in first 50 lines
            if body_pattern.search(line):
                # Look for struct type before
                for prev_line in lines[:lines.index(line)][-10:]:
                    if struct_match := struct_pattern.search(prev_line):
                        return "RequestBody"
            if "Request" in line and "struct" in line:
                match = re.search(r'(\w+Request)', line)
                if match:
                    return match.group(1)
        return None
    
    def _find_response_body(self, lines: List[str]) -> Optional[str]:
        """Find response body type in handler."""
        for line in lines[:50]:
            if "Response" in line and "struct" in line:
                match = re.search(r'(\w+Response)', line)
                if match:
                    return match.group(1)
            if "json.NewEncoder" in line and "w" in line:
                return "JSONResponse"
        return None
    
    def to_json(self, output_file: str):
        """Export analysis results to JSON."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                [asdict(e) for e in self.endpoints],
                f,
                indent=2,
                ensure_ascii=False
            )
        print(f"Analysis saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Go HTTP handlers")
    parser.add_argument("project_root", help="Root directory of Go project")
    parser.add_argument("-o", "--output", default="endpoints.json", help="Output file")
    
    args = parser.parse_args()
    
    analyzer = GoHandlerAnalyzer(args.project_root)
    endpoints = analyzer.analyze()
    
    print(f"Found {len(endpoints)} endpoints:")
    for ep in endpoints:
        print(f"  {ep.method:7} {ep.path} -> {ep.handler_name}")
    
    analyzer.to_json(args.output)


if __name__ == "__main__":
    main()
