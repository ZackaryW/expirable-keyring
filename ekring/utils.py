import datetime
import typing

import dateparser


def parse_readable_date(date : str):
    import re
    # match 
    # in 1 day
    # in 1 hour
    # in 1 minute 
    # in 1 second
    # in 1 week
    # in 1 month
    # in 1 year
    # get number and date type, with optional s
    match = re.match(r"in (\d+) (\w+)", date)
    if match is None:
        return None
    
    num = int(match.group(1))
    date_type = match.group(2)
    if date_type.endswith("s"):
        date_type = date_type[:-1]

    match date_type:
        case "day":
            return datetime.timedelta(days=num)
        case "hour":
            return datetime.timedelta(hours=num)
        case "minute":
            return datetime.timedelta(minutes=num)
        case "second":
            return datetime.timedelta(seconds=num)
        case "week":
            return datetime.timedelta(weeks=num)
        case "month":
            return datetime.timedelta(days=num*30)
        case "year":
            return datetime.timedelta(days=num*365)
        case _:
            return None

def yield_every_n_char(string : str, n : int):
    for i in range(0, len(string), n):
        yield string[i:i+n]

def split_every_n_char(string : str, n : int):
    return list(yield_every_n_char(string, n))

def dateformat_length(string :str):
    length = 0
    for segment in split_every_n_char(string, 2):
        match segment:
            case "%Y":
                length += 4
            case "%m":
                length += 2
            case "%d":
                length += 2
            case "%H":
                length += 2
            case "%M":
                length += 2
            case "%S":
                length += 2
            case _:
                length += len(segment)
            
    return length

class IncrementCounter:
    index : int = 0

    def __init__(self, start : int = 0):
        self.index = start

    def __call__(self):
        self.index += 1
        return self.index
    
default_counter = IncrementCounter()

def parse_date_info(
    date : typing.Union[
        str, int, float, datetime.timedelta, datetime.datetime,
        datetime.date
    ]
):
    match date:
        case str(date) if date.startswith("in "):
            res = parse_readable_date(date)
            if res is None:
                raise ValueError("invalid date format")
            datetime_info =  datetime.datetime.now()
            res = datetime_info + res
        case str(date):
            res =  dateparser.parse(date)
            if res is None:
                raise ValueError("invalid date format")

        case int(date):
            res = datetime.datetime.fromtimestamp(date)
        case float(date):
            res = datetime.datetime.fromtimestamp(date)
        case date if isinstance(date, datetime.timedelta):
            res = datetime.datetime.now() + date
            return res
        case date if isinstance(date, datetime.datetime):
            res = date
        case date if isinstance(date, datetime.date):
            res = date + datetime.timedelta()
        case _:
            raise ValueError("invalid date format")
        
    # for all datetime objects that does not happen today, strip the time part
    if res.date() != datetime.datetime.now().date():
        res = datetime.datetime.combine(res.date(), datetime.time())

    return res
