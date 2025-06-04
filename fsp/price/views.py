import datetime as dt
import requests
from lxml import html
from django.shortcuts import render

from price.logging import logger


STOCKS_QUANTITY = 22586948000


cbr_headers = {
        'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0)'
                       'Gecko/20100101 Firefox/45.0')
    }
moex_price_url = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=marketdata&marketdata.columns=LAST'
prev_price_url = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=securities&securities.columns=PREVPRICE'
market_price_url = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=marketdata&marketdata.columns=MARKETPRICE'
# use prev price, then market price url when moex price is off

def get_used_month():
    if dt.datetime.now().day > 15:
        return dt.datetime.now().strftime('%m')
    return (dt.datetime.now() - dt.timedelta(days=17)).strftime('%m')


def get_cbr_url(usedmonth):
    return (f'https://www.cbr.ru/banking_sector/credit/coinfo/f123/'
            f'?regnum=1481&dt=2024-{usedmonth}-01')


def parse_own_capital():
    parsed_page = requests.get(get_cbr_url(get_used_month()),
                               headers=cbr_headers)
    tree = html.fromstring(parsed_page.content)
    parsed_string = tree.xpath(
        '/html/body/main/div/div/div/div[3]/div[2]/table/tr[2]/td[3]/text()'
    )[0]
    logger.info(f'parsed own capital, its {parsed_string}')
    return int(parsed_string.replace(' ', '')) * 1000


def get_fair_price():
    own_capital = parse_own_capital()
    fair_price = round(own_capital / STOCKS_QUANTITY, 2)
    logger.info(f'got fair price, its {fair_price}')
    return fair_price


def get_moex_price():
    moex_request = requests.get(moex_price_url).json()
    moex_price = moex_request['marketdata']['data'][0][0]
    if moex_price is None:
        moex_request = requests.get(prev_price_url).json()
        moex_price = moex_request['securities']['data'][0][0]
        if moex_price is None:
            moex_request = requests.get(market_price_url).json()
            moex_price = moex_request['marketdata']['data'][0][0]
    logger.info(f'got moex price, its {moex_price}')
    return moex_price


def get_price_score():
    pb_value = round(get_moex_price() / get_fair_price(), 2)
    logger.info(f'got P/B, its {pb_value}')
    if pb_value < 1:
        return 'дешево'
    elif 1 <= pb_value <= 1.2:
        return 'справедливо'
    elif 1.2 < pb_value < 1.4:
        return 'чуть дорого'
    return 'дорого'


def index(request):
    context = {
        'moex_price': get_moex_price(),
        'fair_price': get_fair_price(),
        'fair_price_20_percent': round(get_fair_price() * 1.2, 2),
        'price_score': get_price_score(),
    }
    logger.info('index works')
    return render(request, 'index.html', context)


def thesis(request):
    pb = round(get_moex_price() / get_fair_price(), 2)
    context = {
        'moex_price': get_moex_price(),
        'pb': pb,
    }
    logger.info('thesis works')
    return render(request, 'thesis.html', context)


def history_data(request):
    logger.info('hist data works')
    return render(request, 'history_data.html')


# TECH INFO - ONLY FOR OTLADKA TIME


def get_otladka_data():
    return requests.get(moex_price_url).json()


def otladka(request):
    context = {
        'otladka': get_otladka_data()
    }
    return render(request, 'otladka.html', context)
