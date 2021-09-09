import matplotlib.figure
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator
import seaborn as sns


month_locator = MonthLocator()


def plot_profit_all_time(df, figure_size=None, offset_days=0) -> matplotlib.figure.Figure:
    figure_size = figure_size or (20, 10)
    # подсчет прибыльности за все время
    group_by_date = df.groupby('date')
    sum_profit_money_by_date = group_by_date['profit_money'].sum()
    sum_spent_by_date = group_by_date['cum_spent'].sum()
    mask = (sum_spent_by_date > 0) & sum_spent_by_date.notna()
    profit_by_date = (sum_profit_money_by_date[mask] / sum_spent_by_date[mask])\
        .mul(100)\
        .rename('profit')\
        .reset_index()\
        .iloc[offset_days:]
    # подсчет точек пополнения
    buy_date = (-1) * df[df['operation_type'] == 'buy'].groupby('date')['total_price'].sum()
    sum_spent_by_date = group_by_date['cum_spent'].sum()
    sum_spent_by_date = sum_spent_by_date.loc[buy_date.index]
    buy_point_size = (buy_date / sum_spent_by_date).mul(100)
    # учитываем offset для графика
    buy_point_size = buy_point_size[buy_point_size.index.isin(profit_by_date['date'])]
    # прорисовка "линии" доходности
    fig = plt.figure(figsize=figure_size)
    ax = fig.gca()
    sns.lineplot(data=profit_by_date, x='date', y='profit', label='Доходность')
    # прорисовка точек покупки ценных бумаг
    x_y_buy_point = profit_by_date[profit_by_date['date'].isin(buy_point_size.index)]
    plt.scatter(x_y_buy_point['date'], x_y_buy_point['profit'], s=buy_point_size, c='r', label='Покупки')
    # прорисовка дополнительных элементов и настройка осей
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.7)
    plt.grid(linestyle='--', alpha=0.3)
    plt.title('Прибыльность портфеля инвестиций')
    plt.xlabel('Дата')
    plt.ylabel('Прибыльность, %')
    plt.legend()
    plt.tight_layout()
    fig.autofmt_xdate()
    ax.xaxis.set_major_locator(month_locator)
    return fig
