# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (resources, responses, )


__all__ = (
    '__where__',
    'NotFound',
    'ServerError',
    'BadRequest',
    'DebugServerError',
)
__where__ = os.path.dirname(os.path.abspath(__file__))


class Response(responses.Response, Exception):
    
    def __init__(self):
        super(Response, self).__init__()


class Resource(resources.Resource, Exception):
    
    def __init__(self, request, route):
        super(Resource, self).__init__(request, route)


class NotFoundResource(Resource):

    def __init__(self, request):
        super(NotFoundResource, self).__init__(request, None)
        
    def __call__(self):
        response = responses.Response()
        response.status = '404 Not Found'
        return response


class ServerErrorResource(Resource):

    def __init__(self, request, exception):
        super(ServerErrorResource, self).__init__(request, None)
        self.exception = exception
        
    def __call__(self):
        response = responses.Response()
        response.status = '500 Internal Server Error'
        return response


class DebugServerErrorResource(ServerErrorResource):
    
    def __init__(self, request, exception):
        super(DebugServerErrorResource, self).__init__(request, exception)
        
    def __call__(self):
        response = responses.Response()
        response.status = '500 Internal Server Error'
        response.body = self.exception['traceback']
        return response
