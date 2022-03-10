import datetime


def first_day_of_the_week(day):
    if isinstance(day, datetime.datetime):
        day = day.date()
    return day - datetime.timedelta(days=day.weekday())
