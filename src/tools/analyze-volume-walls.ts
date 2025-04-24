"use strict";

import { OrderBook, Trade, PriceVolumeData } from "../types/tools";
import { getConfig } from "../config/env";
import { getLatestOrderBook, getRecentTrades } from "../services/mongodb";

const config = getConfig();

export const analyzeVolumeAtPrice = (
  trades: Trade[],
  orderBook: OrderBook
): Record<number, PriceVolumeData> => {
  const priceVolumes: Record<number, PriceVolumeData> = {};
  
  for (const trade of trades.reverse()) {
    const price = trade.price;
    if (!priceVolumes[price]) {
      priceVolumes[price] = {
        buy_volume: 0,
        sell_volume: 0,
        after_hour_buy: 0,
        after_hour_sell: 0,
        after_hour_unknown: 0,
        buy_value: 0,
        sell_value: 0,
        after_hour_buy_value: 0,
        after_hour_sell_value: 0,
        after_hour_unknown_value: 0,
        total_volume: 0,
        total_value: 0,
        volume_imbalance: 0,
        value_imbalance: 0,
        total_trades: 0
      };
    }
    
    const data = priceVolumes[price];
    const value = trade.price * trade.volume;
    
    if (trade.side === "bu") {
      data.buy_volume += trade.volume;
      data.buy_value += value;
    } else if (trade.side === "sd") {
      data.sell_volume += trade.volume;
      data.sell_value += value;
    } else {
      if (trade.price >= orderBook.ask_1.price) {
        data.after_hour_buy += trade.volume;
        data.after_hour_buy_value += value;
      } else if (trade.price <= orderBook.bid_1.price) {
        data.after_hour_sell += trade.volume;
        data.after_hour_sell_value += value;
      } else {
        data.after_hour_unknown += trade.volume;
        data.after_hour_unknown_value += value;
      }
    }
    
    data.total_trades += 1;
    data.last_trade_time = new Date(trade.time * 1000).toISOString();
  }
  
  // Calculate totals and imbalances
  for (const data of Object.values(priceVolumes)) {
    data.total_volume = 
      data.buy_volume + 
      data.sell_volume + 
      data.after_hour_buy +
      data.after_hour_sell +
      data.after_hour_unknown;
      
    data.total_value = 
      data.buy_value + 
      data.sell_value + 
      data.after_hour_buy_value +
      data.after_hour_sell_value +
      data.after_hour_unknown_value;
      
    data.volume_imbalance = 
      (data.buy_volume + data.after_hour_buy) - 
      (data.sell_volume + data.after_hour_sell);
      
    data.value_imbalance = 
      (data.buy_value + data.after_hour_buy_value) - 
      (data.sell_value + data.after_hour_sell_value);
  }
  
  return priceVolumes;
};

export const analyzeVolumeWalls = async (symbol: string, days?: number) => {
  const orderBook = await getLatestOrderBook(symbol);
  if (!orderBook) {
    throw new Error("No order book data available");
  }
  
  const trades = await getRecentTrades(symbol, config.TRADES_TO_FETCH, days);
  const priceVolumes = analyzeVolumeAtPrice(trades, orderBook);
  
  // Sort by total value
  const sortedLevels = Object.entries(priceVolumes)
    .sort(([, a], [, b]) => b.total_value - a.total_value)
    .slice(0, 5);
    
  // Calculate trading summaries
  const buyVolume = trades
    .filter(t => t.side === "bu")
    .reduce((sum, t) => sum + t.volume, 0);
    
  const sellVolume = trades
    .filter(t => t.side === "sd")
    .reduce((sum, t) => sum + t.volume, 0);
    
  const afterHourTrades = trades.filter(t => t.side === "after-hour");
  const afterHourBuy = afterHourTrades
    .filter(t => t.price >= orderBook.ask_1.price)
    .reduce((sum, t) => sum + t.volume, 0);
    
  const afterHourSell = afterHourTrades
    .filter(t => t.price <= orderBook.bid_1.price)
    .reduce((sum, t) => sum + t.volume, 0);
    
  const afterHourUnknown = afterHourTrades
    .filter(t => orderBook.bid_1.price < t.price && t.price < orderBook.ask_1.price)
    .reduce((sum, t) => sum + t.volume, 0);
    
  const totalVolume = buyVolume + sellVolume + afterHourBuy + afterHourSell + afterHourUnknown;
  
  return {
    timestamp: orderBook.timestamp,
    symbol,
    market_status: {
      current_price: orderBook.match_price,
      bid_price: orderBook.bid_1.price,
      bid_volume: orderBook.bid_1.volume,
      ask_price: orderBook.ask_1.price,
      ask_volume: orderBook.ask_1.volume,
      spread: orderBook.ask_1.price - orderBook.bid_1.price
    },
    volume_analysis: {
      significant_levels: sortedLevels.map(([price, data]) => ({
        price: Number(price),
        ...data
      })),
      current_bid_accumulated: priceVolumes[orderBook.bid_1.price] || {},
      current_ask_accumulated: priceVolumes[orderBook.ask_1.price] || {}
    },
    trading_summary: {
      period: `last ${config.TRADES_TO_FETCH} trades`,
      total_trades: trades.length,
      volume: {
        buy: buyVolume,
        sell: sellVolume,
        after_hour: {
          buy: afterHourBuy,
          sell: afterHourSell,
          unknown: afterHourUnknown,
          total: afterHourBuy + afterHourSell + afterHourUnknown
        },
        total: totalVolume,
        buy_ratio: (buyVolume + afterHourBuy) / 
          (buyVolume + sellVolume + afterHourBuy + afterHourSell) || 0
      }
    }
  };
}; 