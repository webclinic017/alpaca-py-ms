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


class MarketStoreApi(pymarketstore.Client):
    TIMEFRAMES = {
        '1Min': 500,
        '3Min': 500,
        '5Min': 500,
        '15Min': 500,
        '30Min': 500,
        '1H': 500,
        '2H': 500,
        '1D': 500}

    SCHEMA = [('Epoch', 'i8'), ('Open', 'f4'), ('High', 'f4'), ('Low', 'f4'),
              ('Close', 'f4'), ('Volume', 'i4'), ('VWAP', 'f4')]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        try:
            self._version = self.server_version()
        except ConnectionError as e:
            # TODO log exception
            pass

    def insert(self, bar: dict):
        """
        Insert bar data received from Alpaca streaming API into database
        :param bar:
        :return:
        """
        payload = convert_bar(bar)
        self.write(payload, '{}/1Min/OHLCV'.format(bar['S']))

    def populate(self, symbols: list):
        rest_api = AlpacaRestAPI()
        for tf, limit in self.TIMEFRAMES.items():
            timeframe = get_timeframe(tf)
            for symbol in symbols:
                start = "2021-12-15"  # FIXME
                bars = rest_api.get_bars(symbol=symbol, timeframe=timeframe, start=start, limit=10000, adjustment='raw')
                payload = convert_dataframe(bars.df)
                result = self.write(payload, '{}/{}/OHLCV'.format(symbol, tf))
                reply = self.query_data(symbol, "1D")
                print(result)

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

    def query_data(self, symbol: str, timeframe: str, start=None, end=None):
        params = pymarketstore.Params(symbols=symbol, timeframe=timeframe, attrgroup='OHLCV')
        reply = super().query(params).first().df()
        return reply

    def clear_database(self):
        logging.info("Removing symbols")
        for i, sym in enumerate(self.list_symbols()):
            logging.info("Removing {}")
            for tf in self.TIMEFRAMES:
                self.destroy('{}/{}/OHLCV'.format(sym, tf))


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


def determine_start_date():
    pass


# TODO Use common definition of this from somewhere
DATA_TYPES = np.dtype([('Epoch', 'i8'), ('Open', 'f4'), ('High', 'f4'), ('Low', 'f4'), ('Close', 'f4'),
                       ('Volume', 'f4'), ('VWAP', 'f4')])


def convert_bar(bar: dict) -> np.array:
    """
    Convert Alpaca streaming API bar dict to numpy ndarray format for Marketstore.
    :param bar: dict of bar data from Alpaca websocket API
    :return: reshaped ndarray of tuples per MarketStore API
    """
    bar_time = bar['t'].seconds
    bar_tuple = (bar_time, bar['o'], bar['h'], bar['l'], bar['c'], bar['v'], bar['vw'])
    return np.array([bar_tuple], dtype=DATA_TYPES)


def convert_dataframe(df: pd.DataFrame) -> np.array:
    """
    Convert Alpaca REST API returned DataFrame to numpy ndarray format for MarketStore.
    :param df: pandas DataFrame returned from Alpaca REST API
    :return: reshaped ndarray of tuples per MarketStore API
    """
    df.columns = df.columns.str.lower()
    df['epoch'] = df.index.astype('int64') // 1e9
    df.reset_index(inplace=True)
    df = df[['epoch', 'open', 'high', 'low', 'close', 'volume', 'vwap']]
    return np.array([tuple(v) for v in df.values.tolist()], dtype=DATA_TYPES)


if __name__ == '__main__':
    ms_api = MarketStoreApi()

    ms_api.populate(['MSFT'])
    for s in ms_api.list_symbols():
        t0 = time.time()
        data = ms_api.query_data(s, '1H')
        print(time.time() - t0)
