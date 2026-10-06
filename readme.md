# WL

## Description
```
usage: wl.py [-h] [--tickers-file TICKERS_FILE] [--verbose]
             [-d PERCENT_DISTANCE] [-s STALE_TIMEOUT]

Remind user to update technical analysis bound to watchlist tickers. That is,
when a ticker goes "stale", notify the user. A ticker is stale when its price
is either close to a support zone, in the middle of a support zone, or price
action has breached the previous all time high for --stale-timeout weeks.

options:
  -h, --help            show this help message and exit
  --tickers-file TICKERS_FILE
                        Path to the tickers JSON file (default: tickers.json)
  --verbose             Enable verbose output (default: False)
  -d, --percent-distance PERCENT_DISTANCE
                        Maximum percent distance from the top of the zone
                        (default: 0.05)
  -s, --stale-timeout STALE_TIMEOUT
                        Stale timeout in weeks (default: 2)
```

## Installation
Using Windows cmd.exe...
```sh
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Example
Using the example `tickers.json` at the top-level, and Windows cmd.exe...
```sh
.venv\Scripts\activate
python --verbose wl.py 2>wl.log # errors, if any, written to wl.log
```