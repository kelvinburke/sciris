'''
Time/date utilities

Highlights:
    - ``sc.tic()/sc.toc()/sc.timer()``: simple methods for timing durations
    - ``sc.readdate()``: convert strings to dates using common formats
    - ``sc.daterange()``: create a list of dates
    - ``sc.datedelta()``: perform calculations on date strings
'''

import time
import dateutil
import warnings
import numpy as np
import pylab as pl
import datetime as dt
from . import sc_utils as ut


__all__ = ['now', 'getdate', 'readdate', 'date', 'day', 'daydiff', 'daterange', 'datedelta', 'datetoyear',
           'elapsedtimestr', 'tic', 'toc', 'toctic', 'Timer', 'timer', 'timedsleep']

def now(timezone=None, utc=False, die=False, astype='dateobj', tostring=False, dateformat=None):
    '''
    Get the current time, optionally in UTC time.

    **Examples**::

        sc.now() # Return current local time, e.g. 2019-03-14 15:09:26
        sc.now('US/Pacific') # Return the time now in a specific timezone
        sc.now(utc=True) # Return the time in UTC
        sc.now(astype='str') # Return the current time as a string instead of a date object
        sc.now(tostring=True) # Backwards-compatible alias for astype='str'
        sc.now(dateformat='%Y-%b-%d') # Return a different date format
    '''
    if isinstance(utc, str): timezone = utc # Assume it's a timezone
    if timezone is not None: tzinfo = dateutil.tz.gettz(timezone) # Timezone is a string
    elif utc:                tzinfo = dateutil.tz.tzutc() # UTC has been specified
    else:                    tzinfo = None # Otherwise, do nothing
    if tostring: astype = 'str'
    timenow = dt.datetime.now(tzinfo)
    output = getdate(timenow, astype=astype, dateformat=dateformat)
    return output



def getdate(obj=None, astype='str', dateformat=None):
        '''
        Alias for converting a date object to a formatted string.

        **Examples**::

            sc.getdate() # Returns a string for the current date
            sc.getdate(sc.now(), astype='int') # Convert today's time to an integer
        '''
        if obj is None:
            obj = now()

        if dateformat is None:
            dateformat = '%Y-%b-%d %H:%M:%S'
        else:
            astype = 'str' # If dateformat is specified, assume type is a string

        try:
            if ut.isstring(obj):
                return obj # Return directly if it's a string
            obj.timetuple() # Try something that will only work if it's a date object
            dateobj = obj # Test passed: it's a date object
        except Exception as E: # pragma: no cover # It's not a date object
            errormsg = f'Getting date failed; date must be a string or a date object: {repr(E)}'
            raise TypeError(errormsg)

        if   astype == 'str':     output = dateobj.strftime(dateformat)
        elif astype == 'int':     output = time.mktime(dateobj.timetuple()) # So ugly!! But it works -- return integer representation of time
        elif astype == 'dateobj': output = dateobj
        else: # pragma: no cover
            errormsg = f'"astype={astype}" not understood; must be "str" or "int"'
            raise ValueError(errormsg)
        return output


def _sanitize_iterables(obj, *args):
    '''
    Take input as a list, array, or non-iterable type, along with one or more
    arguments, and return a list, along with information on what the input types
    were.

    **Examples**::

        _sanitize_iterables(1, 2, 3)             # Returns [1,2,3], False, False
        _sanitize_iterables([1, 2], 3)           # Returns [1,2,3], True, False
        _sanitize_iterables(np.array([1, 2]), 3) # Returns [1,2,3], True, True
        _sanitize_iterables(np.array([1, 2, 3])) # Returns [1,2,3], False, True
    '''
    is_list = isinstance(obj, list) or len(args)>0 # If we're given a list of args, treat it like a list
    is_array = isinstance(obj, np.ndarray) # Check if it's an array
    if is_array: # If it is, convert it to a list
        obj = obj.tolist()
    objs = ut.dcp(ut.promotetolist(obj)) # Ensure it's a list, and deepcopy to avoid mutability
    objs.extend(args) # Add on any arguments
    return objs, is_list, is_array


