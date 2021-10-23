import datetime as dt
from enum import Enum

import pandas as pd
from cbrf.models import DynamicCurrenciesRates


# see: https://www.cbr.ru/scripts/XML_val.asp?d=0
class CurrencyID(Enum):
    USD = "R01235"
    EUR = "R01239"
    GBP = "R01035"
    CHF = "R01775"
    CNY = "R01375"
    JPY = "R01820"
    HKD = "R01200"
    TRY = "R01700"


def currency_history_quotes(name: str, from_date: dt.date, to_date: dt.date):
    # делаем запрос к ЦБРФ для получения исторических данных
    from_date = dt.datetime(from_date.year, from_date.month, from_date.day)
    to_date = dt.datetime(to_date.year, to_date.month, to_date.day)
    id_code = CurrencyID[name].value
    history_rates = DynamicCurrenciesRates(from_date, to_date, id_code)
    # формируем и возвращаем результат
    rate_dates = [rate.date for rate in history_rates.rates]
    rate_values = [rate.value / rate.denomination for rate in history_rates.rates]
    currencies = pd.Series(rate_values, index=rate_dates, name='currency')
    return currencies


if __name__ == '__main__':
    # пример запроса исторического курса доллара
    date_to = dt.date.today()
    date_from = date_to - dt.timedelta(days=30)
    usd_history = currency_history_quotes('USD', date_from, date_to)
