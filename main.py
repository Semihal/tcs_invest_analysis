from tinvest_analysis.analysis import investment_type_ration, investment_type_profit, correlation_type_profit, \
    profit_by_ticker
from tinvest_analysis.processing import parse_broker_operations, parse_financial_quote, input_choosing_accounts, \
    load_operations, load_financial_quotes, merge_quotes_and_operations, calculate_profit
from tinvest_analysis.charts import plot_profit_all_time
from tinvest_analysis.utils.date import last_available_date


splits = [
    {
        'isin': 'IE00BD3QJN10',
        'ratio': 100
    }
]


if __name__ == '__main__':
    token = "input your token here"
    last_date = last_available_date()

    accounts = parse_broker_operations(token)
    selected_account = input_choosing_accounts(accounts)
    parse_financial_quote(selected_account)

    operations = load_operations(selected_account, splits)
    quotes = load_financial_quotes(date_to=last_date)
    df = merge_quotes_and_operations(quotes, operations)
    df = calculate_profit(df)

    type_ration = investment_type_ration(df, last_date)
    print('Процентное соотношение по типам активов:', type_ration, sep='\n')
    print()
    profit_by_type_date, type_profit_agg = investment_type_profit(df)
    print('Прибыль по типам активов:', type_profit_agg, sep='\n')
    print()
    corr_type_profit = correlation_type_profit(profit_by_type_date)
    print('Корреляция прибыли по типам активов:', corr_type_profit, sep='\n')
    print()
    profit_by_ticker_agg = profit_by_ticker(df, last_date)
    print('Прибыли текущих активов:', profit_by_ticker_agg, sep='\n')

    profit_by_date_chart = plot_profit_all_time(df, offset_days=5)
    profit_by_date_chart.savefig('artifacts/all_profit.png')
