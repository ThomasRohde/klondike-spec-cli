#!/usr/bin/env python3
"""Test the /api/commits endpoint."""

import subprocess
import time
import requests
import json

# Start server in background
print("Starting server...")
proc = subprocess.Popen(
    ["klondike", "serve", "--port", "8006"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Wait for server to start
time.sleep(3)

try:
    # Test endpoint
    print("\nTesting /api/commits endpoint...")
    response = requests.get("http://127.0.0.1:8006/api/commits?count=3")
    print(f"Status: {response.status_code}")
    commits = response.json()
    print(f"Commits returned: {len(commits)}")
    print(json.dumps(commits, indent=2))
    
    # Verify structure
    if commits:
        first = commits[0]
        assert "hash" in first, "Missing hash field"
        assert "author" in first, "Missing author field"
        assert "date" in first, "Missing date field"
        assert "message" in first, "Missing message field"
        print("\n✅ All required fields present")
    
    print("\n✅ Test passed!")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
finally:
    # Stop server
    proc.terminate()
    proc.wait(timeout=5)
    print("\nServer stopped")
