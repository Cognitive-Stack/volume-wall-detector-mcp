import axios from "axios";
import { getConfig } from "../config/env";
import { OrderBook, Trade } from "../types/tools";

const config = getConfig();

const headers = {
  "User-Agent": "Mozilla/5.0",
  "Accept": "application/json"
};

export const fetchOrderBook = async (symbol: string): Promise<OrderBook> => {
  const url = `${config.API_BASE_URL}/v2/stock/${symbol}`;
  const response = await axios.get(url, { headers });
  
  const data = response.data.data;
  return {
    symbol,
    timestamp: new Date().toISOString(),
    match_price: data.mp,
    bid_1: {
      price: data.b1,
      volume: data.b1v
    },
    ask_1: {
      price: data.o1,
      volume: data.o1v
    },
    change_percent: data.lpcp,
    volume: data.lv
  };
};

export const fetchTrades = async (symbol: string): Promise<Trade[]> => {
  const trades: Trade[] = [];
  let lastId: string | undefined;
  
  while (trades.length < config.TRADES_TO_FETCH) {
    const params: Record<string, any> = {
      stockSymbol: symbol,
      pageSize: Math.min(config.PAGE_SIZE, config.TRADES_TO_FETCH - trades.length)
    };
    
    if (lastId) {
      params.lastId = lastId;
    }
    
    const url = `${config.API_BASE_URL}/le-table`;
    const response = await axios.get(url, { headers, params });
    
    const items = response.data.data.items;
    if (!items || items.length === 0) {
      break;
    }
    
    const batchTrades = items.map((item: any) => ({
      trade_id: item._id,
      symbol: item.stockSymbol,
      price: item.price,
      volume: item.vol,
      side: item.side === "bu" || item.side === "sd" ? item.side : "after-hour",
      time: Math.floor(new Date().setHours(
        Number(item.time.split(":")[0]),
        Number(item.time.split(":")[1]),
        Number(item.time.split(":")[2] || 0)
      ) / 1000)
    }));
    
    trades.push(...batchTrades);
    lastId = items[items.length - 1]._id;
    
    // Add small delay to avoid hitting rate limits
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  return trades.slice(0, config.TRADES_TO_FETCH);
}; 