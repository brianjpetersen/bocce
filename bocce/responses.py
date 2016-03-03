# standard libraries
import os
import abc
import collections
import copy
import json
# third party libraries
import werkzeug
# first party libraries
from . import (logging, surly, utils, headers, )
Headers = headers.Mutable


__where__ = os.path.dirname(os.path.abspath(__file__))


class Cookie:
    
    pass


class Cookies(collections.abc.MutableMapping):
    
    def __init__(self, _response):
        self._response = _response
        self._cookies = {}
    
    def set(self, key, value='', max_age=None, expires=None, path='/', 
            domain=None, secure=None, httponly=False):
        self._response.set_cookie(
            key, value, max_age, expires, path, domain, secure, httponly,
        )
    
    def __setitem__(self, ):
        pass


def log(request, response, configuration):
    # collect details from request, response, and exception traceback (if any)
    http_details = '{} {} {} {}'.format(
        utils.timestamp(),
        response.status_code,
        request.method.ljust(7),
        request.url.path,
    )
    # no error
    if response.status_code < 400:
        logging.logger.info(http_details)
    # client error
    elif response.status_code < 500:
        logging.logger.warning(http_details)
    # server error
    else:
        exception = getattr(response, 'traceback', '')
        formatted_traceback = _remove_blanks(_indent(exception_traceback))
        specifier = '{}\n\n{}\n'
        exception_details = specifier.format(http_details, formatted_traceback)
        logging.logger.error(exception_details)


class Response:
    
    configure = []
    before = []
    after = [log, ]
    
    def __init__(self):
        self.configure = copy.deepcopy(self.configure)
        self.before = copy.deepcopy(self.before)
        self.after = copy.deepcopy(self.after)
        # abstract over response
        _response = self._response = werkzeug.Response()
        self.headers = _response.headers
        # status_code
        # status
        
        
        
    def handle(self, request, configuration):
        pass
    
    def respond(self, environment, start_response):
        self._response(environment, start_response)


Response = werkzeug.Response
