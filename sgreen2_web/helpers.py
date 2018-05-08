import time

from pyramid.request import Request


def process_start_time_end_time(request: Request) -> tuple:
    """
    Gets start and end times from request and returns them
    as ints
    :param request: the Pyramid request
    :return:
    """
    # defaults to 10 min ago - current time
    start_time = (int(time.time()) - 10 * 60) * 1000
    end_time = int(time.time()) * 1000

    # get optional query params
    try:
        if "start_time" in request.GET.keys():
            start_time = int(request.GET.getone("start_time"))

        if "end_time" in request.GET.keys():
            end_time = int(request.GET.getone("end_time"))
    except ValueError:
        raise ValueError("start_time and end_time must be integers")

    return start_time, end_time


def get_timestamp() -> int:
    return int(time.time()) * 1000
