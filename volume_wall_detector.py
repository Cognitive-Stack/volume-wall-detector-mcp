import os
from datetime import date, datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from typing import List, Optional, Union, Dict, Any
import pymongo
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
import time
from pydantic import BaseModel, Field

load_dotenv()

# Mandatory environment variables
TIMEZONE = os.getenv("TIMEZONE", "GMT+7")  # Default to GMT+7 if not specified
API_BASE_URL = os.getenv("API_BASE_URL")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE")
MONGO_AUTH_MECHANISM = os.getenv("MONGO_AUTH_MECHANISM")

# Optional environment variables
PAGE_SIZE = os.getenv("PAGE_SIZE", 50)
TRADES_TO_FETCH = int(os.getenv("TRADES_TO_FETCH", "10000"))
DAYS_TO_FETCH = int(os.getenv("DAYS_TO_FETCH", "1"))  # Default to 1 day if not specified

# Headers for API requests
HEADERS: dict = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

def MONGO_URL() -> str:
        """Build MongoDB connection URL from components"""
        if MONGO_USER and MONGO_PASSWORD:
            return (
                f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"
                f"?authSource={MONGO_AUTH_SOURCE}"
                f"&authMechanism={MONGO_AUTH_MECHANISM}"
            )
        return f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

def parse_timezone(tz_str: str) -> timezone:
    """Parse timezone string (e.g., 'GMT+7' or 'GMT-5') into timezone object"""
    try:
        if not tz_str.startswith(('GMT+', 'GMT-')):
            raise ValueError("Timezone must be in format 'GMT+n' or 'GMT-n'")
        
        offset = int(tz_str[4:]) if tz_str[3] == '+' else -int(tz_str[4:])
        return timezone(timedelta(hours=offset))
    except Exception as e:
        raise ValueError(f"Invalid timezone format: {tz_str}. Error: {str(e)}")

class OrderBookLevel(BaseModel):
    """Order book level with price and volume"""
    price: float
    volume: int

class OrderBook(BaseModel):
    """Order book data"""
    symbol: str
    timestamp: str
    match_price: float
    bid_1: OrderBookLevel
    ask_1: OrderBookLevel
    change_percent: float
    volume: int

class Trade(BaseModel):
    """Trade data"""
    trade_id: str
    symbol: str
    price: float
    volume: int
    side: str  # "bu" or "sd" or "after-hour"
    time: int
    
    @property
    def value(self) -> float:
        """Calculate trade value"""
        return self.price * self.volume

class PriceVolumeData(BaseModel):
    """Volume and value data at a price level"""
    buy_volume: int = 0
    sell_volume: int = 0
    after_hour_buy: int = 0
    after_hour_sell: int = 0
    after_hour_unknown: int = 0
    buy_value: float = 0.0
    sell_value: float = 0.0
    after_hour_buy_value: float = 0.0
    after_hour_sell_value: float = 0.0
    after_hour_unknown_value: float = 0.0
    total_volume: int = 0
    total_value: float = 0.0
    volume_imbalance: int = 0
    value_imbalance: float = 0.0
    total_trades: int = 0
    last_trade_time: Optional[str] = None

class AfterHourVolume(BaseModel):
    """After-hour trading volume data"""
    buy: int
    sell: int
    unknown: int
    total: int

class AfterHourValue(BaseModel):
    """After-hour trading value data"""
    buy: float
    sell: float
    unknown: float
    total: float

class VolumeAnalysis(BaseModel):
    """Volume analysis data"""
    buy: int
    sell: int
    after_hour: AfterHourVolume
    total: int
    buy_ratio: float

class ValueAnalysis(BaseModel):
    """Value analysis data"""
    buy: float
    sell: float
    after_hour: AfterHourValue
    total: float
    buy_ratio: float

class MarketStatus(BaseModel):
    """Current market status"""
    current_price: float
    bid_price: float
    bid_volume: int
    ask_price: float
    ask_volume: int
    spread: float

class VolumeAnalysisResult(BaseModel):
    """Volume analysis results"""
    significant_levels: list[Dict[str, Any]]
    current_bid_accumulated: PriceVolumeData
    current_ask_accumulated: PriceVolumeData

class TradingSummary(BaseModel):
    """Trading summary data"""
    period: str
    total_trades: int
    volume: VolumeAnalysis
    value: ValueAnalysis
    unique_price_levels: int
    average_price: float

# class StockAnalysis(BaseModel):
#     """Complete stock analysis result"""
#     timestamp: str
#     symbol: str
#     market_status: MarketStatus
#     volume_analysis: VolumeAnalysisResult
#     trading_summary: TradingSummary

class MongoResult(BaseModel):
    """MongoDB operation result"""
    success: bool = False
    inserted_count: int = 0
    error: Optional[str] = None

