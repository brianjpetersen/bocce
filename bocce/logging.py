# standard libraries
import os
import logging
# third party libraries
pass
# first party libraries
from . import (utils, )


__where__ = os.path.dirname(os.path.abspath(__file__))


"""
def _indent(s, number=4, char=' '):
    indent = number * char
    return indent + ('\n' + indent).join(s.split('\n'))


def _remove_blanks(s):
    return '\n'.join([line for line in s.splitlines() if line.strip()])


        self._components = collections.OrderedDict([
            ('host', host),
            ('path', path),
            ('scheme', scheme),
            ('query_string', query_string),
            ('port', port),
            ('fragment', fragment),
            ('user', user),
            ('password', password),
        ])
"""


# configure default logger
logger = logging.getLogger('bocce')
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.INFO)


def enable(level=logging.INFO, handler=logging.StreamHandler()):
    logger.addHandler(handler)
    handler.setLevel(level)

