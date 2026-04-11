"""Utility to retrieve common ICE futures prices via Yahoo Finance."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Dict, Iterable, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import json

YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"


@dataclass
class FutureQuote:
    """Container for storing a single future contract quote."""

    symbol: str
    name: str
    price: float
    currency: str
    market_time: _dt.datetime

    def to_dict(self) -> Dict[str, str]:
        """Return a dictionary representation that is JSON serializable."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "market_time": self.market_time.isoformat(),
        }


class IceFuturesFetcher:
    """Fetch a batch of ICE futures quotes from Yahoo Finance."""

    DEFAULT_CONTRACTS: Dict[str, str] = {
        "BZ=F": "ICE Brent Crude Oil",
        "DX=F": "ICE U.S. Dollar Index",
        "SB=F": "ICE Sugar No. 11",
        "KC=F": "ICE Coffee C",
    }

    def __init__(self) -> None:
        """Initialise the fetcher."""

    def fetch(self, contracts: Dict[str, str] | None = None) -> List[FutureQuote]:
        """Fetch quotes for the provided contracts.

        Args:
            contracts: Mapping of Yahoo Finance symbols to human readable names.
                If omitted, :pyattr:`DEFAULT_CONTRACTS` is used.

        Returns:
            A list of :class:`FutureQuote` instances for the requested symbols.
        """

        mapping = contracts or self.DEFAULT_CONTRACTS
        symbols = ",".join(mapping.keys())
        payload = self._get_payload({"symbols": symbols})

        results = payload.get("quoteResponse", {}).get("result", [])
        quotes: List[FutureQuote] = []
        for item in results:
            symbol = item.get("symbol")
            if symbol is None or symbol not in mapping:
                continue
            price = item.get("regularMarketPrice")
            currency = item.get("currency", "")
            timestamp = item.get("regularMarketTime")
            market_time = (
                _dt.datetime.fromtimestamp(timestamp, tz=_dt.timezone.utc)
                if timestamp is not None
                else _dt.datetime.now(tz=_dt.timezone.utc)
            )
            quotes.append(
                FutureQuote(
                    symbol=symbol,
                    name=mapping[symbol],
                    price=float(price) if price is not None else float("nan"),
                    currency=currency,
                    market_time=market_time,
                )
            )

        return quotes

    def _get_payload(self, params: Dict[str, str]) -> Dict[str, object]:
        """Fetch JSON payload from Yahoo Finance."""
        query = urlencode(params)
        url = f"{YAHOO_QUOTE_URL}?{query}" if query else YAHOO_QUOTE_URL
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=10) as response:
            data = response.read().decode("utf-8")
        return json.loads(data)


def _format_quotes(quotes: Iterable[FutureQuote]) -> str:
    """Format quotes for pretty CLI output."""
    lines = []
    for quote in quotes:
        lines.append(
            f"{quote.name} ({quote.symbol}): {quote.price} {quote.currency} "
            f"@ {quote.market_time.isoformat()}"
        )
    return "\n".join(lines)


def main() -> None:
    """Entry point for CLI usage."""
    fetcher = IceFuturesFetcher()
    quotes = fetcher.fetch()
    print(_format_quotes(quotes))


if __name__ == "__main__":
    main()
