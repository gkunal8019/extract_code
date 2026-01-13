import re
import ast
from pathlib import Path
from typing import Set, Dict, List
from collections import defaultdict

def parse_imports_with_names(file_path):
    """Extract what is imported from each module."""
    imports = {}  # {module: [names]}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module
                    names = [alias.name for alias in node.names]
                    if module not in imports:
                        imports[module] = []
                    imports[module].extend(names)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name] = ['*']  # Import entire module
    
    except Exception as e:
        print(f"[WARNING] Could not parse {file_path}: {e}")
    
    return imports

def extract_function_or_class(file_path, name):
    """Extract a specific function or class definition from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            tree = ast.parse(content)
        
        lines = content.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if node.name == name:
                    # Get line numbers
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if node.end_lineno else start_line + 1
                    
                    # Extract the code
                    code_lines = lines[start_line:end_line]
                    return '\n'.join(code_lines)
        
        return None
    
    except Exception as e:
        print(f"[WARNING] Could not extract {name} from {file_path}: {e}")
        return None

def get_global_variables(file_path):
    """Extract global variables and imports from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.splitlines()
        globals_code = []
        
        tree = ast.parse(content)
        
        # Get all top-level assignments and imports
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign)):
                start = node.lineno - 1
                end = node.end_lineno if node.end_lineno else start + 1
                globals_code.extend(lines[start:end])
        
        return '\n'.join(globals_code) if globals_code else ""
    
    except Exception as e:
        return ""

def resolve_import_to_file(import_name, project_dir):
    """Convert import name to file path."""
    path = import_name.replace('.', '/')
    
    py_file = project_dir / f"{path}.py"
    if py_file.exists():
        return py_file
    
    init_file = project_dir / path / "__init__.py"
    if init_file.exists():
        return init_file
    
    return None

def build_tree_structure(files, project_dir):
    """Build a tree structure from file paths."""
    tree = {}
    
    for file_path in files:
        rel_path = file_path.relative_to(project_dir)
        parts = rel_path.parts
        
        current = tree
        for i, part in enumerate(parts):
            if part not in current:
                # Check if this is the last part (file)
                is_file = (i == len(parts) - 1)
                current[part] = {'_is_file': is_file, '_children': {}}
            current = current[part]['_children']
    
    return tree

def print_tree(tree, prefix="", is_last=True, max_files_per_dir=8):
    """Print tree structure with proper formatting."""
    items = sorted(tree.items(), key=lambda x: (not x[1]['_is_file'], x[0]))
    
    for idx, (name, data) in enumerate(items):
        is_last_item = (idx == len(items) - 1)
        
        # Determine connector
        if is_last_item:
            connector = "└── "
            extension = "    "
        else:
            connector = "├── "
            extension = "│   "
        
        # Print current item
        if data['_is_file']:
            print(f"{prefix}{connector}📄 {name}")
        else:
            # Count files in this directory
            child_count = len(data['_children'])
            print(f"{prefix}{connector}📁 {name}/")
            
            # If more than max_files, show truncated
            if child_count > max_files_per_dir:
                # Show first max_files items
                shown_items = list(data['_children'].items())[:max_files_per_dir]
                for child_name, child_data in shown_items:
                    child_prefix = prefix + extension
                    if child_data['_is_file']:
                        print(f"{child_prefix}├── 📄 {child_name}")
                    else:
                        print(f"{child_prefix}├── 📁 {child_name}/")
                
                # Show ellipsis
                print(f"{child_prefix}├── ...")
                print(f"{child_prefix}└── (up to {child_count} files in this directory)")
            else:
                # Recursively print children
                print_tree(data['_children'], prefix + extension, is_last_item, max_files_per_dir)