class TradesResult(MongoResult):
    """Result of trades operation"""
    trades_fetched: int = 0

class StoreResult(BaseModel):
    """Result of storing stock data"""
    order_book: MongoResult
    trades: TradesResult

def store_stock_data(data: Union[OrderBook, List[Trade]], collection_name: str) -> MongoResult:
    """Store stock data into MongoDB"""
    result = MongoResult()
    
    try:
        client = MongoClient(MONGO_URL())
        db = client[MONGO_DATABASE]
        collection = db[collection_name]
        
        # Setup indexes if they don't exist
        if collection_name == "order_books":
            collection.create_index([("symbol", 1), ("timestamp", -1)])
        elif collection_name == "trades":
            collection.create_index([("symbol", 1), ("time", -1)])
            collection.create_index([("trade_id", 1)], unique=True)
        
        # Convert and store data
        if isinstance(data, OrderBook):
            insert_result = collection.insert_one(data.model_dump())
            result.success = insert_result.acknowledged
            result.inserted_count = 1 if insert_result.acknowledged else 0
            
        elif isinstance(data, list):
            if not data:
                result.success = True
                return result
                
            trade_docs = [trade.model_dump() for trade in data]
            try:
                operations = [
                    pymongo.UpdateOne(
                        {"trade_id": doc["trade_id"]},
                        {"$set": doc},
                        upsert=True
                    ) for doc in trade_docs
                ]
                
                # Delete today's records using configured timezone
                tz = parse_timezone(TIMEZONE)
                today_start = datetime.now(tz).replace(
                    hour=0, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                ).timestamp()
                
                collection.delete_many({
                    "symbol": trade_docs[0]["symbol"],
                    "time": {"$gte": today_start}
                })
                
                bulk_result = collection.bulk_write(operations, ordered=False)
                result.success = True
                result.inserted_count = bulk_result.upserted_count + bulk_result.modified_count
            except Exception as e:
                result.success = False
                result.error = f"Bulk upsert failed: {str(e)}"
                
    except Exception as e:
        result.error = str(e)
    finally:
        client.close()
        
    return result

def fetch_order_book(symbol) -> OrderBook:
    """Fetch current order book data for a symbol"""
    url = f"{API_BASE_URL}/v2/stock/{symbol}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json().get("data", {})
    
    return OrderBook(
        symbol=symbol,
        timestamp=datetime.now().isoformat(),
        match_price=data.get("mp"),
        bid_1=OrderBookLevel(
            price=data.get("b1"),
            volume=data.get("b1v")
        ),
        ask_1=OrderBookLevel(
            price=data.get("o1"),
            volume=data.get("o1v")
        ),
        change_percent=data.get("lpcp"),
        volume=data.get("lv")
    )

def fetch_trades(symbol: str) -> List[Trade]:
    """
    Fetch specified number of trades for a symbol using lastId pagination
    
    Args:
        symbol: Stock symbol
        
    Returns:
        List[Trade]: List of trades, newest first
    """
    trades = []
    last_id = None
    
    while len(trades) < TRADES_TO_FETCH:
        # Prepare request parameters
        params = {
            "stockSymbol": symbol,
            "pageSize": min(PAGE_SIZE, TRADES_TO_FETCH - len(trades))
        }
        if last_id:
            params["lastId"] = last_id
            
        # Make API request
        url = f"{API_BASE_URL}/le-table"
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        # Process response
        items = response.json().get("data", {}).get("items", [])
        if not items:  # No more trades available
            break
            
        # Convert items to Trade objects
        batch_trades = [
            Trade(
                trade_id=item["_id"],
                symbol=item["stockSymbol"],
                price=item["price"],
                volume=item["vol"],
                side=item["side"] if item.get("side") in ["bu", "sd"] else "after-hour",
                time=datetime.combine(date.today(), datetime.strptime(item["time"], "%H:%M:%S").time()).timestamp()
            ) for item in items
        ]
        
        trades.extend(batch_trades)
        
        # Update last_id for next iteration
        last_id = items[-1]["_id"]
        
        # Add small delay to avoid hitting rate limits
        time.sleep(0.1)
    
    return trades[:TRADES_TO_FETCH]  # Ensure we don't return more than requested

def fetch_and_store_stock_data(symbol: str) -> StoreResult:
    """
    Fetch and store both order book and trades data
    
    Returns:
        StoreResult: Results of both operations
    """
    # Fetch and store order book
    order_book = fetch_order_book(symbol)
    order_book_result = store_stock_data(order_book, "order_books")
    
    # Fetch and store trades
    trades = fetch_trades(symbol)
    trades_result = store_stock_data(trades, "trades")
    
    return StoreResult(
        order_book=order_book_result,
        trades=TradesResult(
            success=trades_result.success,
            inserted_count=trades_result.inserted_count,
            error=trades_result.error,
            trades_fetched=len(trades)
        )
    )


