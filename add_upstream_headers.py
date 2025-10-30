#!/usr/bin/env python3
"""
Script to automatically add X-Upstream-Target headers after proxy_pass directives in nginx config files.

Usage:
    python add_upstream_headers.py [directory]
    
    If no directory is specified, searches for all .conf files in current directory and subdirectories.
"""

import os
import re
import sys
from pathlib import Path


def extract_proxy_url(line):
    """Extract the URL from a proxy_pass directive."""
    # Match proxy_pass http://backend:5001/; or similar patterns
    match = re.search(r'proxy_pass\s+(https?://[^;]+);', line)
    if match:
        url = match.group(1)
        # Remove trailing slash if present
        url = url.rstrip('/')
        # Remove protocol prefix for cleaner header
        url = re.sub(r'^https?://', '', url)
        return url
    return None


def get_indentation(line):
    """Get the indentation (spaces/tabs) from a line."""
    match = re.match(r'^(\s*)', line)
    return match.group(1) if match else ''


def has_upstream_target_header(lines, start_idx, indentation):
    """Check if X-Upstream-Target header already exists after the proxy_pass line."""
    # Look ahead a few lines to see if the header already exists
    for i in range(start_idx + 1, min(start_idx + 5, len(lines))):
        if 'X-Upstream-Target' in lines[i]:
            return True
        # Stop searching if we hit a closing brace or another directive
        if re.match(r'^\s*\}', lines[i]) or re.match(r'^\s*proxy_', lines[i]):
            break
    return False


def safe_print(text):
    """Print text safely, handling encoding issues on Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: encode with replacement for incompatible characters
        print(text.encode('ascii', 'replace').decode('ascii'))


def process_nginx_conf(filepath, dry_run=False):
    """Process a single nginx.conf file and add X-Upstream-Target headers."""
    safe_print(f"\n[*] Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    i = 0
    changes_made = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check if this line contains proxy_pass
        if 'proxy_pass' in line and not line.strip().startswith('#'):
            proxy_url = extract_proxy_url(line)
            
            if proxy_url:
                indentation = get_indentation(line)
                
                # Check if X-Upstream-Target header already exists nearby
                if has_upstream_target_header(lines, i, indentation):
                    safe_print(f"  [SKIP] Line {i+1}: X-Upstream-Target already exists for {proxy_url}")
                else:
                    # Add the X-Upstream-Target header
                    header_line = f'{indentation}proxy_set_header X-Upstream-Target "{proxy_url}";\n'
                    new_lines.append(header_line)
                    modified = True
                    changes_made += 1
                    safe_print(f"  [ADD] Line {i+1}: Added X-Upstream-Target for {proxy_url}")
        
        i += 1
    
    if modified:
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            safe_print(f"  [SAVED] {changes_made} change(s) to {filepath}")
        else:
            safe_print(f"  [DRY RUN] Would save {changes_made} change(s) to {filepath}")
        return changes_made
    else:
        safe_print(f"  [INFO] No changes needed")
        return 0


def find_nginx_configs(directory):
    """Find all nginx configuration files (.conf) in the directory and subdirectories."""
    nginx_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.conf'):
                nginx_files.append(os.path.join(root, file))
    
    return nginx_files


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Add X-Upstream-Target headers after proxy_pass directives in nginx config files (.conf)'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to search for nginx config files (.conf) (default: current directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually modifying files'
    )
    parser.add_argument(
        '--file',
        help='Process a specific file instead of searching directory'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        safe_print("[DRY RUN MODE] No files will be modified\n")
    
    if args.file:
        # Process a specific file
        if not os.path.isfile(args.file):
            safe_print(f"[ERROR] File not found: {args.file}")
            sys.exit(1)
        
        total_changes = process_nginx_conf(args.file, dry_run=args.dry_run)
    else:
        # Search directory for nginx config files
        if not os.path.isdir(args.directory):
            safe_print(f"[ERROR] Directory not found: {args.directory}")
            sys.exit(1)
        
        safe_print(f"[SEARCH] Searching for nginx config files (.conf) in: {args.directory}")
        nginx_files = find_nginx_configs(args.directory)
        
        if not nginx_files:
            safe_print(f"[ERROR] No .conf files found in {args.directory}")
            sys.exit(1)
        
        safe_print(f"[FOUND] {len(nginx_files)} config file(s)")
        
        total_changes = 0
        for nginx_file in nginx_files:
            changes = process_nginx_conf(nginx_file, dry_run=args.dry_run)
            total_changes += changes
    
    safe_print(f"\n{'='*60}")
    if args.dry_run:
        safe_print(f"[DRY RUN] Would make {total_changes} total change(s)")
    else:
        safe_print(f"[COMPLETE] Made {total_changes} total change(s)")
    safe_print(f"{'='*60}\n")


if __name__ == '__main__':
    main()

