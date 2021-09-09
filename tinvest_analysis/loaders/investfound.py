import datetime as dt
import time
from typing import Dict

from tqdm import tqdm
import requests
from lxml import etree
import pandas as pd


INVESTMENT_OBJECT_TYPE_XPATH = "//ul[contains(@class, 'param_list')]" \
                               "/li[span[text() = 'Объект инвестирования']]" \
                               "/div[contains(@class, 'value')]/text()"
GEOGRAPHY_XPATH = "//ul[contains(@class, 'param_list')]" \
                  "/li[span[text() = 'География инвестирования']]" \
                  "/div[contains(@class, 'value')]/text()"
CURRENCY_XPATH = "//ul[contains(@class, 'param_list')]" \
                 "/li[span[text() = 'Валюта фонда']]" \
                 "/div[contains(@class, 'value')]/text()"


class InvestTypeBase:

    def url(self) -> str:
        raise NotImplementedError

    def default_chart_payload(self):
        raise NotImplementedError

    @classmethod
    def parse(cls, isin: str):
        params = {'searchString': isin}
        response = requests.get(cls.url, params).json()
        # Защита от неточного поиска
        if response['total'] == 1:
            body = response['currentResults'][0]
            return cls(isin, body)
        return

    def __init__(self, isin, response_body):
        self.isin = isin
        self.attributes = self._parse_attributes(response_body)
        self.chartData = self._get_chart_data()

    def _parse_attributes(self, response_body):
        raise NotImplementedError

    def _get_chart_data(self):
        raise NotImplementedError

    def _parse_geography(self, url):
        page_content = requests.get(url)
        doc = etree.HTML(page_content.content)
        geography = doc.xpath(GEOGRAPHY_XPATH)[0]
        return geography if len(geography) > 0 else None

    def _parse_currency(self, url):
        page_content = requests.get(url)
        doc = etree.HTML(page_content.content)
        currency = doc.xpath(CURRENCY_XPATH)[0]
        return currency if len(currency) > 0 else None

    def investment_type(self, url):
        page_content = requests.get(url)
        doc = etree.HTML(page_content.content)
        invest_type = doc.xpath(INVESTMENT_OBJECT_TYPE_XPATH)[0]
        return invest_type if len(invest_type) > 0 else None


