from datetime import datetime

import tinvest
import pandas as pd
from tinvest import OperationStatus, Currency, OperationTypeWithCommission


class Tinkoff:

    def __init__(self, token: str):
        self.client = tinvest.SyncClient(token)

    def get_broker_accounts(self):
        accounts = self.client.get_accounts()
        payload = accounts.payload
        return {
            account.broker_account_type.value: str(account.broker_account_id)
            for account in payload.accounts
        }

    def get_portfolio_currencies(self):
        currencies = self.client.get_portfolio_currencies()\
            .payload\
            .currencies
        df = pd.DataFrame((
            {
                'currency': currency.currency.name,
                'balance': float(currency.balance)
            }
            for currency in currencies
        ))
        return df

    def get_operations(self, broker_account_id: str, date_from: datetime = None):
        date_from = date_from or datetime(2015, 1, 1, 0, 0, 0)
        date_to = datetime.now()
        operations = self.client.get_operations(
            from_=date_from,
            to=date_to,
            broker_account_id=broker_account_id
        ).payload.operations

        df = pd.DataFrame((operation.dict() for operation in operations))\
            .set_index('id')
        df = self._operations_processing(df)
        df = self._operations_map_ticker(df)
        return df

    def _operations_processing(self, df):
        to_drop = [
            'status',
            'trades',
            'quantity',
            'currency',
            'is_margin_call'
        ]
        rename_dict = {
            'date': 'dt',
            'price': 'unit_price',
            'payment': 'total_price',
            'quantity_executed': 'count',
            'commission': 'commission'
        }
        operations_filter = (
                (df['status'] == OperationStatus.done)
                & (df['currency'] == Currency.rub)
                & (df['instrument_type'].notna())
                & (df['operation_type'] != OperationTypeWithCommission.broker_commission)
        )
        df = df.copy()
        df = df[operations_filter]
        df.rename(columns=rename_dict, inplace=True)
        df.sort_values(by='dt', inplace=True)
        df['dt'] = pd.to_datetime(df['dt']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['commission'] = df['commission'].apply(lambda x: float(x['value']) if x else None)
        df['instrument_type'] = df['instrument_type'].apply(lambda x: x.name)
        df['operation_type'] = df['operation_type'].apply(lambda x: x.name)
        df.drop(columns=to_drop, inplace=True)
        return df

    def _operations_map_ticker(self, df):
        unique_figi = df['figi'].unique()
        figi_information = {
            figi: self.client.get_market_search_by_figi(figi).payload
            for figi in unique_figi
        }
        figi_to_ticker = {figi: value.ticker for figi, value in figi_information.items()}
        figi_to_isin = {figi: value.isin for figi, value in figi_information.items()}
        df['ticker'] = df['figi'].map(figi_to_ticker)
        df['isin'] = df['figi'].map(figi_to_isin)
        return df


if __name__ == '__main__':
    import os
    TOKEN = os.environ['TOKEN']

    client = Tinkoff(token=TOKEN)
    accounts = client.get_broker_accounts()
    currencies = client.get_portfolio_currencies()
    operations = client.get_operations(broker_account_id=accounts['TinkoffIis'])

    currencies.to_csv('../data/tinkoff/currencies.csv', header=True, encoding='utf-8')
    operations.to_csv('../data/tinkoff/operations.csv', index=True, header=True, encoding='utf-8')
