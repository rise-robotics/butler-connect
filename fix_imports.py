#!/usr/bin/env python3
"""
Fix import paths in Butler Connect project
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix src.* imports in a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace src.* imports with relative imports
        patterns = [
            (r'from src\.core\.', 'from core.'),
            (r'from src\.web\.', 'from web.'),
            (r'from src\.utils\.', 'from utils.'),
            (r'from src\.safety\.', 'from safety.'),
            (r'from src\.monitoring\.', 'from monitoring.'),
            (r'from src\.control\.', 'from control.'),
        ]
        
        modified = False
        for old_pattern, new_pattern in patterns:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_pattern, content)
                modified = True
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in {filepath}")
        else:
            print(f"⚪ No changes needed in {filepath}")
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")

def main():
    """Fix all Python files in the src directory"""
    src_dir = Path("src")
    
    if not src_dir.exists():
        print("❌ src directory not found")
        return
    
    print("🔧 Fixing import paths in Butler Connect project...")
    
    # Find all Python files
    python_files = list(src_dir.rglob("*.py"))
    
    for py_file in python_files:
        fix_imports_in_file(py_file)
    
    print(f"✅ Processed {len(python_files)} Python files")

if __name__ == "__main__":
    main()
