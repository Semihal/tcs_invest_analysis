import datetime as dt

import pandas as pd

from tinvest_analysis.loaders.cbrf_api import CurrencyID, currency_history_quotes
from tinvest_analysis.loaders.investfound import InvestFounds
from tinvest_analysis.loaders.tinkoff import Tinkoff
from tinvest_analysis.utils.fs import TINKOFF_DIR, HISTORY_QUOTE_DIR, HISTORY_CURRENCY_DIR


def parse_broker_operations(token: str):
    """
    Получение списка операций в портфеле от Тинькофф.
    """
    client = Tinkoff(token=token)
    accounts = client.get_broker_accounts()
    for account_type, account_id in accounts.items():
        folder = TINKOFF_DIR / account_type
        folder.mkdir(exist_ok=True)
        currencies = client.get_portfolio_currencies(account_id)
        operations = client.get_operations(account_id)
        currencies.to_csv(folder / 'currencies.csv', index=False, header=True)
        operations.to_csv(folder / 'operations.csv', index=True, header=True)
    return list(accounts.keys())


def parse_financial_quote(account_type):
    """
    Парсинг котировок ценных бумаг с сайта InvestFounds.
    """
    operations_path = TINKOFF_DIR / account_type / 'operations.csv'
    operations = pd.read_csv(operations_path)
    isin_list = operations['isin'].dropna().unique()

    client = InvestFounds(isin_list)
    for isin, asset in client.assets.items():
        asset.chartData.to_csv(HISTORY_QUOTE_DIR / f'{isin}.csv', header=True, index=False)


def parse_currency_quote():
    date_from = dt.date(2015, 1, 1)
    date_to = dt.date.today()
    rates = []
    for currency in CurrencyID:
        history_data = currency_history_quotes(currency.name, date_from, date_to)\
            .assign(currency=currency.name)
        file_path = HISTORY_CURRENCY_DIR / f'{currency.name}.csv'
        history_data.to_csv(file_path, header=True, index=False)
        rates.append(history_data)
    currency_rates = pd.concat(rates).reset_index(drop=True)
    currency_rates['date'] = currency_rates['date'].dt.date
    return currency_rates



def input_choosing_accounts(accounts):
    """
    Выбор портфеля, для которого будет производиться анализ.
    """
    print('Выбери интересующий тебя счет:')
    for i, account_type in enumerate(accounts, start=1):
        print(f'[{i}] {account_type}')
    input_index = int(input())
    return accounts[input_index - 1]


def load_operations(account_type, splits, currency_rates):
    operations_path = TINKOFF_DIR / account_type / 'operations.csv'
    operations = pd.read_csv(operations_path, parse_dates=['dt'])
    # откидываем все операции, что происходили сегодня
    operations['date'] = operations['dt'].dt.date
    operations = operations[operations['date'] < dt.date.today()]
    # оставляем только операции покупок и продаж
    operations = operations[operations['operation_type'].isin(['buy', 'sell', 'buy_card'])]
    # преобразуем все курсы валют к рублю
    mul_columns = ['total_price', 'unit_price', 'commission']
    operations = operations.merge(currency_rates, on=['date', 'currency'], how='left')
    mask = operations['close_price'].notna()
    operations.loc[mask, mul_columns] = operations.loc[mask, mul_columns]\
        .mul(operations.loc[mask, 'close_price'].astype('float'), axis=0)
    operations = operations.drop(columns=['close_price'])
    # преобразуем buy_card в buy
    type_map_dict = dict({x: x for x in operations['operation_type'].unique()}, buy_card='buy')
    operations['operation_type'] = operations['operation_type'].map(type_map_dict)
    # удаление бесполезных колонок
    operations = operations.drop(columns=['id'])
    # если бумага была продана, то поменяем ее count на отрицательный
    sell_mask = operations['operation_type'] == 'sell'
    operations.loc[sell_mask, 'count'] *= -1

    # обработка сплита акций
    for split_event in splits:
        # маска для операций, проведенных ДО сплита
        mask = \
            (operations['isin'] == split_event['isin']) \
            & (operations['dt'].dt.date <= split_event['date'])
        operations.loc[mask, 'count'] = operations.loc[mask, 'count'].mul(split_event['ratio'])
        operations.loc[mask, 'unit_price'] = operations.loc[mask, 'unit_price'].div(split_event['ratio'])
    return operations


def load_financial_quotes():
    quotes = []
    for path in HISTORY_QUOTE_DIR.iterdir():
        if not path.suffix == '.csv':
            continue
        df = (pd.read_csv(path, parse_dates=['dt'])
              .rename(columns={'dt': 'date'})
              .sort_values(by='date')
              .reset_index(drop=True)
              .assign(isin=path.stem))
        df['date'] = df['date'].dt.date
        # откидываем все котировки, что известны на текущий день
        df = df[df['date'] < dt.date.today()]
        quotes.append(df)
    quotes = pd.concat(quotes, axis=0)
    return quotes


def enrichment_ticker_prices(briefcase_ticker_price: pd.DataFrame, quotes: pd.DataFrame):
    # добавляем котировки акций к портфелю ценных бумаг
    briefcase_ticker_price = pd.merge(
        briefcase_ticker_price, quotes,
        left_on=['date', 'isin'],
        right_on=['date', 'isin'],
        how='left'
    ).sort_values(by='date')
    # заполняем пропуски в зависимости от ценной бумаги
    ffill_columns = ['close_price', 'investemnt_object_type', 'geography', 'currency']
    briefcase_ticker_price[ffill_columns] = briefcase_ticker_price.groupby('isin').ffill()[ffill_columns]
    # считаем характеристики доходности
    briefcase_ticker_price = calculate_profit(briefcase_ticker_price)
    return briefcase_ticker_price


def calculate_profit(df: pd.DataFrame):
    df['profit_money'] = df['quantity'] * df['close_price'] - df['buy_price']
    df['profit_percent'] = 100 * df['profit_money'] / df['buy_price']
    return df