def _sanitize_output(obj, is_list, is_array, dtype=None):
    '''
    The companion to _sanitize_iterables, convert the object back to the original
    type supplied.
    '''
    if is_array:
        output = np.array(obj, dtype=dtype)
    elif not is_list and len(obj) == 1:
        output = obj[0]
    else:
        output = obj
    return output


def readdate(datestr=None, *args, dateformat=None, return_defaults=False):
    '''
    Convenience function for loading a date from a string. If dateformat is None,
    this function tries a list of standard date types.

    By default, a numeric date is treated as a POSIX (Unix) timestamp. This can be changed
    with the ``dateformat`` argument, specifically:

    - 'posix'/None: treat as a POSIX timestamp, in seconds from 1970
    - 'ordinal'/'matplotlib': treat as an ordinal number of days from 1970 (Matplotlib default)

    Args:
        datestr (int, float, str or list): the string containing the date, or the timestamp (in seconds), or a list of either
        args (list): additional dates to convert
        dateformat (str or list): the format for the date, if known; if 'dmy' or 'mdy', try as day-month-year or month-day-year formats; can also be a list of options
        return_defaults (bool): don't convert the date, just return the defaults

    Returns:
        dateobj (date): a datetime object

    **Examples**::

        dateobj  = sc.readdate('2020-03-03') # Standard format, so works
        dateobj  = sc.readdate('04-03-2020', dateformat='dmy') # Date is ambiguous, so need to specify day-month-year order
        dateobj  = sc.readdate(1611661666) # Can read timestamps as well
        dateobj  = sc.readdate(16166, dateformat='ordinal') # Or ordinal numbers of days, as used by Matplotlib
        dateobjs = sc.readdate(['2020-06', '2020-07'], dateformat='%Y-%m') # Can read custom date formats
        dateobjs = sc.readdate('20200321', 1611661666) # Can mix and match formats
    '''

    # Define default formats
    formats_to_try = {
        'date':           '%Y-%m-%d', # 2020-03-21
        'date-slash':     '%Y/%m/%d', # 2020/03/21
        'date-dot':       '%Y.%m.%d', # 2020.03.21
        'date-space':     '%Y %m %d', # 2020 03 21
        'date-alpha':     '%Y-%b-%d', # 2020-Mar-21
        'date-alpha-rev': '%d-%b-%Y', # 21-Mar-2020
        'date-alpha-sp':  '%d %b %Y', # 21 Mar 2020
        'date-Alpha':     '%Y-%B-%d', # 2020-March-21
        'date-Alpha-rev': '%d-%B-%Y', # 21-March-2020
        'date-Alpha-sp':  '%d %B %Y', # 21 March 2020
        'date-numeric':   '%Y%m%d',   # 20200321
        'datetime':       '%Y-%m-%d %H:%M:%S',    # 2020-03-21 14:35:21
        'datetime-alpha': '%Y-%b-%d %H:%M:%S',    # 2020-Mar-21 14:35:21
        'default':        '%Y-%m-%d %H:%M:%S.%f', # 2020-03-21 14:35:21.23483
        'ctime':          '%a %b %d %H:%M:%S %Y', # Sat Mar 21 23:09:29 2020
        }

    # Define day-month-year formats
    dmy_formats = {
        'date':           '%d-%m-%Y', # 21-03-2020
        'date-slash':     '%d/%m/%Y', # 21/03/2020
        'date-dot':       '%d.%m.%Y', # 21.03.2020
        'date-space':     '%d %m %Y', # 21 03 2020
    }

    # Define month-day-year formats
    mdy_formats = {
        'date':           '%m-%d-%Y', # 03-21-2020
        'date-slash':     '%m/%d/%Y', # 03/21/2020
        'date-dot':       '%m.%d.%Y', # 03.21.2020
        'date-space':     '%m %d %Y', # 03 21 2020
    }

    # To get the available formats
    if return_defaults:
        return formats_to_try

    # Handle date formats
    format_list = ut.promotetolist(dateformat, keepnone=True) # Keep none which signifies default
    if dateformat is not None:
        if dateformat == 'dmy':
            formats_to_try = dmy_formats
        elif dateformat == 'mdy':
            formats_to_try = mdy_formats
        else:
            formats_to_try = {}
            for f,fmt in enumerate(format_list):
                formats_to_try[f'User supplied {f}'] = fmt

    # Ensure everything is in a consistent format
    datestrs, is_list, is_array = _sanitize_iterables(datestr, *args)

    # Actually process the dates
    dateobjs = []
    for datestr in datestrs: # Iterate over them
        dateobj = None
        exceptions = {}
        if isinstance(datestr, dt.datetime):
            dateobj = datestr # Nothing to do
        elif ut.isnumber(datestr):
            if 'posix' in format_list or None in format_list:
                dateobj = dt.datetime.fromtimestamp(datestr)
            elif 'ordinal' in format_list or 'matplotlib' in format_list:
                dateobj = pl.num2date(datestr)
            else:
                errormsg = f'Could not convert numeric date {datestr} using available formats {ut.strjoin(format_list)}; must be "posix" or "ordinal"'
                raise ValueError(errormsg)
        else:
            for key,fmt in formats_to_try.items():
                try:
                    dateobj = dt.datetime.strptime(datestr, fmt)
                    break # If we find one that works, we can stop
                except Exception as E:
                    exceptions[key] = str(E)
            if dateobj is None:
                formatstr = ut.newlinejoin([f'{item[1]}' for item in formats_to_try.items()])
                errormsg = f'Was unable to convert "{datestr}" to a date using the formats:\n{formatstr}'
                if dateformat not in ['dmy', 'mdy']:
                    errormsg += '\n\nNote: to read day-month-year or month-day-year dates, use dateformat="dmy" or "mdy" respectively.'
                raise ValueError(errormsg)
        dateobjs.append(dateobj)

    # If only a single date was supplied, return just that; else return the list/array
    output = _sanitize_output(dateobjs, is_list, is_array, dtype=object)
    return output


