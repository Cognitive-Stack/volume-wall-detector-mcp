#!/usr/bin/env node
"use strict";

import { FastMCP } from "fastmcp";
import { tools } from "./services/tools";
import { Tool } from "./types/tools";
import { getConfig } from "./config/env";

const config = getConfig();

const server = new FastMCP({
  name: "Volume Wall Detector MCP",
  version: "1.0.0"
});

// Register all tools
tools.forEach((tool) => {
  (server.addTool as Tool)(tool);
});

// Start server with appropriate transport
if (config.TRANSPORT_TYPE === "sse") {
  server.start({
    transportType: "sse",
    sse: {
      endpoint: "/sse",
      port: parseInt(config.PORT, 10)
    }
  });
} else {
  server.start({
    transportType: "stdio"
  });
} 