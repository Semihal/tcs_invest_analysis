# Настройка
Для правильного функционирования приложения необходимо указать необходимые настройки в файле `config.yaml`:
1. tinkoff.token - указать токен подключения к openAPI Tinkoff.
2. stock_splits - содержит массив известных дроблений акций
   * isin - уникальный идентификатор ценной бумаги
   * ratio - сколько бумаг получилось из 1
3. charts - настройка отрисовки графиков
   * offset_days - сколько необходимо дней отступа в данных для прорисовки графика общей прибыльности портфеля (artifacts/all_profit.png). 
   Необходимо на случай, когда первые закупки сильно уносили доходность в + или - (они будет искривлять весь график).

# Запуск
1. Установить python версии не менее 3.8
2. В терминале (cmd): `pip install -r requirements.txt`
3. Запустить: `python main.py`