class Stock(InvestTypeBase):

    url = "https://investfunds.ru/stocks"
    default_chart_payload = {}

    def _parse_attributes(self, response_body) -> dict:
        return dict(
            id=response_body['id'],
            id_numeric=response_body['id.numeric'],
            name=response_body['name'],
            url=response_body['url'].strip('/'),
            trading_grounds=[
                dict(
                    exchange_name=ground['name'],
                    id=ground['id'],
                    id_numeric=ground['id.numeric']
                )
                for ground in response_body['trading_grounds']
                if ground['name'].lower() in ('московская биржа', 'санкт-петербургская биржа')
            ]
        )

    def _get_chart_data(self) -> pd.DataFrame:
        stock_id = self.attributes['id_numeric']
        ground_id = self.attributes['trading_grounds'][0]['id_numeric']
        payload = {
            'action': 'chartData',
            'stocks[]': f'{stock_id}/{ground_id}',
            'dateFrom': dt.date(2015, 1, 1).strftime('%d.%m.%Y'),
            'needVolume': False,
            'newAlgorithm': True
        }
        url = f"{self.url[:-7]}/{self.attributes['url']}"
        response = requests.get(f'{url}/1', payload)
        response.raise_for_status()
        content = response.json()[0]
        chart_data = content['data']
        # make dataframe
        df = pd.DataFrame(chart_data, columns=['dt', 'close_price'])
        df['dt'] = df['dt'].apply(lambda x: dt.datetime.fromtimestamp(x // 1000))
        df = df.assign(investemnt_object_type='Акции', geography=None, currency=None)
        return df

    def _parse_currency(self, url):
        xpath = "//ul[contains(@class, 'param_list')]" \
                "/li[span[text() = 'Номинал']]" \
                "/div[contains(@class, 'value')]/text()"
        page_content = requests.get(url)
        doc = etree.HTML(page_content.content)
        currency = doc.xpath(xpath)
        if len(currency) > 0:
            currency = currency.split(' ', 1)[-1]
        return currency


class Bond(InvestTypeBase):

    url = "https://investfunds.ru/bonds"
    default_chart_payload = {}

    def _parse_attributes(self, response_body) -> dict:
        return dict(
            id=response_body['id'],
            name=response_body['document'],
            url=response_body['if_bond_link'].strip('/')
        )

    def _get_chart_data(self) -> pd.DataFrame:
        payload = {
            'action': 'chartData',
            'tg_id': None,
            'data_keys': 'last',
            'date_from': None
        }
        pass


class Fund(InvestTypeBase):

    url = "https://investfunds.ru/funds"
    default_chart_payload = {}

    def _parse_attributes(self, response_body) -> dict:
        return dict(
            fc_id=response_body['fc_id'],
            fc_id_numeric=response_body['fc_id.numeric'],
            fund_id=response_body['fund_id'],
            fund_id_numeric=response_body['fund_id.numeric'],
            name=response_body['fund_name'],
            url=response_body['funds_url'].strip('/')
        )

    def _get_chart_data(self) -> pd.DataFrame:
        payload = {
            'action': 'chartData',
            'data_key': 'pay',
            'currencyId': 1,
            'date_from': dt.date(2015, 1, 1).strftime('%d.%m.%Y'),
            'ids[]': self.attributes['fund_id_numeric']
        }
        url = f"{self.url[:-6]}/{self.attributes['url']}"
        response = requests.get(url, payload)
        response.raise_for_status()
        content = response.json()[0]
        date_format = content['tooltip']['xDateFormat']
        chart_data = content['data']
        # make dataframe
        df = pd.DataFrame(chart_data, columns=['dt', 'close_price'])
        df['dt'] = df['dt'].apply(lambda x: dt.datetime.fromtimestamp(x // 1000))
        df = df.assign(investemnt_object_type=None, geography=None, currency=self._parse_currency(url))
        return df


class Etf(InvestTypeBase):

    url = "https://investfunds.ru/etf"
    default_chart_payload = {}

    def _parse_attributes(self, response_body) -> dict:
        return dict(
            id=response_body['id'],
            id_numeric=response_body['id.numeric'],
            fund_id=response_body['fund_id'],
            fund_id_numeric=response_body['fund_id.numeric'],
            name=response_body['name'],
            url=response_body['class_link'].strip('/'),
            trading_grounds=[
                dict(
                    exchange_name=ground['name'],
                    id=ground['id'],
                    id_numeric=ground['id.numeric']
                )
                for ground in response_body['trading_grounds']
                if ground['name'].lower() in ('московская биржа', 'санкт-петербургская биржа')
            ]
        )

    def _get_chart_data(self) -> pd.DataFrame:
        payload = {
            'action': 'chartData',
            'data_key': 'close',
            'date_from': dt.date(2015, 1, 1).strftime('%d.%m.%Y'),
            'needVolume': 1
        }
        url = f"{self.url[:-4]}/{self.attributes['url']}"
        response = requests.get(f'{url}/1', payload)
        response.raise_for_status()
        content = response.json()[0]
        date_format = content['tooltip']['xDateFormat']
        chart_data = content['data']
        # make dataframe
        df = pd.DataFrame(chart_data, columns=['dt', 'close_price'])
        df['dt'] = df['dt'].apply(lambda x: dt.datetime.fromtimestamp(x // 1000))
        df = df.assign(
            investemnt_object_type=self.investment_type(url),
            geography=self._parse_geography(url),
            currency=self._parse_currency(url))
        return df


class InvestFounds:
    URL = 'https://investfunds.ru'
    InvestTypes = (Etf, Stock, Bond, Fund)

    def __init__(self, isin_list):
        self.assets: Dict[str, InvestTypeBase] = self._parse_assets(isin_list)

    def _parse_assets(self, isin_list) -> dict:
        ids = {}
        for isin in tqdm(isin_list):
            for invest_type_parser in self.InvestTypes:
                invest_unit = invest_type_parser.parse(isin)
                if invest_unit:
                    ids[isin] = invest_unit
                    break
                time.sleep(1)
            if isin not in ids:
                print(f'Skip {isin} :(')
        return ids


if __name__ == '__main__':
    operations = pd.read_csv('../../data/tinkoff/operations.csv')
    isin_list = operations.loc[operations['isin'].notna(), 'isin'].unique()

    client = InvestFounds(isin_list)
    for isin, asset in client.assets.items():
        asset.chartData.to_csv(f'../data/investfunds/{isin}.csv', header=True, index=False, sep=',')
