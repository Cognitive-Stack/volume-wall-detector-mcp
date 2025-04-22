import { MongoClient } from "mongodb";
import { getConfig } from "../config/env";
import { OrderBook, Trade } from "../types/tools";

const config = getConfig();

export const getMongoUrl = () => {
  if (config.MONGO_USER && config.MONGO_PASSWORD) {
    return `mongodb://${config.MONGO_USER}:${config.MONGO_PASSWORD}@${config.MONGO_HOST}:${config.MONGO_PORT}/${config.MONGO_DATABASE}?authSource=${config.MONGO_AUTH_SOURCE}&authMechanism=${config.MONGO_AUTH_MECHANISM}`;
  }
  return `mongodb://${config.MONGO_HOST}:${config.MONGO_PORT}/${config.MONGO_DATABASE}`;
};

export const storeStockData = async (data: OrderBook | Trade[], collectionName: string) => {
  const client = new MongoClient(getMongoUrl());
  
  try {
    await client.connect();
    const db = client.db(config.MONGO_DATABASE);
    const collection = db.collection(collectionName);
    
    // Setup indexes if they don't exist
    if (collectionName === "order_books") {
      await collection.createIndex({ symbol: 1, timestamp: -1 });
    } else if (collectionName === "trades") {
      await collection.createIndex({ symbol: 1, time: -1 });
      await collection.createIndex({ trade_id: 1 }, { unique: true });
    }
    
    if (Array.isArray(data)) {
      if (data.length === 0) {
        return { success: true, inserted_count: 0 };
      }
      
      const operations = data.map(doc => ({
        updateOne: {
          filter: { trade_id: doc.trade_id },
          update: { $set: doc },
          upsert: true
        }
      }));
      
      const result = await collection.bulkWrite(operations);
      return {
        success: true,
        inserted_count: result.upsertedCount + result.modifiedCount
      };
    } else {
      const result = await collection.insertOne(data);
      return {
        success: result.acknowledged,
        inserted_count: result.acknowledged ? 1 : 0
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    };
  } finally {
    await client.close();
  }
};

export const getLatestOrderBook = async (symbol: string): Promise<OrderBook | null> => {
  const client = new MongoClient(getMongoUrl());
  
  try {
    await client.connect();
    const db = client.db(config.MONGO_DATABASE);
    const doc = await db.collection("order_books")
      .findOne({ symbol }, { sort: { timestamp: -1 } });
      
    return doc as OrderBook | null;
  } finally {
    await client.close();
  }
};

export const getRecentTrades = async (
  symbol: string,
  limit: number = 100,
  days: number = config.DAYS_TO_FETCH
): Promise<Trade[]> => {
  const client = new MongoClient(getMongoUrl());
  
  try {
    await client.connect();
    const db = client.db(config.MONGO_DATABASE);
    
    const startTime = new Date();
    startTime.setDate(startTime.getDate() - days);
    startTime.setHours(0, 0, 0, 0);
    
    const trades = await db.collection("trades")
      .find({
        symbol,
        time: { $gte: Math.floor(startTime.getTime() / 1000) }
      })
      .sort({ time: -1 })
      .limit(limit)
      .toArray();
      
    return trades.map(trade => ({
      symbol: trade.symbol,
      price: trade.price,
      volume: trade.volume,
      trade_id: trade.trade_id,
      side: trade.side,
      time: trade.time
    }));
  } finally {
    await client.close();
  }
};