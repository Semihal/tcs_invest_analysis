import numpy as np
import pandas as pd

from tinvest_analysis.loaders.investfound import InvestFounds
from tinvest_analysis.loaders.tinkoff import Tinkoff
from tinvest_analysis.utils.fs import TINKOFF_DIR, HISTORY_QUOTE_DIR


def parse_broker_operations(token: str):
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
    operations_path = TINKOFF_DIR / account_type / 'operations.csv'
    operations = pd.read_csv(operations_path)
    isin_list = operations['isin'].dropna().unique()

    client = InvestFounds(isin_list)
    for isin, asset in client.assets.items():
        asset.chartData.to_csv(HISTORY_QUOTE_DIR / f'{isin}.csv', header=True, index=False)


def input_choosing_accounts(accounts):
    print('Вебери интересующий тебя счет:')
    for i, account_type in enumerate(accounts, start=1):
        print(f'[{i}] {account_type}')
    input_index = int(input())
    return accounts[input_index - 1]


def load_operations(account_type):
    operations_path = TINKOFF_DIR / account_type / 'operations.csv'
    operations = pd.read_csv(operations_path, parse_dates=['dt'])
    operations = operations[operations['operation_type'].isin(['buy', 'sell', 'buy_card'])]
    # превращаем buy_card в buy
    type_map_dict = dict({x: x for x in operations['operation_type'].unique()}, buy_card='buy')
    operations['operation_type'] = operations['operation_type'].map(type_map_dict)
    # если count < 0 - то мы продали акцию, если count > 0 - купили
    operations['count'] = operations.apply(lambda x: x['count'] if x['operation_type'] == 'buy' else -x['count'], axis=1)
    # считаем итоговое количество оставшихся штук. этого актива на момент времени dt
    operations['cum_count'] = operations.groupby('ticker')['count'].cumsum()
    # кол-во потраченых денег на текущее кол-во активов
    operations['cum_spent'] = operations.groupby('ticker')['total_price'].apply(lambda x: (-x).cumsum())
    operations['cum_spent'] = operations.apply(lambda x: 0 if x['cum_count'] == 0 else x['cum_spent'], axis=1)
    # средняя цена бумаг в портфеле
    operations['avg_price'] = operations['cum_spent'] / operations['cum_count']
    operations['avg_price'] = operations.apply(lambda x: 0 if x['cum_count'] == 0 else x['avg_price'], axis=1)
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
        quotes.append(df)
    quotes = pd.concat(quotes, axis=0)
    return quotes


def merge_quotes_and_operations(quotes: pd.DataFrame, operations: pd.DataFrame):
    # подготавливаем operations
    operations = operations.copy()
    operations['date'] = operations['dt'].dt.date
    operations = operations.groupby(['isin', 'date']).last()
    # подготавливаем quotes
    quotes = quotes.merge(operations, on=['date', 'isin'], how='left')
    quotes = quotes.sort_values(by='date')
    # заполняем пропуски предыдущими значениями
    ffill_columns = ['ticker', 'cum_count', 'cum_spent', 'avg_price']
    quotes[ffill_columns] = quotes.groupby('isin').ffill()[ffill_columns]
    # удаление лишних колонок
    quotes = quotes.drop(columns=[
        'id',
        'dt',
        'figi',
        'isin',
        'instrument_type',
        # 'total_price',
        'unit_price',
    ])
    # оставляем записи начиная с даты покупки
    quotes = quotes.dropna(subset=ffill_columns, how='any')
    # проставляем avg_price как none для уже полностью проданых бумаг
    quotes['avg_price'] = quotes['avg_price'].apply(lambda x: np.nan if x == 0 else x)
    return quotes


def calculate_profit(df: pd.DataFrame):
    df['profit_money'] = df['cum_count'] * df['close_price'] - df['cum_spent']
    df['profit_percent'] = 100 * df['profit_money'] / df['cum_spent']
    return df