def date(obj, *args, start_date=None, readformat=None, outformat=None, as_date=True, **kwargs):
    '''
    Convert any reasonable object -- a string, integer, or datetime object, or
    list/array of any of those -- to a date object. To convert an integer to a
    date, you must supply a start date.

    Caution: while this function and readdate() are similar, and indeed this function
    calls readdate() if the input is a string, in this function an integer is treated
    as a number of days from start_date, while for readdate() it is treated as a
    timestamp in seconds. To change

    Args:
        obj (str, int, date, datetime, list, array): the object to convert
        args (str, int, date, datetime): additional objects to convert
        start_date (str, date, datetime): the starting date, if an integer is supplied
        readformat (str/list): the format to read the date in; passed to sc.readdate()
        outformat (str): the format to output the date in, if returning a string
        as_date (bool): whether to return as a datetime date instead of a string

    Returns:
        dates (date or list): either a single date object, or a list of them (matching input data type where possible)

    **Examples**::

        sc.date('2020-04-05') # Returns datetime.date(2020, 4, 5)
        sc.date([35,36,37], start_date='2020-01-01', as_date=False) # Returns ['2020-02-05', '2020-02-06', '2020-02-07']
        sc.date(1923288822, readformat='posix') # Interpret as a POSIX timestamp

    New in version 1.0.0.
    New in version 1.2.2: "readformat" argument; renamed "dateformat" to "outformat"
    '''
    # Handle deprecation
    dateformat = kwargs.pop('dateformat', None)
    if dateformat is not None: # pragma: no cover
        outformat = dateformat
        warnmsg = 'sc.date() argument "dateformat" has been deprecated as of v1.2.2; use "outformat" instead'
        warnings.warn(warnmsg, category=DeprecationWarning, stacklevel=2)

    # Convert to list and handle other inputs
    if obj is None:
        return None
    if outformat is None:
        outformat = '%Y-%m-%d'
    obj, is_list, is_array = _sanitize_iterables(obj, *args)

    dates = []
    for d in obj:
        if d is None:
            dates.append(d)
            continue
        try:
            if type(d) == dt.date: # Do not use isinstance, since must be the exact type
                pass
            elif isinstance(d, dt.datetime):
                d = d.date()
            elif ut.isstring(d):
                d = readdate(d, dateformat=readformat).date()
            elif ut.isnumber(d):
                if readformat is not None:
                    d = readdate(d, dateformat=readformat).date()
                else:
                    if start_date is None:
                        errormsg = f'To convert the number {d} to a date, you must either specify "posix" or "ordinal" read format, or supply start_date'
                        raise ValueError(errormsg)
                    d = date(start_date) + dt.timedelta(days=int(d))
            else: # pragma: no cover
                errormsg = f'Cannot interpret {type(d)} as a date, must be date, datetime, or string'
                raise TypeError(errormsg)
            if as_date:
                dates.append(d)
            else:
                dates.append(d.strftime(outformat))
        except Exception as E:
            errormsg = f'Conversion of "{d}" to a date failed: {str(E)}'
            raise ValueError(errormsg)

    # Return an integer rather than a list if only one provided
    output = _sanitize_output(dates, is_list, is_array, dtype=object)
    return output


