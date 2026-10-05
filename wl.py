import json
import logging
import argparse
import yfinance as yf # type: ignore

from pprint import pformat
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Zone:
    top: float
    bottom: float

@dataclass
class TickerData:
    zones: list[Zone]
    yf_ticker: Optional[yf.Ticker] = None

def decode(o: dict[str, Any]) -> Zone | dict[str, Any]:
    match o:
        case {"top": float(top), "bottom": float(bottom)}:
            return Zone(top=top, bottom=bottom)
        case {"bottom": float(bottom)}:
            return o
        case {"top": float(top)}:
            return o
        case _:
            for k, v in o.items():
                assert isinstance(v, list), \
                    f"Expected list for key '{k}', got {type(v).__name__}"
                for item in v:
                    assert isinstance(item, Zone), \
                        f"Found non-Zone item in '{k}'" 
            for k in o:
                o[k] = TickerData(zones=o[k])
            return o

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tickers-file",
        default="tickers.json",
        help="Path to the tickers JSON file"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        "-d",
        "--percent-distance",
        type=float,
        default=0.05,
        help="Maximum percent distance from the top of the zone"
    )
    args = parser.parse_args()

    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('peewee').setLevel(logging.WARNING)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    with open(args.tickers_file, "r") as tickers_handle:
        tickers = json.load(tickers_handle, object_hook=decode)

    logging.info(pformat(tickers))

    yf_tickers = yf.Tickers(' '.join(tickers.keys()))

    logging.info(pformat(yf_tickers))

    for sym, yf_ticker_data in yf_tickers.tickers.items():
        tickers[sym].yf_ticker = yf_ticker_data

    logging.info(pformat(tickers))

    for sym, data in tickers.items():
        curr = data.yf_ticker.info['currentPrice']
        logging.info(f"current price for {sym}: {curr}")
        ath = data.yf_ticker.history(period='max')['High'].max()
        logging.info(f"all-time high for {sym}: {ath}")
        for zone in data.zones:
            delta = curr - zone.top
            logging.info(
                f"delta for {sym} in zone {zone.top}-{zone.bottom}: {delta}")

            if delta < 0:
                continue

            pct = delta / ath
            logging.info(
                f"percent distance for {sym} in zone "
                f"{zone.top}-{zone.bottom}: {pct}"
            )
            if pct <= args.percent_distance:
                print(sym)

if __name__ == "__main__":
    main()
