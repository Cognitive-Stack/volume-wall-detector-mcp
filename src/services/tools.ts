import { z } from "zod";
import { ToolConfig } from "../types/tools";
import { analyzeVolumeWalls } from "../tools/analyze-volume-walls";
import { fetchOrderBook, fetchTrades } from "./api";
import { storeStockData } from "./mongodb";

export const tools: ToolConfig[] = [
  {
    name: "fetch-order-book",
    description: "Fetch current order book data for a symbol",
    parameters: z.object({
      symbol: z.string().describe("Stock symbol to fetch order book for")
    }),
    execute: async (args) => {
      const orderBook = await fetchOrderBook(args.symbol);
      const result = await storeStockData(orderBook, "order_books");
      return JSON.stringify(result);
    }
  },
  {
    name: "fetch-trades",
    description: "Fetch recent trades for a symbol",
    parameters: z.object({
      symbol: z.string().describe("Stock symbol to fetch trades for")
    }),
    execute: async (args) => {
      const trades = await fetchTrades(args.symbol);
      const result = await storeStockData(trades, "trades");
      return JSON.stringify(result);
    }
  },
  {
    name: "analyze-stock",
    description: "Analyze stock data including volume and value analysis",
    parameters: z.object({
      symbol: z.string().describe("Stock symbol to analyze"),
      days: z.number().optional().describe("Number of days to analyze (optional)")
    }),
    execute: async (args) => {
      const result = await analyzeVolumeWalls(args.symbol, args.days);
      return JSON.stringify(result);
    }
  }
]; 