def day(obj, *args, start_date=None, **kwargs):
    '''
    Convert a string, date/datetime object, or int to a day (int), the number of
    days since the start day. See also sc.date() and sc.daydiff(). If a start day
    is not supplied, it returns the number of days into the current year.

    Args:
        obj (str, date, int, list, array): convert any of these objects to a day relative to the start day
        args (list): additional days
        start_date (str or date): the start day; if none is supplied, return days since (supplied year)-01-01.

    Returns:
        days (int or list): the day(s) in simulation time (matching input data type where possible)

    **Examples**::

        sc.day(sc.now()) # Returns how many days into the year we are
        sc.day(['2021-01-21', '2024-04-04'], start_date='2022-02-22') # Days can be positive or negative

    New in version 1.0.0.
    New in version 1.2.2: renamed "start_day" to "start_date"
    '''

    # Handle deprecation
    start_day = kwargs.pop('start_day', None)
    if start_day is not None: # pragma: no cover
        start_date = start_day
        warnmsg = 'sc.day() argument "start_day" has been deprecated as of v1.2.2; use "start_date" instead'
        warnings.warn(warnmsg, category=DeprecationWarning, stacklevel=2)

    # Do not process a day if it's not supplied, and ensure it's a list
    if obj is None:
        return None
    obj, is_list, is_array = _sanitize_iterables(obj, *args)

    days = []
    for d in obj:
        if d is None:
            days.append(d)
        elif ut.isnumber(d):
            days.append(int(d)) # Just convert to an integer
        else:
            try:
                if ut.isstring(d):
                    d = readdate(d).date()
                elif isinstance(d, dt.datetime):
                    d = d.date()
                if start_date:
                    start_date = date(start_date)
                else:
                    start_date = date(f'{d.year}-01-01')
                d_day = (d - start_date).days # Heavy lifting -- actually compute the day
                days.append(d_day)
            except Exception as E: # pragma: no cover
                errormsg = f'Could not interpret "{d}" as a date: {str(E)}'
                raise ValueError(errormsg)

    # Return an integer rather than a list if only one provided
    output = _sanitize_output(days, is_list, is_array)
    return output


def daydiff(*args):
    '''
    Convenience function to find the difference between two or more days. With
    only one argument, calculate days since 2020-01-01.

    **Examples**::

        diff  = sc.daydiff('2020-03-20', '2020-04-05') # Returns 16
        diffs = sc.daydiff('2020-03-20', '2020-04-05', '2020-05-01') # Returns [16, 26]

    New in version 1.0.0.
    '''
    days = [date(day) for day in args]
    if len(days) == 1:
        days.insert(0, date(f'{now().year}-01-01')) # With one date, return days since Jan. 1st

    output = []
    for i in range(len(days)-1):
        diff = (days[i+1] - days[i]).days
        output.append(diff)

    if len(output) == 1:
        output = output[0]

    return output


