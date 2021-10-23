import datetime as dt

import pandas as pd
from cbrf.models import DynamicCurrenciesRates


def currency_history_quotes(code: str, from_date: dt.date, to_date: dt.date):
    # USD: R01235
    # EUR: R01239
    # see: https://www.cbr.ru/scripts/XML_val.asp?d=0
    # делаем запрос к ЦБРФ для получения исторических данных
    from_date = dt.datetime(from_date.year, from_date.month, from_date.day)
    to_date = dt.datetime(to_date.year, to_date.month, to_date.day)
    history_rates = DynamicCurrenciesRates(from_date, to_date, code)
    # формируем и возвращаем результат
    rate_dates = [rate.date for rate in history_rates.rates]
    rate_values = [rate.value for rate in history_rates.rates]
    currencies = pd.Series(rate_values, index=rate_dates, name='currency')
    return currencies


if __name__ == '__main__':
    # пример запроса исторического курса доллара
    date_1 = dt.datetime(2021, 9, 1)
    date_2 = dt.datetime(2021, 9, 30)
    usd_history = currency_history_quotes('R01235', date_1, date_2)
