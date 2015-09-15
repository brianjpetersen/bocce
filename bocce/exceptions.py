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

    @classmethod
    def configure(cls, configuration):
        pass

    def __init__(self):
        super(Response, self).__init__()


class NotFoundResponse(Response):

    def __init__(self, request):
        super(NotFoundResponse, self).__init__()
        self.status = '404 Not Found'


class ServerErrorResponse(Response):

    def __init__(self, request, exception):
        super(ServerErrorResponse, self).__init__()
        self.exception = exception
        self.status = '500 Internal Server Error'


class DebugServerErrorResponse(ServerErrorResponse):

    def __init__(self, request, exception):
        super(DebugServerErrorResponse, self).__init__(request, exception)
        self.body = exception['traceback']


# deprecate?

class MethodNotAllowedResponse(Response):

    def __init__(self):
        super(MethodNotAllowedResponse, self).__init__()
        self.status = '405 Method Not Allowed'


class BadRequestResponse(Response):

    def __init__(self):
        super(BadRequestResponse, self).__init__()
        self.status = '400 Bad Request'
