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
