#!/usr/bin/env python3
"""
Script to programmatically update the TEST_INDEX.md file.
Handles adding/updating test mappings and dependencies while maintaining the document format.
"""

import re
import sys
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class TestMapping:
    source: str
    tests: List[str]
    description: str

@dataclass
class Component:
    name: str
    mappings: List[TestMapping]

@dataclass
class Dependency:
    type: str
    tests: List[str]
    description: Optional[str] = None

class TestIndexUpdater:
    def __init__(self, file_path: str = "docs/TEST_INDEX.md"):
        self.file_path = file_path
        self.content = self._read_file()
        
    def _read_file(self) -> str:
        """Read the TEST_INDEX.md file"""
        try:
            with open(self.file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: {self.file_path} not found")
            sys.exit(1)
    
    def _write_file(self, content: str):
        """Write content back to TEST_INDEX.md"""
        with open(self.file_path, "w") as f:
            f.write(content)
    
    def _find_component_section(self, component_name: str) -> tuple[int, int]:
        """Find the start and end positions of a component section"""
        pattern = f"## {re.escape(component_name)}\n"
        match = re.search(pattern, self.content)
        if not match:
            return -1, -1
        
        start = match.start()
        next_section = re.search(r"\n##\s+", self.content[start + len(pattern):])
        end = next_section.start() + start + len(pattern) if next_section else len(self.content)
        return start, end
    
    def _format_test_files(self, tests: List[str]) -> str:
        """Format test files with proper markdown and line breaks"""
        return "<br>".join([f"`{test}`" for test in tests])
    
    def add_mapping(self, source: str, tests: List[str], description: str, component: str):
        """Add a new mapping to a component section"""
        start, end = self._find_component_section(component)
        if start == -1:
            print(f"Error: Component section '{component}' not found")
            sys.exit(1)
        
        # Find the table in the section
        section = self.content[start:end]
        table_end = section.find("\n\n", section.find("|---"))
        if table_end == -1:
            table_end = len(section)
        
        # Create new table row
        new_row = f"| `{source}` | {self._format_test_files(tests)} | {description} |\n"
        
        # Insert the new row
        updated_section = (
            section[:table_end] +
            new_row +
            section[table_end:]
        )
        
        # Update the content
        self.content = self.content[:start] + updated_section + self.content[end:]
        self._write_file(self.content)
        print(f"Added mapping for {source} to {component}")
    
    def update_mapping(self, source: str, description: Optional[str] = None, tests: Optional[List[str]] = None):
        """Update an existing mapping"""
        pattern = r"\|\s*`" + re.escape(source) + r"`\s*\|([^|]+)\|([^|]+)\|"
        match = re.search(pattern, self.content)
        if not match:
            print(f"Error: No mapping found for {source}")
            sys.exit(1)
        
        current_tests = match.group(1).strip()
        current_desc = match.group(2).strip()
        
        # Update the row
        new_tests = self._format_test_files(tests) if tests else current_tests
        new_desc = description if description else current_desc
        new_row = f"| `{source}` | {new_tests} | {new_desc} |"
        
        # Replace the old row
        self.content = re.sub(pattern, new_row, self.content)
        self._write_file(self.content)
        print(f"Updated mapping for {source}")
    
    def add_dependency(self, change_type: str, dependency: str, description: Optional[str] = None):
        """Add a new dependency to a change type section"""
        pattern = f"### {re.escape(change_type)}\n"
        match = re.search(pattern, self.content)
        if not match:
            print(f"Error: Change type section '{change_type}' not found")
            sys.exit(1)
        
        # Find the end of the current dependencies
        start = match.end()
        next_section = re.search(r"\n###\s+", self.content[start:])
        section_end = next_section.start() + start if next_section else len(self.content)
        
        # Add the new dependency
        new_dep = f"- Run `{dependency}`"
        if description:
            new_dep += f" - {description}"
        new_dep += "\n"
        
        # Insert at the end of the current dependencies
        self.content = (
            self.content[:section_end] +
            new_dep +
            self.content[section_end:]
        )
        self._write_file(self.content)
        print(f"Added dependency {dependency} to {change_type}")
    
    def validate(self) -> bool:
        """Validate the TEST_INDEX.md format"""
        # Check component sections
        if not re.search(r"^## Document Format\n", self.content, re.MULTILINE):
            print("Error: Missing Document Format section")
            return False
        
        # Check component tables
        components = re.finditer(r"^## ([^#\n]+)$", self.content, re.MULTILINE)
        for comp in components:
            name = comp.group(1).strip()
            if name in ["Document Format", "Test Dependencies", "Running Tests", 
                       "Coverage Requirements", "Maintaining This Index", 
                       "File Format Schema", "Regex Patterns"]:
                continue
                
            # Find the table header
            table_pattern = r"\|\s*Source File\s*\|\s*Test Files\s*\|\s*Description\s*\|"
            section_start = comp.start()
            next_section = re.search(r"\n##\s+", self.content[section_start:])
            section_end = next_section.start() + section_start if next_section else len(self.content)
            section = self.content[section_start:section_end]
            
            if not re.search(table_pattern, section):
                print(f"Error: Invalid table format in {name} section")
                return False
        
        # Find Test Dependencies section
        deps_section = re.search(r"^## Test Dependencies\n.*?(?=^##|\Z)", self.content, re.MULTILINE | re.DOTALL)
        if not deps_section:
            print("Error: Missing Test Dependencies section")
            return False
            
        # Check each dependency subsection
        subsections = re.finditer(r"### ([^\n]+)\n(.*?)(?=###|\Z)", deps_section.group(0), re.DOTALL)
        for subsection in subsections:
            change_type = subsection.group(1)
            content = subsection.group(2).strip()
            
            # Check if at least one valid dependency line exists
            valid_lines = [
                line.strip() for line in content.split("\n")
                if line.strip() and line.strip().startswith("- Run `") and "`" in line
            ]
            
            if not valid_lines:
                print(f"Error: No valid dependencies found in {change_type} section")
                return False
        
        print("TEST_INDEX.md format is valid")
        return True

def main():
    parser = argparse.ArgumentParser(description="Update TEST_INDEX.md programmatically")
    
    # Add subparsers for different operations
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add mapping command
    add_parser = subparsers.add_parser("add-mapping", help="Add a new test mapping")
    add_parser.add_argument("--source", required=True, help="Source file path")
    add_parser.add_argument("--tests", nargs="+", required=True, help="Test file paths")
    add_parser.add_argument("--description", required=True, help="Test description")
    add_parser.add_argument("--component", required=True, help="Component section name")
    
    # Update mapping command
    update_parser = subparsers.add_parser("update-mapping", help="Update an existing mapping")
    update_parser.add_argument("--source", required=True, help="Source file path")
    update_parser.add_argument("--description", help="New test description")
    update_parser.add_argument("--tests", nargs="+", help="New test file paths")
    
    # Add dependency command
    dep_parser = subparsers.add_parser("add-dependency", help="Add a new test dependency")
    dep_parser.add_argument("--change-type", required=True, help="Change type section")
    dep_parser.add_argument("--dependency", required=True, help="Test dependency path")
    dep_parser.add_argument("--description", help="Dependency description")
    
    # Validate command
    subparsers.add_parser("validate", help="Validate TEST_INDEX.md format")
    
    args = parser.parse_args()
    
    updater = TestIndexUpdater()
    
    if args.command == "add-mapping":
        updater.add_mapping(args.source, args.tests, args.description, args.component)
    elif args.command == "update-mapping":
        updater.update_mapping(args.source, args.description, args.tests)
    elif args.command == "add-dependency":
        updater.add_dependency(args.change_type, args.dependency, args.description)
    elif args.command == "validate":
        if not updater.validate():
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 