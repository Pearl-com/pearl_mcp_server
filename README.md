# Pearl MCP Server

A Model Context Protocol (MCP) server implementation that exposes Pearl's AI and Expert services through a standardized interface. This server allows MCP clients like Claude Desktop, Cursor, and other MCP-compatible applications to interact with [Pearl's advanced AI assistants and human experts](https://www.pearl.com/post/download-this-free-whitepaper-now-beyond-ai-how-pearl-s-mcp-server-bridges-your-ai-agents-with-re).

## Features

- Support for both stdio and SSE transports
- Integration with Pearl API for AI and expert assistance
- Session management for continuous conversations
- Multiple interaction modes:
  - AI-only mode for quick automated responses
  - AI-Expert mode for AI-assisted human expert support
  - Expert mode for direct human expert assistance
- Conversation history tracking
- Stateful session management

## Prerequisites

- Python 3.12 or higher
- Pearl API Key (Contact [Pearl](https://www.pearl.com/contact) to obtain your API key)
- pip or uv package manager

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Pearl-com/pearl_mcp_server.git
cd pearl_mcp_server
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

## Configuration

1. Create a `.env` file in the src directory:
```env
PEARL_API_KEY=your-api-key-here
```

## Running the Server

### Local Development

Start the server using either stdio (default) or SSE transport:

```bash
# Using stdio transport (default)
pearl-mcp-server --api-key your-api-key

# Using SSE transport on custom port
pearl-mcp-server --api-key your-api-key --transport sse --port 8000
```

### Using Remote Server

Pearl provides a hosted MCP server at:
```
https://pearl-api-mcp-server.pearlapi.workers.dev/sse
```

This can be used directly with any MCP client without installing the Python application locally.

## Available Tools

The server provides the following tools:

1. `ask_pearl_ai`
   - Quick AI-only responses without human review
   - Best for general inquiries and non-critical situations
   - Parameters:
     - `question`: The user's query
     - `chat_history` (optional): Previous conversation context
     - `session_id` (optional): For continuing conversations

2. `ask_pearl_expert`
   - AI-assisted human expert support
   - Best for complex topics requiring expert verification
   - Parameters: Same as ask_pearl_ai

3. `ask_expert`
   - Direct human expert assistance
   - Best for complex or sensitive topics
   - Parameters: Same as ask_pearl_ai

4. `get_conversation_status`
   - Check the status of an active conversation
   - Parameter: `session_id`

5. `get_conversation_history`
   - Retrieve full conversation history
   - Parameter: `session_id`

## Expert Categories

Pearl's MCP server provides access to a wide range of expert categories. The appropriate expert category is automatically determined by Pearl's API based on the context of your query, ensuring you're connected with the most relevant expert for your needs.

Here are the main categories of expertise available:

- **Medical & Healthcare**
  - General Medicine
  - Dental Health
  - Mental Health
  - Nutrition & Diet
  - Fitness & Exercise
  - Veterinary Medicine

- **Legal & Financial**
  - Legal Advice
  - Tax Consultation
  - Financial Planning
  - Business Law
  - Employment Law
  - Real Estate Law

- **Technical & Professional**
  - Software Development
  - IT Support
  - Computer Repair
  - Electronics
  - Mechanical Engineering
  - Home Improvement

- **Education & Career**
  - Academic Tutoring
  - Career Counseling
  - Resume Writing
  - Test Preparation
  - College Admissions
  - Professional Development

- **Lifestyle & Personal**
  - Relationship Advice
  - Parenting
  - Pet Care
  - Personal Styling
  - Interior Design
  - Travel Planning

Each expert category can be accessed through the `ask_expert` or `ask_pearl_expert` tools. You don't need to specify the category - simply describe your question or problem, and Pearl's AI will automatically route your request to the most appropriate expert type based on the context.

## Connecting with MCP Clients

### Local Connection (stdio transport)

For connecting to a local MCP server using stdio transport, add the following configuration to your MCP client:

```json
{
    "pearl-mcp-server": {
        "type": "stdio",
        "command": "pearl-mcp-server",
        "args": ["--api-key", "your-api-key"],
        "env": {
            "PEARL_API_KEY": "Your Pearl Api Key"
        }
    }
}
```

### Remote Connection using mcp-remote

Some MCP clients don't support direct connection to remote MCP servers. For these clients, you can use the `mcp-remote` package as a bridge:

1. Prerequisites:
   - Node.js 18 or higher
   - npm (Node Package Manager)

2. Configuration for remote server:
```json
{
    "mcpServers": {
        "pearl-remote": {
            "command": "npx",
            "args": [
                "mcp-remote",
                "https://pearl-api-mcp-server.pearlapi.workers.dev/sse"
            ]
        }
    }
}
```

3. Configuration file locations:
   - Claude Desktop:
     - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
     - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Cursor: `~/.cursor/mcp.json`
   - Windsurf: `~/.codeium/windsurf/mcp_config.json`

4. Additional Options:
   - Force latest version: Add `@latest` to npx command
   ```json
   "args": ["mcp-remote@latest", "https://pearl-api-mcp-server.pearlapi.workers.dev/sse"]
   ```
   

5. Troubleshooting:
   - Clear stored credentials: `rm -rf ~/.mcp-auth`
   - View logs:
     - Windows (PowerShell): `Get-Content "$env:APPDATA\Claude\Logs\mcp.log" -Wait -Tail 20`
     - macOS/Linux: `tail -n 20 -F ~/Library/Logs/Claude/mcp*.log`
   - Test connection: `npx mcp-remote-client https://pearl-api-mcp-server.pearlapi.workers.dev/sse`

### Custom Python Client

```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def main():
    # For stdio transport
    async with stdio_client(
        StdioServerParameters(command="pearl-mcp-server", args=["--api-key", "your-api-key"])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(tools)
            
            # Call Pearl AI
            result = await session.call_tool(
                "ask_pearl_ai", 
                {
                    "question": "What is MCP?",
                    "session_id": "optional-session-id"
                }
            )
            print(result)

asyncio.run(main())
```

## API Key

To obtain a Pearl API key for using this server:

1. Visit [Pearl Contact Page](https://www.pearl.com/contact)
2. Request an API key for MCP server integration
3. Follow the provided instructions to complete the registration process

Keep your API key secure and never commit it to version control.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.