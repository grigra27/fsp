#!/usr/bin/env python
"""
Script to remove .map file references from CSS files
Run this before collectstatic if you have issues with missing .map files
"""
import os
import re
import sys
from pathlib import Path

def fix_css_files(static_dir):
    """Remove sourceMappingURL comments from CSS files"""
    css_files = list(Path(static_dir).glob('**/*.css'))
    map_pattern = re.compile(r'\s*/\*#\s*sourceMappingURL=.*?\*/')
    
    print(f"Found {len(css_files)} CSS files to process")
    
    for css_file in css_files:
        print(f"Processing {css_file}...")
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove sourceMappingURL comments
            new_content = map_pattern.sub('', content)
            
            if content != new_content:
                with open(css_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Removed .map references from {css_file}")
            else:
                print(f"ℹ️ No .map references found in {css_file}")
                
        except Exception as e:
            print(f"❌ Error processing {css_file}: {e}")
    
    print("\n✅ CSS files processed successfully!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        static_dir = sys.argv[1]
    else:
        # Default to static_dev directory
        base_dir = Path(__file__).resolve().parent.parent
        static_dir = base_dir / 'static_dev'
    
    if not os.path.exists(static_dir):
        print(f"❌ Directory not found: {static_dir}")
        sys.exit(1)
        
    print(f"Processing CSS files in {static_dir}")
    fix_css_files(static_dir)