def daterange(start_date, end_date, inclusive=True, as_date=False, dateformat=None):
    '''
    Return a list of dates from the start date to the end date. To convert a list
    of days (as integers) to dates, use sc.date() instead.

    Args:
        start_date (int/str/date): the starting date, in any format
        end_date (int/str/date): the end date, in any format
        inclusive (bool): if True (default), return to end_date inclusive; otherwise, stop the day before
        as_date (bool): if True, return a list of datetime.date objects instead of strings
        dateformat (str): passed to date()

    **Example**::

        dates = sc.daterange('2020-03-01', '2020-04-04')

    New in version 1.0.0.
    '''
    end_day = day(end_date, start_date=start_date)
    if inclusive:
        end_day += 1
    days = list(range(end_day))
    dates = date(days, start_date=start_date, as_date=as_date, dateformat=dateformat)
    return dates


def datedelta(datestr, days=0, months=0, years=0, weeks=0, as_date=None, **kwargs):
    '''
    Perform calculations on a date string (or date object), returning a string (or a date).
    Wrapper to dateutil.relativedelta().

    Args:
        datestr (str/date): the starting date (typically a string)
        days (int): the number of days (positive or negative) to increment
        months (int): as above
        years (int): as above
        weeks (int): as above
        as_date (bool): if True, return a date object; otherwise, return as input type
        kwargs (dict): passed to ``sc.readdate()``

    **Examples**::

        sc.datedelta('2021-07-07', 3) # Add 3 days
        sc.datedelta('2021-07-07', days=-4) # Subtract 4 days
        sc.datedelta('2021-07-07', weeks=4, months=-1, as_date=True) # Add 4 weeks but subtract a month, and return a dateobj
    '''
    if as_date is None and isinstance(datestr, str): # Typical case
        as_date = False
    dateobj = readdate(datestr, **kwargs)
    newdate = dateobj + dateutil.relativedelta.relativedelta(days=days, months=months, years=years, weeks=weeks)
    newdate = date(newdate, as_date=as_date)
    return newdate


def datetoyear(dateobj, dateformat=None):
    """
    Convert a DateTime instance to decimal year.

    Args:
        dateobj (date, str):  The datetime instance to convert
        dateformat (str): If dateobj is a string, the optional date conversion format to use

    Returns:
        Equivalent decimal year

    **Example**::

        sc.datetoyear('2010-07-01') # Returns approximately 2010.5

    By Luke Davis from https://stackoverflow.com/a/42424261, adapted by Romesh Abeysuriya.

    New in version 1.0.0.
    """
    if ut.isstring(dateobj):
        dateobj = readdate(dateobj, dateformat=dateformat)
    year_part = dateobj - dt.datetime(year=dateobj.year, month=1, day=1)
    year_length = dt.datetime(year=dateobj.year + 1, month=1, day=1) - dt.datetime(year=dateobj.year, month=1, day=1)
    return dateobj.year + year_part / year_length