def get_latest_order_book(symbol: str) -> Optional[OrderBook]:
    """Get the latest order book from MongoDB"""
    try:
        client = MongoClient(MONGO_URL())
        db = client[MONGO_DATABASE]
        doc = db.order_books.find_one(
            {"symbol": symbol},
            sort=[("timestamp", -1)]
        )
        if doc:
            return OrderBook(
                symbol=doc["symbol"],
                timestamp=doc["timestamp"],
                match_price=doc["match_price"],
                bid_1=OrderBookLevel(**doc["bid_1"]),
                ask_1=OrderBookLevel(**doc["ask_1"]),
                change_percent=doc["change_percent"],
                volume=doc["volume"]
            )
        return None
    finally:
        client.close()

def get_recent_trades(symbol: str, limit: int = 100, days: int = None) -> List[Trade]:
    """
    Get recent trades from MongoDB
    
    Args:
        symbol: Stock symbol
        limit: Maximum number of trades to return
        days: Number of days to look back (defaults to DAYS_TO_FETCH from env)
    
    Returns:
        List[Trade]: List of trades, newest first
    """
    try:
        client = MongoClient(MONGO_URL())
        db = client[MONGO_DATABASE]
        
        # Use provided days or fall back to environment variable
        days_to_fetch = days if days is not None else DAYS_TO_FETCH
        
        # Calculate the timestamp for N days ago using configured timezone
        tz = parse_timezone(TIMEZONE)
        now = datetime.now(tz)
        days_ago = now - timedelta(days=days_to_fetch)
        start_timestamp = days_ago.replace(
            hour=0, 
            minute=0, 
            second=0, 
            microsecond=0
        ).timestamp()
        
        # Query with date filter
        trades = list(db.trades.find(
            {
                "symbol": symbol,
                "time": {"$gte": start_timestamp}
            },
            sort=[("time", -1)],
            limit=limit
        ))
        
        return [Trade(
            trade_id=t["trade_id"],
            symbol=t["symbol"],
            price=t["price"],
            volume=t["volume"],
            side=t["side"],
            time=t["time"]
        ) for t in trades]
    finally:
        client.close()

def analyze_volume_at_price(trades: List[Trade], order_book: OrderBook) -> Dict[float, PriceVolumeData]:
    """Analyze accumulated volume and value at each price level"""
    price_volumes: Dict[float, PriceVolumeData] = {}
    
    for trade in reversed(trades):
        price = trade.price
        if price not in price_volumes:
            price_volumes[price] = PriceVolumeData()
        
        data = price_volumes[price]
        # Accumulate volumes and values by side
        if trade.side == "bu":
            data.buy_volume += trade.volume
            data.buy_value += trade.value
        elif trade.side == "sd":
            data.sell_volume += trade.volume
            data.sell_value += trade.value
        else:  # after-hour trade classification
            if price >= order_book.ask_1.price:
                data.after_hour_buy += trade.volume
                data.after_hour_buy_value += trade.value
            elif price <= order_book.bid_1.price:
                data.after_hour_sell += trade.volume
                data.after_hour_sell_value += trade.value
            else:
                data.after_hour_unknown += trade.volume
                data.after_hour_unknown_value += trade.value

        tz = parse_timezone(TIMEZONE)
        data.total_trades += 1
        data.last_trade_time = str(datetime.fromtimestamp(trade.time, tz=tz))
    
    # Calculate additional metrics
    for price_data in price_volumes.values():
        price_data.total_volume = (
            price_data.buy_volume + 
            price_data.sell_volume + 
            price_data.after_hour_buy +
            price_data.after_hour_sell +
            price_data.after_hour_unknown
        )
        price_data.total_value = (
            price_data.buy_value + 
            price_data.sell_value + 
            price_data.after_hour_buy_value +
            price_data.after_hour_sell_value +
            price_data.after_hour_unknown_value
        )
        # Volume imbalance includes classified after-hour trades
        price_data.volume_imbalance = (
            price_data.buy_volume + 
            price_data.after_hour_buy
        ) - (
            price_data.sell_volume + 
            price_data.after_hour_sell
        )
        # Value imbalance includes classified after-hour trades
        price_data.value_imbalance = (
            price_data.buy_value + 
            price_data.after_hour_buy_value
        ) - (
            price_data.sell_value + 
            price_data.after_hour_sell_value
        )
    
    return price_volumes

