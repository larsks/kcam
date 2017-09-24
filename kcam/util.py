import datetime


def date_from_path(path):
    if len(str(path).split('/')) != 4:
        raise ValueError('path "%s" must have four components' % path)

    year, month, day = (int(x) for x in str(path.parent).split('/'))
    hour, minute, second = (int(x) for x in str(path.name).split(':'))
    return datetime.datetime(
        year=year, month=month, day=day,
        hour=hour, minute=minute, second=second
    )
