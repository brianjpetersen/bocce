# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (requests, responses, )


__all__ = ('Resource', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class Resource(object):

    def __init__(self, request, route):
        self.request = request
        self.route = route

    @classmethod
    def configure(cls, configuration):
        pass

    @classmethod
    def wsgify(cls, environ, start_response):
        request = requests.Request(environ)
        resource = cls(request, None)
        with resource as (handler, kwargs):
            response = handler(**kwargs)
        return response(environ, start_response)

    def __call__(self):
        response = responses.Response()
        return response

    def __enter__(self):
        return self, {}

    def __exit__(self, exception_type, exception_value, exception_traceback):
        pass
