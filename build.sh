#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download and Extract ExifTool (Unix Version)
# We put it in a 'bin' folder within our project
mkdir -p bin
curl -L https://exiftool.org/Image-ExifTool-13.54.tar.gz | tar -xz -C bin --strip-components=1

# 3. Make the exiftool script executable
chmod +x bin/exiftool