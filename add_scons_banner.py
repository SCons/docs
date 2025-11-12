#!/usr/bin/env python3
import os
import sys
import re
from packaging import version  # for comparing version directories safely

# HTML banner to insert
BANNER_HTML = """<div style="background-color:#ffcccc; border:2px solid red; padding:10px; margin-bottom:10px; font-family:sans-serif;">
<strong>Notice:</strong> This document is for an old version of SCons that is no longer supported. 
You should upgrade, and read the 
<a href="https://scons.org/doc/production/HTML/scons-man.html" target="_blank">
SCons documentation for the current stable release</a>.
</div>
"""

# Match directories like 4.7.2, 3.0, 3.1.1-beta, etc.
VERSION_DIR_PATTERN = re.compile(r"^\d+\.\d+(?:\.\d+.*)?$")


def parse_version_string(s):
    """Safely parse version strings for comparison; non-parsable ones return None."""
    try:
        return version.parse(s)
    except Exception:
        return None


def add_banner_to_html_file(filepath):
    """Insert the warning banner at the top of the HTML body or file, handling encoding issues."""
    encodings_to_try = ["utf-8", "latin-1", "windows-1252"]
    content = None
    encoding_used = None

    # Try reading file with fallback encodings
    for enc in encodings_to_try:
        try:
            with open(filepath, "r", encoding=enc) as f:
                content = f.read()
            encoding_used = enc
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        print(f"❌ Could not decode file with any known encoding: {filepath}")
        return

    # Skip if banner already added
    if "SCons documentation for the current stable release" in content:
        return  # silently skip

    # Insert before <body> tag if present, else prepend
    if "<body" in content:
        parts = content.split("<body", 1)
        before_body = parts[0]
        body_and_rest = "<body" + parts[1]
        content = before_body + body_and_rest.replace(">", ">\n" + BANNER_HTML, 1)
    else:
        content = BANNER_HTML + "\n" + content

    # Write file back with same encoding
    try:
        with open(filepath, "w", encoding=encoding_used) as f:
            f.write(content)
    except Exception as e:
        print(f"❌ Error writing {filepath}: {e}")


def process_directory(root_dir):
    """Find version directories, exclude the latest, and add banners to HTML files."""
    version_dirs = []
    for entry in os.listdir(root_dir):
        entry_path = os.path.join(root_dir, entry)
        if os.path.isdir(entry_path) and VERSION_DIR_PATTERN.match(entry):
            version_dirs.append(entry)
        else:
            print(f"Skipping non-version directory: {entry}")

    if not version_dirs:
        print("No version directories found.")
        return

    # Determine the highest version
    parsed_versions = [(d, parse_version_string(d)) for d in version_dirs]
    parsed_versions = [(d, v) for d, v in parsed_versions if v is not None]
    if parsed_versions:
        latest_version_dir = max(parsed_versions, key=lambda x: x[1])[0]
        print(f"Excluding latest version directory: {latest_version_dir}")
    else:
        latest_version_dir = None

    for vdir in version_dirs:
        if vdir == latest_version_dir:
            continue
        for dirpath, _, filenames in os.walk(os.path.join(root_dir, vdir)):
            for filename in filenames:
                if filename.lower().endswith(".html"):
                    add_banner_to_html_file(os.path.join(dirpath, filename))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 add_scons_banner.py <root_directory>")
        sys.exit(1)

    root_directory = sys.argv[1]
    if not os.path.isdir(root_directory):
        print(f"Error: {root_directory} is not a valid directory.")
        sys.exit(1)

    process_directory(root_directory)