def analyze_stock_data(symbol: str, days: int = None) -> dict:
    """Analyze stock data including volume and value analysis"""
    order_book = get_latest_order_book(symbol)
    trades = get_recent_trades(symbol, limit=TRADES_TO_FETCH, days=days)
    
    if not order_book:
        raise ValueError("No order book data available")
    
    # Analyze volumes at each price level
    price_volumes = analyze_volume_at_price(trades, order_book)
    
    # Sort prices for significant levels
    sorted_levels = sorted(
        [(price, data) for price, data in price_volumes.items()],
        key=lambda x: x[1].total_value,
        reverse=True
    )
    
    # Get top 5 levels
    significant_levels = [
        {
            "price": price,
            "buy_volume": data.buy_volume,
            "sell_volume": data.sell_volume,
            "after_hour_buy": data.after_hour_buy,
            "after_hour_sell": data.after_hour_sell,
            "after_hour_unknown": data.after_hour_unknown,
            "buy_value": data.buy_value,
            "sell_value": data.sell_value,
            "after_hour_buy_value": data.after_hour_buy_value,
            "after_hour_sell_value": data.after_hour_sell_value,
            "after_hour_unknown_value": data.after_hour_unknown_value,
            "total_volume": data.total_volume,
            "total_value": data.total_value,
            "volume_imbalance": data.volume_imbalance,
            "value_imbalance": data.value_imbalance,
            "total_trades": data.total_trades,
            "last_trade_time": data.last_trade_time
        }
        for price, data in sorted_levels[:5]
    ]
    
    # Calculate trading summaries
    buy_volume = sum(t.volume for t in trades if t.side == "bu")
    sell_volume = sum(t.volume for t in trades if t.side == "sd")
    after_hour_trades = [t for t in trades if t.side == "after-hour"]
    
    after_hour_buy = sum(t.volume for t in after_hour_trades if t.price >= order_book.ask_1.price)
    after_hour_sell = sum(t.volume for t in after_hour_trades if t.price <= order_book.bid_1.price)
    after_hour_unknown = sum(t.volume for t in after_hour_trades 
                           if order_book.bid_1.price < t.price < order_book.ask_1.price)
    
    buy_value = sum(t.value for t in trades if t.side == "bu")
    sell_value = sum(t.value for t in trades if t.side == "sd")
    after_hour_buy_value = sum(t.value for t in after_hour_trades if t.price >= order_book.ask_1.price)
    after_hour_sell_value = sum(t.value for t in after_hour_trades if t.price <= order_book.bid_1.price)
    after_hour_unknown_value = sum(t.value for t in after_hour_trades 
                                 if order_book.bid_1.price < t.price < order_book.ask_1.price)

    total_volume = buy_volume + sell_volume + after_hour_buy + after_hour_sell + after_hour_unknown
    total_value = buy_value + sell_value + after_hour_buy_value + after_hour_sell_value + after_hour_unknown_value

    return {
        "timestamp": order_book.timestamp,
        "symbol": symbol,
        "market_status": {
            "current_price": order_book.match_price,
            "bid_price": order_book.bid_1.price,
            "bid_volume": order_book.bid_1.volume,
            "ask_price": order_book.ask_1.price,
            "ask_volume": order_book.ask_1.volume,
            "spread": order_book.ask_1.price - order_book.bid_1.price
        },
        "volume_analysis": {
            "significant_levels": significant_levels,
            "current_bid_accumulated": price_volumes.get(order_book.bid_1.price, PriceVolumeData()).model_dump(),
            "current_ask_accumulated": price_volumes.get(order_book.ask_1.price, PriceVolumeData()).model_dump()
        },
        "trading_summary": {
            "period": f"last {TRADES_TO_FETCH} trades",
            "total_trades": len(trades),
            "volume": {
                "buy": buy_volume,
                "sell": sell_volume,
                "after_hour": {
                    "buy": after_hour_buy,
                    "sell": after_hour_sell,
                    "unknown": after_hour_unknown,
                    "total": after_hour_buy + after_hour_sell + after_hour_unknown
                },
                "total": total_volume,
                "buy_ratio": (buy_volume + after_hour_buy) / 
                            (buy_volume + sell_volume + after_hour_buy + after_hour_sell) 
                            if (buy_volume + sell_volume + after_hour_buy + after_hour_sell) > 0 else 0
            },
            "value": {
                "buy": buy_value,
                "sell": sell_value,
                "after_hour": {
                    "buy": after_hour_buy_value,
                    "sell": after_hour_sell_value,
                    "unknown": after_hour_unknown_value,
                    "total": after_hour_buy_value + after_hour_sell_value + after_hour_unknown_value
                },
                "total": total_value,
                "buy_ratio": (buy_value + after_hour_buy_value) / 
                            (buy_value + sell_value + after_hour_buy_value + after_hour_sell_value)
                            if (buy_value + sell_value + after_hour_buy_value + after_hour_sell_value) > 0 else 0
            },
            "unique_price_levels": len(price_volumes),
            "average_price": total_value / total_volume if total_volume > 0 else 0
        }
    }

if __name__ == "__main__":
    # Test the functions
    symbol = "VIC"
    fetch_and_store_stock_data(symbol)
    print(analyze_stock_data(symbol))