def elapsedtimestr(pasttime, maxdays=5, minseconds=10, shortmonths=True):
    """
    Accepts a datetime object or a string in ISO 8601 format and returns a
    human-readable string explaining when this time was.

    The rules are as follows:

    * If a time is within the last hour, return 'XX minutes'
    * If a time is within the last 24 hours, return 'XX hours'
    * If within the last 5 days, return 'XX days'
    * If in the same year, print the date without the year
    * If in a different year, print the date with the whole year

    These can be configured as options.

    **Examples**::

        yesterday = sc.datedelta(sc.now(), days=-1)
        sc.elapsedtimestr(yesterday)
    """

    # Elapsed time function by Alex Chan
    # https://gist.github.com/alexwlchan/73933442112f5ae431cc
    def print_date(date, includeyear=True, shortmonths=True):
        """Prints a datetime object as a full date, stripping off any leading
        zeroes from the day (strftime() gives the day of the month as a zero-padded
        decimal number).
        """
        # %b/%B are the tokens for abbreviated/full names of months to strftime()
        if shortmonths:
            month_token = '%b'
        else:
            month_token = '%B'

        # Get a string from strftime()
        if includeyear:
            date_str = date.strftime('%d ' + month_token + ' %Y')
        else:
            date_str = date.strftime('%d ' + month_token)

        # There will only ever be at most one leading zero, so check for this and
        # remove if necessary
        if date_str[0] == '0':
            date_str = date_str[1:]

        return date_str
    now_time = dt.datetime.now()

    # If the user passes in a string, try to turn it into a datetime object before continuing
    if isinstance(pasttime, str):
        try:
            pasttime = readdate(pasttime)
        except ValueError as E: # pragma: no cover
            errormsg = f"User supplied string {pasttime} is not in a readable format."
            raise ValueError(errormsg) from E
    elif isinstance(pasttime, dt.datetime):
        pass
    else: # pragma: no cover
        errormsg = f"User-supplied value {pasttime} is neither a datetime object nor an ISO 8601 string."
        raise TypeError(errormsg)

    # It doesn't make sense to measure time elapsed between now and a future date, so we'll just print the date
    if pasttime > now_time:
        includeyear = (pasttime.year != now_time.year)
        time_str = print_date(pasttime, includeyear=includeyear, shortmonths=shortmonths)

    # Otherwise, start by getting the elapsed time as a datetime object
    else:
        elapsed_time = now_time - pasttime

        # Check if the time is within the last minute
        if elapsed_time < dt.timedelta(seconds=60):
            if elapsed_time.seconds <= minseconds:
                time_str = "just now"
            else:
                time_str = f"{elapsed_time.seconds} secs ago"

        # Check if the time is within the last hour
        elif elapsed_time < dt.timedelta(seconds=60 * 60):

            # We know that seconds > 60, so we can safely round down
            minutes = int(elapsed_time.seconds / 60)
            if minutes == 1:
                time_str = "a minute ago"
            else:
                time_str = f"{minutes} mins ago"

        # Check if the time is within the last day
        elif elapsed_time < dt.timedelta(seconds=60 * 60 * 24 - 1):

            # We know that it's at least an hour, so we can safely round down
            hours = int(elapsed_time.seconds / (60 * 60))
            if hours == 1:
                time_str = "1 hour ago"
            else:
                time_str = f"{hours} hours ago"

        # Check if it's within the last N days, where N is a user-supplied argument
        elif elapsed_time < dt.timedelta(days=maxdays):
            if elapsed_time.days == 1:
                time_str = "yesterday"
            else:
                time_str = f"{elapsed_time.days} days ago"

        # If it's not within the last N days, then we're just going to print the date
        else:
            includeyear = (pasttime.year != now_time.year)
            time_str = print_date(pasttime, includeyear=includeyear, shortmonths=shortmonths)

    return time_str



def tic():
    '''
    With toc(), a little pair of functions to calculate a time difference:

    **Examples**::

        sc.tic()
        slow_func()
        sc.toc()

        T = sc.tic()
        slow_func2()
        sc.toc(T, label='slow_func2')
    '''
    global _tictime  # The saved time is stored in this global
    _tictime = time.time()  # Store the present time in the global
    return _tictime    # Return the same stored number



