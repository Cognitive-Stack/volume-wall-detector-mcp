"use strict";

import { z } from "zod";
import { FastMCP } from "fastmcp";

export type ToolConfig = {
  name: string;
  description: string;
  parameters: z.ZodObject<any>;
  execute: (args: any) => Promise<string>;
};

export type Tool = FastMCP["addTool"];

// Data Models
export const OrderBookLevelSchema = z.object({
  price: z.number(),
  volume: z.number()
});

export const OrderBookSchema = z.object({
  symbol: z.string(),
  timestamp: z.string(),
  match_price: z.number(),
  bid_1: OrderBookLevelSchema,
  ask_1: OrderBookLevelSchema,
  change_percent: z.number(),
  volume: z.number()
});

export const TradeSchema = z.object({
  trade_id: z.string(),
  symbol: z.string(),
  price: z.number(),
  volume: z.number(),
  side: z.enum(["bu", "sd", "after-hour"]),
  time: z.number()
});

export const PriceVolumeDataSchema = z.object({
  buy_volume: z.number().default(0),
  sell_volume: z.number().default(0),
  after_hour_buy: z.number().default(0),
  after_hour_sell: z.number().default(0),
  after_hour_unknown: z.number().default(0),
  buy_value: z.number().default(0),
  sell_value: z.number().default(0),
  after_hour_buy_value: z.number().default(0),
  after_hour_sell_value: z.number().default(0),
  after_hour_unknown_value: z.number().default(0),
  total_volume: z.number().default(0),
  total_value: z.number().default(0),
  volume_imbalance: z.number().default(0),
  value_imbalance: z.number().default(0),
  total_trades: z.number().default(0),
  last_trade_time: z.string().optional()
});

export type OrderBookLevel = z.infer<typeof OrderBookLevelSchema>;
export type OrderBook = z.infer<typeof OrderBookSchema>;
export type Trade = z.infer<typeof TradeSchema>;
export type PriceVolumeData = z.infer<typeof PriceVolumeDataSchema>; 