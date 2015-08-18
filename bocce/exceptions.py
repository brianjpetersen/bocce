# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (responses, )


__all__ = ('Response', 'NotFound', 'MethodNotAllowed', 'ServerError', 
           'BadRequest', 'DebugServerError', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class Response(responses.Response, Exception):

    def __init__(self, status):
        responses.Response.__init__(self)
        self.status = status


class NotFound(Response):

    def __init__(self, request, route):
        Response.__init__(self, '404 Not Found')


class ServerError(responses.Response, Exception):

    def __init__(self, request, route, exception):
        responses.Response.__init__(self)
        self.exception = exception
        self.status = '500 Internal Server Error'


class DebugServerError(ServerError):

    def __init__(self, request, route, exception):
        ServerError.__init__(self, request, route, exception)
        self.body = exception['traceback']


# deprecate?

class MethodNotAllowed(Response):

    def __init__(self):
        Response.__init__(self, '405 Method Not Allowed')


class BadRequest(Response):

    def __init__(self):
        Response.__init__(self, '400 Bad Request')
