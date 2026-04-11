# ICE Futures Price Fetcher

This example project retrieves several commonly traded contracts from the ICE exchange
(Brent crude oil, U.S. Dollar Index, Sugar No. 11 and Coffee C) by calling Yahoo Finance's
public quote endpoint.

## Requirements

- Python 3.9+
- Internet access to reach Yahoo Finance

## Usage

Run the module directly to print the latest quotes:

```bash
python fetch_ice_futures.py
```

Each line in the output contains the name, symbol, last traded price, currency and the
exchange timestamp (in UTC).
