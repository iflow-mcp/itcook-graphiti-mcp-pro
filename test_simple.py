#!/usr/bin/env python3
"""Simple test script"""
import subprocess
import json
import time

# Start the server
env = {
    'NEO4J_URI': 'bolt://localhost:7687',
    'NEO4J_USER': 'neo4j',
    'NEO4J_PASSWORD': 'test_password',
    'LLM_BASE_URL': 'https://api.openai.com/v1',
    'LLM_API_KEY': 'sk-test-key',
    'LLM_MODEL_NAME': 'gpt-4',
    'LLM_TEMPERATURE': '0.0',
    'SMALL_LLM_BASE_URL': 'https://api.openai.com/v1',
    'SMALL_LLM_API_KEY': 'sk-test-key',
    'SMALL_LLM_MODEL_NAME': 'gpt-3.5-turbo',
    'EMBEDDING_BASE_URL': 'https://api.openai.com/v1',
    'EMBEDDING_API_KEY': 'sk-test-key',
    'EMBEDDING_MODEL_NAME': 'text-embedding-ada-002',
    'SEMAPHORE_LIMIT': '20',
    'MCP_TRANSPORT': 'stdio',
    'PYTHONUNBUFFERED': '1',
}

import os
env.update(os.environ)

proc = subprocess.Popen(
    ["/app/auto-mcp-upload/.venv/bin/python", "-u", "main.py", "--stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
    cwd="/app/auto-mcp-upload/data/5782"
)

print("🚀 Server started, PID:", proc.pid)
time.sleep(2)

# Check if server is still running
if proc.poll() is not None:
    print("❌ Server exited early")
    print("STDERR:", proc.stderr.read().decode())
    exit(1)

# Send initialize request
init_req = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
}

print("📤 Sending initialize request...")
proc.stdin.write((json.dumps(init_req) + "\n").encode())
proc.stdin.flush()

# Read all output
try:
    # Wait a bit for response
    time.sleep(1)

    # Check if server is still running
    if proc.poll() is not None:
        print("❌ Server exited after request")
        print("STDOUT:", proc.stdout.read().decode())
        print("STDERR:", proc.stderr.read().decode())
        exit(1)

    # Try to read response
    import select
    if select.select([proc.stdout], [], [], 0.1)[0]:
        line = proc.stdout.readline().decode().strip()
        if line:
            response = json.loads(line)
            print("✅ Response:", json.dumps(response, indent=2)[:200])
        else:
            print("❌ Empty response")
    else:
        print("❌ No data available to read")

    # Send list_tools request
    tools_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }

    print("📤 Sending list_tools request...")
    proc.stdin.write((json.dumps(tools_req) + "\n").encode())
    proc.stdin.flush()

    time.sleep(1)

    if proc.poll() is not None:
        print("❌ Server exited after list_tools request")
        print("STDOUT:", proc.stdout.read().decode())
        print("STDERR:", proc.stderr.read().decode())
        exit(1)

    if select.select([proc.stdout], [], [], 0.1)[0]:
        line = proc.stdout.readline().decode().strip()
        if line:
            response = json.loads(line)
            if 'result' in response and 'tools' in response['result']:
                tools = response['result']['tools']
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool['name']}")
            else:
                print("❌ No tools in response")
        else:
            print("❌ Empty response")
    else:
        print("❌ No data available to read")

except Exception as e:
    print("❌ Error:", e)
    print("STDOUT:", proc.stdout.read().decode())
    print("STDERR:", proc.stderr.read().decode())

# Cleanup
proc.terminate()
try:
    proc.wait(timeout=5)
except:
    proc.kill()
    proc.wait()
