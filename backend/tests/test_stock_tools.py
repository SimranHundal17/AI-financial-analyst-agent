import json
import unittest
from unittest.mock import patch

import pandas as pd

from backend.stock_tools import (
    get_balance_sheet,
    get_historical_stock_price,
    get_stock_news,
    get_stock_price,
)


class StockToolTests(unittest.TestCase):
    @patch("backend.stock_tools.yf.Ticker")
    def test_latest_close_is_serialized_with_date(self, ticker_factory) -> None:
        ticker = ticker_factory.return_value
        ticker.history.return_value = pd.DataFrame(
            {"Close": [100.5]}, index=pd.to_datetime(["2026-10-16"])
        )
        ticker.fast_info = {"currency": "USD"}

        result = json.loads(get_stock_price.invoke({"ticker": "aapl"}))

        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["date"], "2026-10-16")
        self.assertEqual(result["closing_price"], 100.5)

    @patch("backend.stock_tools.yf.Ticker")
    def test_missing_closes_return_a_tool_error(self, ticker_factory) -> None:
        ticker_factory.return_value.history.return_value = pd.DataFrame(
            {"Close": [None, None]}, index=pd.to_datetime(["2026-10-15", "2026-10-16"])
        )

        result = json.loads(get_stock_price.invoke({"ticker": "AAPL"}))

        self.assertIn("error", result)

    @patch("backend.stock_tools.yf.Ticker")
    def test_historical_prices_are_json_serializable(self, ticker_factory) -> None:
        ticker_factory.return_value.history.return_value = pd.DataFrame(
            {"Close": [10.0], "Volume": [12]}, index=pd.to_datetime(["2026-01-02"])
        )

        result = json.loads(
            get_historical_stock_price.invoke(
                {"ticker": "MSFT", "start_date": "2026-01-01", "end_date": "2026-02-01"}
            )
        )

        self.assertEqual(result["series"][0]["date"], "2026-01-02")
        self.assertEqual(result["series"][0]["Close"], 10.0)

    @patch("backend.stock_tools.yf.Ticker")
    def test_balance_sheet_has_periods_and_line_items(self, ticker_factory) -> None:
        ticker_factory.return_value.balance_sheet = pd.DataFrame(
            {pd.Timestamp("2025-12-31"): [20]}, index=["Cash"]
        )

        result = json.loads(get_balance_sheet.invoke({"ticker": "AAPL"}))

        self.assertEqual(result["periods"], ["2025-12-31"])
        self.assertEqual(result["line_items"][0]["metric"], "Cash")

    @patch("backend.stock_tools.yf.Ticker")
    def test_news_is_normalized(self, ticker_factory) -> None:
        ticker_factory.return_value.news = [
            {
                "content": {
                    "title": "Company update",
                    "provider": {"displayName": "Example News"},
                    "canonicalUrl": {"url": "https://example.com/story"},
                }
            }
        ]

        result = json.loads(get_stock_news.invoke({"ticker": "AAPL"}))

        self.assertEqual(result["articles"][0]["publisher"], "Example News")
        self.assertEqual(result["articles"][0]["url"], "https://example.com/story")

    def test_invalid_date_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            get_historical_stock_price.invoke(
                {"ticker": "AAPL", "start_date": "2026-03-01", "end_date": "2026-02-01"}
            )


if __name__ == "__main__":
    unittest.main()