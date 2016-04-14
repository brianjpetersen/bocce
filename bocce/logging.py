# standard libraries
import os
import logging
# third party libraries
pass
# first party libraries
from . import (utils, )


__where__ = os.path.dirname(os.path.abspath(__file__))


def _indent(s, number=4, char=' '):
    indent = number * char
    return indent + ('\n' + indent).join(s.split('\n'))


def _remove_blanks(s):
    return '\n'.join([line for line in s.splitlines() if line.strip()])


# configure default logger
logger = logging.getLogger('bocce')
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.INFO)


def enable(level=logging.INFO, handler=logging.StreamHandler()):
    logger.addHandler(handler)
    handler.setLevel(level)


logger.enable = enable


def log(request, response, configuration):
    # collect details from request, response, and exception traceback (if any)
    http_details = '{} {} {} {}'.format(
        utils.When.timestamp(),
        response.status_code,
        request.http.method.ljust(7),
        '/{}'.format(request.url.path),
    )
    # no error
    if response.status_code < 400:
        logger.info(http_details)
    # client error
    elif response.status_code < 500:
        logger.warning(http_details)
    # server error
    else:
        traceback = getattr(response, 'traceback', '')
        formatted_traceback = _remove_blanks(_indent(traceback))
        specifier = '{}\n\n{}\n'
        exception_details = specifier.format(http_details, formatted_traceback)
        logger.error(exception_details)
