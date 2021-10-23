import matplotlib.figure
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator
import seaborn as sns


month_locator = MonthLocator()


def plot_profit_all_time(df, operations, figure_size=None) -> matplotlib.figure.Figure:
    figure_size = figure_size or (20, 10)
    # подсчет прибыльности за все время
    group_by_date = df.groupby('date')
    # прибыльность акций за каждый день
    sum_profit_money_by_date = group_by_date['profit_money'].sum()
    # размер портфеля на каждый день
    sum_spent_by_date = group_by_date['buy_price'].sum()
    # процент прибыли всего портфеля
    profit_by_date = (sum_profit_money_by_date / sum_spent_by_date)\
        .mul(100)\
        .rename('profit')\
        .reset_index()
    # маска, указывающая на события покупок по тем бумагам, которые учитываются в портфеле
    buy_mask = operations['operation_type'].isin(['buy', 'buy_card']) & operations['isin'].isin(df['isin'].unique())
    # считаем общую сумму на которую была совершена покупка
    buy_date = (-1) * operations[buy_mask].groupby(operations['dt'].dt.date)['total_price'].sum()
    # считаем, на какую сумму пополнился портфель
    sum_spent_by_date = sum_spent_by_date.loc[buy_date.index]
    buy_point_size = (buy_date / sum_spent_by_date).mul(100)
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