def toc(start=None, output=False, label=None, sigfigs=None, filename=None, reset=False, baselabel):
    '''
    With tic(), a little pair of functions to calculate a time difference.

    Args:
        start (float): the starting time, as returned by e.g. sc.tic()
        output (bool): whether to return the output (otherwise print)
        label (str): optional label to add
        sigfigs (int): number of significant figures for time estimate
        filename (str): log file to write results to
        reset (bool): reset the time; like calling sc.toctic() or sc.tic() again

    **Examples**::

        sc.tic()
        slow_func()
        sc.toc()

        T = sc.tic()
        slow_func2()
        sc.toc(T, label='slow_func2')
    '''
    from . import sc_printing as scp # To avoid circular import
    global _tictime  # The saved time is stored in this global

    # Set defaults
    if label   is None: label = ''
    if sigfigs is None: sigfigs = 3

    # If no start value is passed in, try to grab the global _tictime.
    if start is None:
        try:    start = _tictime
        except: start = 0 # This doesn't exist, so just leave start at 0.

    # Get the elapsed time in seconds.
    elapsed = time.time() - start

    # Create the message giving the elapsed time.
    if label=='': base = 'Elapsed time: '
    else:         base = f'Elapsed time for {label}: '
    logmessage = base + f'{scp.sigfig(elapsed, sigfigs=sigfigs)} s'

    # Optionally reset the counter
    if reset:
        _tictime = time.time()  # Store the present time in the global

    if output:
        return elapsed
    else:
        if filename is not None:
            scp.printtologfile(logmessage, filename) # If we passed in a filename, append the message to that file.
        else:
            print(logmessage) # Otherwise, print the message.
        return


def toctic(returntic=False, returntoc=False, *args, **kwargs):
    '''
    A convenience function for multiple timings. Can return the default output of
    either tic() or toc() (default neither). Arguments are passed to toc(). Equivalent
    to sc.toc(reset=True).

    **Example**::

        sc.tic()
        slow_operation_1()
        sc.toctic()
        slow_operation_2()
        sc.toc()

    New in version 1.0.0.
    '''
    tocout = toc(*args, **kwargs)
    ticout = tic()
    if   returntic: return ticout
    elif returntoc: return tocout
    else:           return None


def timedsleep(delay=None, verbose=True):
    '''
    Delay for a certain amount of time, to ensure accurate timing.

    **Example**::

        for i in range(10):
            sc.timedsleep('start') # Initialize
            for j in range(int(1e6)):
                tmp = pl.rand()
            sc.timedsleep(1) # Wait for one second including computation time
    '''
    global _delaytime
    if delay is None or delay=='start':
        _delaytime = time.time()  # Store the present time in the global.
        return _delaytime         # Return the same stored number.
    else:
        try:    start = _delaytime
        except: start = time.time()
        elapsed = time.time() - start
        remaining = delay-elapsed
        if remaining>0:
            if verbose:
                print(f'Pausing for {remaining:0.1f} s')
            time.sleep(remaining)
        else:
            if verbose:
                print(f'Warning, delay less than elapsed time ({delay:0.1f} vs. {elapsed:0.1f})')
    return None


class Timer(object):
    '''
    Simple timer class

    This wraps ``tic`` and ``toc`` with the formatting arguments and
    the start time (at construction)
    Use this in a ``with...as`` block to automatically print
    elapsed time when the block finishes.

    Implementation based on https://preshing.com/20110924/timing-your-code-using-pythons-with-statement/

    Example making repeated calls to the same Timer::

        >>> timer = Timer()
        >>> timer.toc()
        Elapsed time: 2.63 s
        >>> timer.toc()
        Elapsed time: 5.00 s

    Example wrapping code using with-as::

        >>> with Timer(label='mylabel') as t:
        >>>     foo()

    '''
    def __init__(self, label=None, **kwargs):
        self.tic()
        self.kwargs = kwargs #: Store kwargs to pass to :func:`toc` at the end of the block
        self.kwargs['label'] = label
        return

    def __enter__(self):
        ''' Reset start time when entering with-as block '''
        self.tic()
        return self

    def __exit__(self, *args):
        ''' Print elapsed time when leaving a with-as block '''
        self.toc()
        return

    def tic(self):
        ''' Set start time '''
        self._start = tic()
        return

    def toc(self):
        ''' Print elapsed time '''
        toc(self._start, **self.kwargs)
        return

    def start(self):
        ''' Alias for tic() '''
        self.tic()
        return

    def stop(self):
        ''' Alias for toc() '''
        self.toc()
        return

timer = Timer # Alias