def print_directory_structure(files, project_dir):
    """Print directory structure in tree format."""
    print("\n" + "="*80)
    print("PROJECT DIRECTORY STRUCTURE (TREE VIEW)")
    print("="*80)
    
    total_files = len(files)
    print(f"\nTotal Files to Extract: {total_files}")
    print(f"Project Root: {project_dir}\n")
    
    # Build tree
    tree = build_tree_structure(files, project_dir)
    
    # Print tree
    print(f"📁 {project_dir.name}/")
    print_tree(tree, prefix="", is_last=True, max_files_per_dir=8)
    
    print("\n" + "="*80 + "\n")

def print_file_locations(files, project_dir):
    """Print detailed file locations and paths."""
    print("="*80)
    print("DETAILED FILE LOCATIONS")
    print("="*80 + "\n")
    
    for idx, file_path in enumerate(sorted(files, key=lambda x: str(x)), 1):
        rel_path = file_path.relative_to(project_dir)
        abs_path = file_path.absolute()
        
        print(f"[{idx:02d}] {rel_path}")
        print(f"     Absolute: {abs_path}")
        print(f"     Directory: {file_path.parent.relative_to(project_dir) if file_path.parent != project_dir else '(root)'}")
        print()
    
    print("="*80 + "\n")

def discover_files(project_dir, entry_file, exclude_patterns):
    """First pass: discover all files that will be processed."""
    project_dir = Path(project_dir)
    entry_file = Path(entry_file)
    
    files_to_process = [(entry_file, ['*'])]
    processed = set()
    discovered_files = []
    
    while files_to_process:
        current_file, names_to_extract = files_to_process.pop(0)
        
        if current_file in processed:
            continue
        
        processed.add(current_file)
        
        # Check exclusions
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in str(current_file):
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        discovered_files.append(current_file)
        
        # Get imports from this file
        try:
            imports = parse_imports_with_names(current_file)
            
            # Process imports
            for module, names in imports.items():
                # Skip standard libraries
                if module in ['os', 'sys', 're', 'cv2', 'uuid', 'numpy', 'tensorflow', 
                              'PIL', 'flask', 'urllib', 'json', 'time', 'gc', 'io',
                              'paddleocr', 'ultralytics', 'torch', 'requests', 'certifi', 'urllib3']:
                    continue
                
                file_path = resolve_import_to_file(module, project_dir)
                if file_path and file_path not in processed:
                    files_to_process.append((file_path, names))
        except:
            pass
    
    return discovered_files

