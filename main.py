import datetime as dt
from pathlib import Path

import pandas as pd
import yaml

from tinvest_analysis.analysis import investment_type_ration, investment_type_profit, correlation_type_profit, \
    profit_by_ticker
from tinvest_analysis.processing import parse_broker_operations, parse_financial_quote, input_choosing_accounts, \
    load_operations, load_financial_quotes, enrichment_ticker_prices, parse_currency_quote
from tinvest_analysis.charts import plot_profit_all_time


def read_config(path):
    with path.open('r') as file:
        return yaml.safe_load(file)


def get_indexes(operations):
    """
    Возвращает список дат, между первой операцией и текущем днем недели
    :param operations:
    :return:
    """
    min_date = operations['dt'].dt.date.min()
    # будем всегда смотреть на отчет Т-1
    today = dt.date.today() - dt.timedelta(days=1)
    # будет являться индексом для нового DataFrame
    datetime_range = pd.date_range(start=min_date, end=today, freq='1D')
    return datetime_range


# REF
def ts_briefcase_ticker_prices(operations) -> pd.DataFrame:
    operations = operations.copy()
    datetime_range = get_indexes(operations)
    # считаем данные по каждому тикеру в разрезе дней
    operations['date'] = operations['dt'].dt.date.astype('datetime64[ns]')
    ts_aggregate = operations\
        .groupby(['date', 'isin', 'figi', 'ticker', 'instrument_type'], as_index=False)\
        .agg(
            quantity=('count', 'sum'),
            balance_change=('total_price', 'sum')
        )\
        .sort_values(by='date')
    # умножаем на (-1) поскольку считаем текущую (по покупкам) цену
    grouped_data = ts_aggregate.groupby(['isin', 'figi', 'ticker', 'instrument_type'])
    ts_aggregate['buy_price'] = (-1) * grouped_data['balance_change'].cumsum()
    ts_aggregate['quantity'] = grouped_data['quantity'].cumsum()

    # для каждой ценной бумаги считаем прибыльность по каждому дню
    # уникальный список акций
    unique_isin = ts_aggregate['isin'].unique()
    ticker_prices = []
    for isin in unique_isin:
        base_date = pd.DataFrame(data=datetime_range, columns=['date'])
        isin_operations = ts_aggregate[ts_aggregate['isin'] == isin]
        ticker_price = pd.merge(base_date, isin_operations, on='date', how='left')\
            .ffill()\
            .dropna(subset=['isin', 'figi', 'ticker'])\
            .drop(columns=['balance_change'])
        ticker_price['date'] = ticker_price['date'].dt.date
        # если бумага была продана полностью, то далее ее не рассматриваем
        ticker_price = ticker_price[ticker_price['quantity'] > 0]
        # считаем среднюю цену акции
        ticker_price['avg_price'] = ticker_price['buy_price'] / ticker_price['quantity']
        ticker_prices.append(ticker_price)
    ticker_prices = pd.concat(ticker_prices, axis=0)
    return ticker_prices


def main(config):
    token = config['tinkoff']['token']
    splits = config['stock_splits']

    accounts = parse_broker_operations(token)
    selected_account = input_choosing_accounts(accounts)
    parse_financial_quote(selected_account)

    quotes = load_financial_quotes()
    currency_rates = parse_currency_quote()
    operations = load_operations(selected_account, splits, currency_rates)
    briefcase_ticker_price = ts_briefcase_ticker_prices(operations)

    briefcase_ticker_price = enrichment_ticker_prices(briefcase_ticker_price, quotes)

    type_ration = investment_type_ration(briefcase_ticker_price)
    print('Процентное соотношение по типам активов:', type_ration, sep='\n')
    print()
    profit_by_type_date, type_profit_agg = investment_type_profit(briefcase_ticker_price)
    print('Прибыль по типам активов:', type_profit_agg, sep='\n')
    print()
    corr_type_profit = correlation_type_profit(profit_by_type_date)
    print('Корреляция прибыли по типам активов:', corr_type_profit, sep='\n')
    print()
    profit_by_ticker_agg = profit_by_ticker(briefcase_ticker_price)
    print('Прибыли текущих активов:', profit_by_ticker_agg, sep='\n')

    profit_by_date_chart = plot_profit_all_time(briefcase_ticker_price, operations)
    profit_by_date_chart.savefig('artifacts/all_profit.png')


if __name__ == '__main__':
    path_config = Path('config.yaml')
    pd.set_option('display.max_columns', 10)
    if not path_config.exists():
        raise FileNotFoundError('Файл config.yaml не найден!')
    config = read_config(path_config)
    main(config)
