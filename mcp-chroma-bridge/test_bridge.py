#!/usr/bin/env python3
"""Test script for MCP Chroma Bridge"""

import json
import subprocess
import sys

def send_message(proc, message):
    """Send a message to the bridge process"""
    proc.stdin.write(json.dumps(message) + '\n')
    proc.stdin.flush()
    
def read_response(proc):
    """Read a response from the bridge process"""
    line = proc.stdout.readline()
    if line:
        return json.loads(line.strip())
    return None

def test_bridge(remote_url, auth_token=None):
    """Test the bridge with basic operations"""
    cmd = [
        sys.executable, 
        "mcp_chroma_bridge.py",
        "--remote-url", remote_url
    ]
    if auth_token:
        cmd.extend(["--auth-token", auth_token])
        
    print(f"Starting bridge connecting to {remote_url}...")
    
    # Start the bridge process
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Test 1: Initialize
        print("\n1. Testing initialize...")
        send_message(proc, {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {}
            },
            "id": 1
        })
        response = read_response(proc)
        print(f"Response: {json.dumps(response, indent=2)}")
        
        # Test 2: List tools
        print("\n2. Testing tools/list...")
        send_message(proc, {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        })
        response = read_response(proc)
        print(f"Response: {json.dumps(response, indent=2)}")
        
        # Test 3: List collections
        print("\n3. Testing chroma_list_collections...")
        send_message(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "chroma_list_collections",
                "arguments": {}
            },
            "id": 3
        })
        response = read_response(proc)
        print(f"Response: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()
        proc.wait()
        
if __name__ == "__main__":
    # Update this URL to your actual Chroma MCP deployment
    REMOTE_URL = "https://chroma-mcp-development.up.railway.app"
    AUTH_TOKEN = "gi9v25dw33k086falw1c1i5m55b2uynt"
    
    test_bridge(REMOTE_URL, AUTH_TOKEN)