def extract_used_code(project_dir, entry_file, output_file, exclude_patterns=None):
    """Extract only the functions/classes that are actually used."""
    
    if exclude_patterns is None:
        exclude_patterns = []
    
    project_dir = Path(project_dir)
    entry_file = Path(entry_file)
    
    print("\n" + "="*80)
    print("SMART CODE EXTRACTION - ANALYSIS PHASE")
    print("="*80)
    print(f"\nProject Directory: {project_dir}")
    print(f"Entry Point: {entry_file.name}")
    print(f"Output File: {output_file}")
    print(f"Exclude Patterns: {', '.join(exclude_patterns)}")
    
    # PHASE 1: Discover all files
    print("\n[PHASE 1] Discovering all files that will be processed...")
    discovered_files = discover_files(project_dir, entry_file, exclude_patterns)
    
    # Print directory structure
    print_directory_structure(discovered_files, project_dir)
    
    # Print detailed locations
    print_file_locations(discovered_files, project_dir)
    
    # PHASE 2: Extract code
    print("="*80)
    print("EXTRACTION PHASE - Extracting code from discovered files")
    print("="*80 + "\n")
    
    files_to_process = [(entry_file, ['*'])]
    processed = set()
    extracted_code = {}
    
    while files_to_process:
        current_file, names_to_extract = files_to_process.pop(0)
        
        if current_file in processed:
            continue
        
        processed.add(current_file)
        
        # Check exclusions
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in str(current_file):
                print(f"[SKIP] {current_file.relative_to(project_dir)}")
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        print(f"[PROCESS] {current_file.relative_to(project_dir)}")
        
        # Get imports from this file
        imports = parse_imports_with_names(current_file)
        
        # Build code for this file
        file_code_parts = []
        
        # Add global variables and imports
        globals_code = get_global_variables(current_file)
        if globals_code:
            file_code_parts.append(globals_code)
        
        # Extract specific functions/classes or entire file
        if '*' in names_to_extract:
            # Import entire file
            with open(current_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            extracted_code[current_file] = content
            print(f"  → Extracted entire file")
        else:
            # Extract only specific names
            for name in names_to_extract:
                if name == '*':
                    continue
                code = extract_function_or_class(current_file, name)
                if code:
                    file_code_parts.append(f"\n{code}")
                    print(f"  → Extracted function/class: {name}")
                else:
                    print(f"  ⚠ Could not find: {name}")
            
            extracted_code[current_file] = '\n\n'.join(file_code_parts)
        
        # Process imports from this file
        for module, names in imports.items():
            # Skip standard libraries
            if module in ['os', 'sys', 're', 'cv2', 'uuid', 'numpy', 'tensorflow', 
                          'PIL', 'flask', 'urllib', 'json', 'time', 'gc', 'io',
                          'paddleocr', 'ultralytics', 'torch', 'requests', 'certifi', 'urllib3']:
                continue
            
            file_path = resolve_import_to_file(module, project_dir)
            if file_path and file_path not in processed:
                files_to_process.append((file_path, names))
    
    # Write output
    print(f"\n{'='*80}")
    print("WRITING OUTPUT FILE")
    print(f"{'='*80}\n")
    
    # Build tree for output file
    tree = build_tree_structure(extracted_code.keys(), project_dir)
    
    total_lines = 0
    with open(output_file, 'w', encoding='utf-8') as out:
        # Write header with file list
        out.write("="*80 + "\n")
        out.write("EXTRACTED FILES SUMMARY\n")
        out.write("="*80 + "\n\n")
        out.write(f"Total Files: {len(extracted_code)}\n")
        out.write(f"Project Root: {project_dir}\n\n")
        
        out.write("Directory Tree Structure:\n")
        out.write(f"📁 {project_dir.name}/\n")
        
        # Write tree to file
        def write_tree(tree_dict, prefix="", is_last=True):
            items = sorted(tree_dict.items(), key=lambda x: (not x[1]['_is_file'], x[0]))
            for idx, (name, data) in enumerate(items):
                is_last_item = (idx == len(items) - 1)
                connector = "└── " if is_last_item else "├── "
                extension = "    " if is_last_item else "│   "
                
                if data['_is_file']:
                    out.write(f"{prefix}{connector}📄 {name}\n")
                else:
                    out.write(f"{prefix}{connector}📁 {name}/\n")
                    write_tree(data['_children'], prefix + extension, is_last_item)
        
        write_tree(tree)
        out.write("\n" + "="*80 + "\n\n")
        
        # Write code
        for file_path, code in extracted_code.items():
            lines = len(code.splitlines())
            total_lines += lines
            
            out.write(f"\n{'='*60}\n")
            out.write(f"FILE: {file_path}\n")
            out.write(f"Relative Path: {file_path.relative_to(project_dir)}\n")
            out.write(f"Directory: {file_path.parent.relative_to(project_dir) if file_path.parent != project_dir else '(root)'}\n")
            out.write(f"Extracted Lines: {lines}\n")
            out.write(f"{'='*60}\n\n")
            out.write(code)
            out.write("\n\n")
            
            print(f"[ADDED] {file_path.relative_to(project_dir)} ({lines} lines)")
    
    print(f"\n{'='*80}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Extracted {len(extracted_code)} files with {total_lines} total lines")
    print(f"✓ Output written to: {output_file}")
    print(f"{'='*80}\n")

# Run the extraction
if __name__ == "__main__":
    extract_used_code(
        project_dir="/data/flaskapp/ocr2",
        entry_file="/data/flaskapp/ocr2/docker_app.py",
        output_file="smart_extracted_code.txt",
        exclude_patterns=["fine_tuned_model", "ocrEnv", "__pycache__"]
    )
