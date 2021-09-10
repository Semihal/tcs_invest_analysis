import datetime as dt

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
    return agg_types
