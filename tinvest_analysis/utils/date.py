import datetime as dt


def last_available_date():
    available_date = dt.date.today()
    today_weekday = available_date.weekday()
    if today_weekday in (5, 6):
        # last friday
        available_date = (available_date
                          - dt.timedelta(today_weekday)
                          + dt.timedelta(days=4))
    elif today_weekday == 0:
        # today is monday
        available_date = available_date - dt.timedelta(days=3)
    else:
        # weekday between tuesday and thursday
        available_date = available_date - dt.timedelta(days=1)
    return available_date
