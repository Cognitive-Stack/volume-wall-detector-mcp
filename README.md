[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/cognitive-stack-volume-wall-detector-mcp-badge.png)](https://mseep.ai/app/cognitive-stack-volume-wall-detector-mcp)

# Volume Wall Detector MCP Server 📊

> 🔌 **Compatible with Cline, Cursor, Claude Desktop, and any other MCP Clients!**
> 
> Volume Wall Detector MCP works seamlessly with any MCP client

<p align="center">
  <img src="vld-logo.png" width="300" alt="VLD Logo">
</p>

The Model Context Protocol (MCP) is an open standard that enables AI systems to interact seamlessly with various data sources and tools, facilitating secure, two-way connections.

The Volume Wall Detector MCP server provides:

* Real-time stock trading volume analysis
* Detection of significant price levels (volume walls)
* Trading imbalance tracking and analysis
* After-hours trading analysis
* MongoDB-based data persistence

## Prerequisites 🔧

Before you begin, ensure you have:

* MongoDB instance running
* Stock market API access
* Node.js (v20 or higher)
* Git installed (only needed if using Git installation method)

## Volume Wall Detector MCP Server Installation ⚡

### Running with NPX

```bash
npx -y volume-wall-detector-mcp@latest
```

### Installing via Smithery

To install Volume Wall Detector MCP Server for Claude Desktop automatically via Smithery:

```bash
npx -y @smithery/cli install volume-wall-detector-mcp --client claude
```

## Configuring MCP Clients ⚙️

### Configuring Cline 🤖

1. Open the Cline MCP settings file:
```bash
# For macOS:
code ~/Library/Application\ Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json

# For Windows:
code %APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

2. Add the Volume Wall Detector server configuration:
```json
{
  "mcpServers": {
    "volume-wall-detector-mcp": {
      "command": "npx",
      "args": ["-y", "volume-wall-detector-mcp@latest"],
      "env": {
        "TIMEZONE": "GMT+7",
        "API_BASE_URL": "your-api-url-here",
        "MONGO_HOST": "localhost",
        "MONGO_PORT": "27017",
        "MONGO_DATABASE": "volume_wall_detector",
        "MONGO_USER": "admin",
        "MONGO_PASSWORD": "password",
        "MONGO_AUTH_SOURCE": "admin",
        "MONGO_AUTH_MECHANISM": "SCRAM-SHA-1",
        "PAGE_SIZE": "50",
        "TRADES_TO_FETCH": "10000",
        "DAYS_TO_FETCH": "1",
        "TRANSPORT_TYPE": "stdio",
        "PORT": "8080"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Configuring Cursor 🖥️

> **Note**: Requires Cursor version 0.45.6 or higher

1. Open Cursor Settings
2. Navigate to Open MCP
3. Click on "Add New Global MCP Server"
4. Fill out the following information:
   * **Name**: "volume-wall-detector-mcp"
   * **Type**: "command"
   * **Command**:
   ```bash
   env TIMEZONE=GMT+7 API_BASE_URL=your-api-url-here MONGO_HOST=localhost MONGO_PORT=27017 MONGO_DATABASE=volume_wall_detector MONGO_USER=admin MONGO_PASSWORD=password MONGO_AUTH_SOURCE=admin MONGO_AUTH_MECHANISM=SCRAM-SHA-1 PAGE_SIZE=50 TRADES_TO_FETCH=10000 DAYS_TO_FETCH=1 npx -y volume-wall-detector-mcp@latest
   ```

### Configuring Claude Desktop 🖥️

Create or edit the Claude Desktop configuration file:

#### For macOS:
```bash
code "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

#### For Windows:
```bash
code %APPDATA%\Claude\claude_desktop_config.json
```

Add the configuration:
```json
{
  "mcpServers": {
    "volume-wall-detector-mcp": {
      "command": "npx",
      "args": ["-y", "volume-wall-detector-mcp@latest"],
      "env": {
        "TIMEZONE": "GMT+7",
        "API_BASE_URL": "your-api-url-here",
        "MONGO_HOST": "localhost",
        "MONGO_PORT": "27017",
        "MONGO_DATABASE": "volume_wall_detector",
        "MONGO_USER": "admin",
        "MONGO_PASSWORD": "password",
        "MONGO_AUTH_SOURCE": "admin",
        "MONGO_AUTH_MECHANISM": "SCRAM-SHA-1",
        "PAGE_SIZE": "50",
        "TRADES_TO_FETCH": "10000",
        "DAYS_TO_FETCH": "1",
        "TRANSPORT_TYPE": "stdio",
        "PORT": "8080"
      }
    }
  }
}
```

## License

MIT 