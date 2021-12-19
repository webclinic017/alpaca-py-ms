#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Autotrader alpaca_api test suite
"""
import pytest
import time

from Autotrader.alpaca import stream_api

api = alpaca_api.AlpacaRestAPI()
order1 = None
order2 = None

def test_get_account():
    account = api.get_account()
    assert type(account) is dict
    assert type(account['equity']) is float

def test_account_configuration():
    api.update_account_configurations(no_shorting=True)
    config = api.get_account_configurations()
    assert config['no_shorting'] == True
    api.update_account_configurations(no_shorting=False)
    config = api.get_account_configurations()
    assert config['no_shorting'] == False

def test_get_seconds_until_market_open():
    seconds = api.get_seconds_until_market_open()
    assert type(seconds) == int


def test_submit_order():
    global order1, order2
    order1 = api.submit_order(symbol='FOA', qty=25)
    order2 = api.submit_order(symbol='ACR', qty=50)
    assert order1['qty'] == 25
    assert order2['qty'] == 50

def test_list_orders():
    global order1, order2
    orders = api.list_orders()
    assert orders[order1['id']]['symbol'] == 'FOA'
    assert orders[order1['id']]['qty'] == 25
    assert orders[order2['id']]['symbol'] == 'ACR'
    assert orders[order2['id']]['qty'] == 50

def test_cancel_order():
    global order1, order2
    api.cancel_order(order1['id'])
    api.cancel_order(order2['id'])
    time.sleep(0.2) # Allow server side update
    orders = api.list_orders()
    assert order1['id'] not in orders.keys()
    assert order2['id'] not in orders.keys()

def test_cancel_order_by_symbol():
    api.submit_order(symbol='RIV', qty=25)
    api.submit_order(symbol='RIV', qty=30)
    api.cancel_order_by_symbol('RIV')
    time.sleep(0.2) # Allow server side update
    ord = api.list_orders(symbols=['RIV'])
    assert ord == {}

def test_get_limit_price():
    pass
    # This is not working for some reason in scope of unit test. TODO

def test_watchlist():
    pass