import datetime as dt

import numpy as np
import pandas as pd


def investment_type_ration(df: pd.DataFrame, last_date: dt.date):
    last_day = df[df['date'] == last_date]
    spent_to_today = last_day['cum_spent'].sum()
    spent__to_today_by_type = last_day.groupby('investemnt_object_type')['cum_spent'].sum()
    spent_by_type_percent: pd.Series = (100 * spent__to_today_by_type / spent_to_today).round(2)
    # делаем читаемый вид
    spent_by_type_percent.index = spent_by_type_percent.index.rename('Type')
    spent_by_type_percent = spent_by_type_percent.rename('percent')
    return spent_by_type_percent


def investment_type_profit(df: pd.DataFrame):
    group_by_type_and_date = df.groupby(['date', 'investemnt_object_type'])
    sum_profit_by_date = group_by_type_and_date['profit_money'].sum()
    sum_spent_by_date = group_by_type_and_date['cum_spent'].sum()
    mask = (sum_spent_by_date > 0) & sum_spent_by_date.notna()
    profit_by_type_date = (sum_profit_by_date[mask] / sum_spent_by_date[mask])\
        .mul(100)\
        .rename('profit')\
        .reset_index()
    agg_types = profit_by_type_date.groupby('investemnt_object_type').agg(
        min_profit=('profit', 'min'),
        max_profit=('profit', 'max'),
        last_profit=('profit', 'last'),
        days_period=('date', lambda x: x.max() - x.min())
    ).round(2)
    # делаем читаемый вид
    agg_types.index = agg_types.index.rename('Type')
    return profit_by_type_date, agg_types


def correlation_type(type_profit_by_date):
    pivot_profit = type_profit_by_date.pivot(
        index='date',
        columns='investemnt_object_type',
        values='profit')
    pivot_profit.columns = pivot_profit.columns.values
    corr_matrix = pivot_profit.corr()
    mask = np.zeros_like(corr_matrix, dtype=bool)
    mask[np.triu_indices_from(mask)] = True
    corr_matrix[mask] = np.nan
    # делаем читаемый вид
    corr_series = corr_matrix.stack().reset_index()
    corr_series = corr_series.rename(columns={
        'level_0': 'Type 1',
        'level_1': 'Type2',
        0: 'correlation'})
    corr_series = corr_series.sort_values(by='correlation', ascending=False)
    return corr_series

