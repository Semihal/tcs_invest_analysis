from tinvest_analysis.processing import parse_broker_operations, parse_financial_quote, input_choosing_accounts, \
    load_operations, load_financial_quotes, merge_quotes_and_operations, calculate_profit
from tinvest_analysis.charts import plot_profit_all_time
from tinvest_analysis.utils.date import last_available_date

if __name__ == '__main__':
    token = "input your token here"
    last_date = last_available_date()

    operations = load_operations(selected_account)
    quotes = load_financial_quotes(date_to=last_date)
    df = merge_quotes_and_operations(quotes, operations)
    df = calculate_profit(df)

    profit_by_date_chart = plot_profit_all_time(df, offset_days=5)
    profit_by_date_chart.savefig('artifacts/all_profit.png')
