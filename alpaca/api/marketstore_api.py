#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The Alpaca module contains several utilities for interacting with the Alpaca trading platform.
"""

# System
import logging
import re
import time
import numpy as np
import pandas as pd
from requests.exceptions import ConnectionError

# Third Party
import alpaca_trade_api
import pymarketstore

# Autotrader
from alpaca import AlpacaRestAPI


def get_timeframe(timeframe: str) -> alpaca_trade_api.TimeFrame:
    match = re.compile("[^\W\d]").search(timeframe)
    number = int(timeframe[:match.start()])
    unit = timeframe[match.start():]

    if unit[0].upper() == "D":
        return alpaca_trade_api.TimeFrame(number, alpaca_trade_api.TimeFrameUnit.Day)
    elif unit[0].upper() == "H":
        return alpaca_trade_api.TimeFrame(number, alpaca_trade_api.TimeFrameUnit.Hour)
    elif unit[0].upper() == "M":
        return alpaca_trade_api.TimeFrame(number, alpaca_trade_api.TimeFrameUnit.Minute)
    else:
        raise ValueError("Timeframe unit not valid: {}".format(unit))

class MarketStoreApi(pymarketstore.Client):
    TIMEFRAMES = ['1D', '1H']
    SCHEMA = [('Epoch', 'i8'), ('Nanoseconds', 'i4'), ('o', 'f4'), ('h', 'f4'), ('l', 'f4'), ('c', 'f4'),
                  ('v', 'i4'), ('n', 'i4'), ('vw', 'f4')]
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        try:
            self._version = self.server_version()
        except ConnectionError as e:
            #TODO log exception
            pass

    def populate(self, symbols: list, start: str):
        rest_api = AlpacaRestAPI()
        for tf in self.TIMEFRAMES:
            timeframe = get_timeframe(tf)
            for symbol in symbols:

                timeframe = alpaca_trade_api.TimeFrame(1, alpaca_trade_api.TimeFrameUnit.Minute)
                start = "2021-12-03"
                symbol = "SPY"
                bars = rest_api.get_bars(symbol=symbol, timeframe=timeframe, start=start, limit=10000, adjustment='raw')
                t0 = time.time()
                reply = self.query("SPY", "1D", "OHLCV")
                self.destroy("SPY/1D/OHLCV")
                for bar in bars._raw:
                    bar['Epoch'] = pd.Timestamp(bar['t']).value / 10**9
                    bar['Nanoseconds'] = 0
                    bar_tuple = tuple(bar[item[0]] for item in self.SCHEMA)
                    payload = np.array([bar_tuple], dtype=self.SCHEMA)
                    result = self.write(payload, '{}/1D/OHLCV'.format(symbol, tf), isvariablelength=False)
                    reply = self.query("SPY", "1D", "OHLCV")
                    print()
                print(time.time() - t0)

    def trim(self, param_d: dict):
        """Trim all datastores according to Timeframe: Limit input dict.
        For example, to trim 1Min data to the last 2000 bars, params = {'1Min': 2000}
        :param params: timeframe/limit dict
        """
        for timeframe, N in param_d.items():
            for symbol in self.list_symbols():
                logging.info("Trimming data for {}".format(symbol))
                search_params = pymarketstore.Params(symbols=symbol, timeframe=timeframe, attrgroup='OHLCV')
                reply = self.query(search_params).first()
                if reply.array.size > N:
                    result = self.destroy(reply.key)
                    result = self.write(reply.array[-N:], reply.key, isvariablelength=True)

    def query(self, symbol: str, timeframe: str, start = None, end = None):
        params = pymarketstore.Params(symbols=symbol, timeframe=timeframe, attrgroup='OHLCV')
        reply = super().query(params).first().df()
        return reply

    def clear_database(self):
        logging.info("Removing symbols")
        for i, sym in enumerate(self.list_symbols()):
            logging.info("Removing {}")
            for tf in self.TIMEFRAMES:
                self.destroy('{}/{}/OHLCV'.format(sym, tf))

if __name__ == '__main__':
    ms_api = MarketStoreApi()

    ms_api.populate(['SPY'], start="2021-01-01")

    query_times = []
    for s in ms_api.list_symbols():
        t0 = time.time()
        data = ms_api.query(s, '1H')
        query_times.append(time.time() - t0)

