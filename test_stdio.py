#!/usr/bin/env python3
"""
Simple script to test the MCP server with stdio transport
"""
import asyncio
import json
import sys
import os

async def test_mcp_server():
    """Test MCP server with stdio transport"""
    # Set environment variables
    env = os.environ.copy()
    env.update({
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
    })

    # Start server
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        '-u',  # Unbuffered output
        'main.py',
        '--stdio',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )

    print("🚀 Starting server...")
    await asyncio.sleep(2)

    if process.returncode is not None:
        stderr = await process.stderr.read()
        print(f"❌ Server failed to start: {stderr.decode()}")
        return False

    try:
        async def read_response():
            """Read and parse JSON response from stdout"""
            while True:
                line = await process.stdout.readline()
                if not line:
                    return None
                line = line.decode().strip()
                if not line:
                    continue
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    # Skip non-JSON lines (like logs)
                    print(f"Skipping non-JSON line: {line[:100]}")
                    continue

        # Test initialize
        print("🔄 Testing initialize...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        request_json = json.dumps(init_request) + '\n'
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        # Read response with timeout
        try:
            response = await asyncio.wait_for(read_response(), timeout=15)
        except asyncio.TimeoutError:
            print("❌ Timeout waiting for initialize response")
            return False

        if response:
            print(f"✅ Initialize response: {json.dumps(response, indent=2)[:200]}")
        else:
            print("❌ No response for initialize")
            return False

        # Test initialized
        print("🔄 Testing initialized...")
        initialized_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "notifications/initialized"
        }

        request_json = json.dumps(initialized_request) + '\n'
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        response = await asyncio.wait_for(read_response(), timeout=15)
        print(f"✅ Initialized response: {json.dumps(response, indent=2)[:200]}")

        # Test list_tools
        print("🔄 Testing list_tools...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list"
        }

        request_json = json.dumps(list_tools_request) + '\n'
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        response = await asyncio.wait_for(read_response(), timeout=15)

        if response and 'result' in response and 'tools' in response['result']:
            tools = response['result']['tools']
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description'][:50]}")
            return True
        else:
            print("❌ Failed to get tools")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False

    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
        return False
    finally:
        # Cleanup
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

if __name__ == '__main__':
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)