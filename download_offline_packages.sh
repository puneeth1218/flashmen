#!/bin/bash
set -e

echo "Creating offline package directories..."
mkdir -p offline_packages/python
mkdir -p offline_packages/npm

echo "Downloading Python dependencies..."
# Use pip download to fetch wheels for the requirements
pip download -r backend/requirements.txt -d offline_packages/python

echo "Populating npm cache..."
# Use npm to install and cache packages locally
cd frontend
npm install --cache ../offline_packages/npm

echo "Offline packages have been downloaded successfully."
