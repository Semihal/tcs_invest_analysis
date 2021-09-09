from tinvest_analysis.analysis import parse_broker_operations, parse_financial_quote, input_choosing_accounts, \
    load_operations, load_financial_quotes, merge_quotes_and_operations, calculate_profit

if __name__ == '__main__':
    token = "input your token here"
    accounts = parse_broker_operations(token)
    selected_account = input_choosing_accounts(accounts)
    parse_financial_quote(selected_account)

    operations = load_operations(selected_account)
    quotes = load_financial_quotes()
    df = merge_quotes_and_operations(quotes, operations)
    df = calculate_profit(df)
