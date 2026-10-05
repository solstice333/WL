import json
import logging
import argparse
import shelve
import yfinance as yf # type: ignore
import datetime as dt

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

@dataclass
class StaleTicker:
    last_seen: dt.datetime
    all_time_high: float

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

def load_stale_tickers() -> dict[str, StaleTicker]:
    with shelve.open("wl.db") as db:
        return dict(db)

def dump_stale_tickers(stale_tickers: dict[str, StaleTicker]) -> None:
    with shelve.open("wl.db") as db:
        for sym, data in stale_tickers.items():
            db[sym] = data

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

    for data in tickers.values():
        assert data.yf_ticker.info['quoteType'] != 'NONE', \
            f"Invalid quoteType for ticker {data.yf_ticker}"

    stale_tickers: dict[str, StaleTicker] = load_stale_tickers()

    for sym, data in tickers.items():
        current_price = data.yf_ticker.info.get(
            'currentPrice',
            data.yf_ticker.info.get(
                'regularMarketPrice',
                data.yf_ticker.info.get(
                    'navPrice',
                    data.yf_ticker.info['previousClose']
                )
            )
        )
        logging.info(f"current price for {sym}: {current_price}")

        if sym not in stale_tickers:
            ath1: float = data.yf_ticker.info['allTimeHigh']
            ath2 = float(
                data.yf_ticker.history(
                    period='max',
                    auto_adjust=False
                )['High'].max()
            )
            ath = max(ath1, ath2)
            stale_tickers[sym] = StaleTicker(
                last_seen=dt.datetime.now(),
                all_time_high=ath
            )
        ath = stale_tickers[sym].all_time_high
        logging.info(f"all-time high for {sym}: {ath}")

        if current_price > ath and \
            (dt.datetime.now() - stale_tickers[sym].last_seen) > \
            dt.timedelta(weeks=args.stale_timeout):
            stale_tickers[sym].last_seen = dt.datetime.now()
            stale_tickers[sym].all_time_high = current_price
            print(sym)
            continue

        for zone in data.zones:
            delta = current_price - zone.top
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
                stale_tickers[sym].last_seen = dt.datetime.now()
                print(sym)

    dump_stale_tickers(stale_tickers)

if __name__ == "__main__":
    main()
