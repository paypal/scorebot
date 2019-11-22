import logging

from django.utils import timezone

_logger = logging.getLogger(__name__)


def is_time_up(time_allowed_since_last_check, last_checked_time, minutes=True):
    """
    Test if the time is up using the last_checked_time + time_allowed_since_last_check compared to timezone.now().
    time_allowed_since_last_check is in minutes if minutes == True else seconds.

    :param time_allowed_since_last_check: the time allowed since last checked time (in mins or secs - must be int)
    :param last_checked_time: the last time (timezone.now()) it was run
    :param minutes: Boolean:
        True if time_allowed_since_last_check is in minutes
        False if time_allowed_since_last_check is in seconds
    :return Boolean: True if the time is up (or the last checked time is None) else False
    """
    time_is_up = True

    if last_checked_time:
        time_allowed = time_allowed_since_last_check
        if minutes:
            time_offset = timezone.timedelta(minutes=time_allowed)
        else:
            time_offset = timezone.timedelta(seconds=time_allowed)
        last_check = last_checked_time + time_offset
        if last_check > timezone.now():
            time_is_up = False

    return time_is_up
