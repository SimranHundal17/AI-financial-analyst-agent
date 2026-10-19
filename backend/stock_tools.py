import json
from datetime import date
from typing import Any

import pandas as pd
import yfinance as yf
from langchain.tools import tool


def _ticker_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol or len(symbol) > 15 or not all(character.isalnum() or character in ".-^=" for character in symbol):
        raise ValueError("Provide a valid ticker symbol.")
    return symbol


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if pd.isna(value):
        return None
    return value


@tool("get_stock_price", description="Get the latest available daily closing price for a listed company's ticker symbol.")
def get_stock_price(ticker: str) -> str:
    """Return the latest available daily close for a company ticker."""
    symbol = _ticker_symbol(ticker)
    stock = yf.Ticker(symbol)
    history = stock.history(period="5d", interval="1d", auto_adjust=False)
    if history.empty or "Close" not in history:
        return json.dumps({"ticker": symbol, "error": "No recent price data was returned."})
    valid_history = history.dropna(subset=["Close"])
    if valid_history.empty:
        return json.dumps({"ticker": symbol, "error": "No recent closing price was returned."})
    latest = valid_history.iloc[-1]
    currency = getattr(stock, "fast_info", {}).get("currency", "unknown")
    return json.dumps(
        {
            "ticker": symbol,
            "date": valid_history.index[-1].date().isoformat(),
            "closing_price": float(latest["Close"]),
            "currency": currency,
            "price_type": "latest available daily close; may be delayed",
        }
    )


@tool("get_historical_stock_price", description="Get daily OHLCV stock prices for a ticker from start_date inclusive to end_date exclusive (YYYY-MM-DD). Use the returned series to compare or plot price performance.")
def get_historical_stock_price(ticker: str, start_date: str, end_date: str) -> str:
    """Return daily open, high, low, close, and volume for a half-open date range."""
    symbol = _ticker_symbol(ticker)
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if start >= end:
        raise ValueError("start_date must be earlier than end_date.")
    history = yf.Ticker(symbol).history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
    if history.empty:
        return json.dumps({"ticker": symbol, "start_date": start_date, "end_date": end_date, "series": []})
    columns = [column for column in ["Open", "High", "Low", "Close", "Volume"] if column in history.columns]
    rows = []
    for timestamp, row in history[columns].iterrows():
        rows.append({"date": timestamp.date().isoformat(), **_json_safe(row.to_dict())})
    return json.dumps({"ticker": symbol, "start_date": start_date, "end_date": end_date, "series": rows})


@tool("get_balance_sheet", description="Get the annual balance sheet for a listed company's ticker symbol, including reported periods and line items.")
def get_balance_sheet(ticker: str) -> str:
    """Return annual balance sheet line items by reporting period."""
    symbol = _ticker_symbol(ticker)
    balance_sheet = yf.Ticker(symbol).balance_sheet
    if balance_sheet.empty:
        return json.dumps({"ticker": symbol, "periods": [], "line_items": []})
    periods = [column.date().isoformat() for column in balance_sheet.columns]
    line_items = []
    for metric, values in balance_sheet.iterrows():
        line_items.append(
            {
                "metric": str(metric),
                "values": [_json_safe(value) for value in values.tolist()],
            }
        )
    return json.dumps({"ticker": symbol, "periods": periods, "line_items": line_items})


@tool("get_stock_news", description="Get recent news headlines and available summaries for a listed company's ticker symbol.")
def get_stock_news(ticker: str) -> str:
    """Return a normalized list of recent news items for a ticker."""
    symbol = _ticker_symbol(ticker)
    articles = yf.Ticker(symbol).news or []
    normalized = []
    for article in articles[:10]:
        content = article.get("content", article)
        provider = content.get("provider") or {}
        canonical_url = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        normalized.append(
            {
                "title": content.get("title"),
                "summary": content.get("summary"),
                "publisher": provider.get("displayName") if isinstance(provider, dict) else provider,
                "published": content.get("pubDate") or content.get("displayTime"),
                "url": canonical_url.get("url") if isinstance(canonical_url, dict) else canonical_url,
            }
        )
    return json.dumps({"ticker": symbol, "articles": normalized})


STOCK_TOOLS = [get_stock_price, get_historical_stock_price, get_balance_sheet, get_stock_news]