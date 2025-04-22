# Volume Wall Detector MCP

A Model Context Protocol (MCP) server for analyzing stock trading volume and identifying significant price levels (volume walls).

## Features

- Fetch and store order book data
- Fetch and store trade data
- Analyze volume distribution at different price levels
- Identify significant price levels based on trading activity
- Track volume and value imbalances
- Support for regular and after-hours trading analysis

## Installation

```bash
npm install volume-wall-detector-mcp
```

## Configuration

Create a `.env` file with the following variables:

```env
TIMEZONE=GMT+7
API_BASE_URL=https://api.example.com
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=volume_wall_detector
MONGO_USER=admin
MONGO_PASSWORD=password
MONGO_AUTH_SOURCE=admin
MONGO_AUTH_MECHANISM=SCRAM-SHA-1
PAGE_SIZE=50
TRADES_TO_FETCH=10000
DAYS_TO_FETCH=1
TRANSPORT_TYPE=stdio
PORT=8080
```

## Available Tools

### fetch-order-book
Fetch current order book data for a symbol.

Parameters:
- `symbol`: Stock symbol to fetch order book for

### fetch-trades
Fetch recent trades for a symbol.

Parameters:
- `symbol`: Stock symbol to fetch trades for

### analyze-stock
Analyze stock data including volume and value analysis.

Parameters:
- `symbol`: Stock symbol to analyze
- `days`: Number of days to analyze (optional)

## Usage

```bash
# Start the server
npm start

# Or in development mode
npm run dev
```

## Development

```bash
# Install dependencies
npm install

# Run tests
npm test

# Build the project
npm run build
```

## License

ISC 