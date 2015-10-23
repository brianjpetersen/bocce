# standard libraries
import os
import mimetypes
import zlib
# third party libraries
pass
# first party libraries
from . import (requests, responses)#, exceptions, )


__all__ = ('Resource', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class Resource(object):

    def __init__(self, request, route):
        self.request = request
        self.route = route

    @classmethod
    def configure(cls, configuration):
        cls.configuration = configuration

    @classmethod
    def wsgify(cls, environ, start_response):
        request = requests.Request(environ)
        resource = cls(request, None)
        with resource as (handler, kwargs):
            response = handler(**kwargs)
        return response(environ, start_response)

    def __call__(self, **kwargs):
        response = responses.Response()
        return response

    def __enter__(self):
        return self, {}

    def __exit__(self, exception_type, exception_value, exception_traceback):
        pass


mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults


def StaticResource(path):#, cache=True):
    
    class StaticResource(Resource):
        
        path = os.path.abspath(path)
        is_file = os.path.isfile(path)
        
        @classmethod
        def configure(cls, configuration):
            super(StaticResource, cls).configure(configuration)
        
        def __init__(self, request, route):
            self.request = request
            self.route = route
            self.response = bocce.Response()
        
        @property
        def method_not_allowed_response(self):
            response = exceptions.Response()
        
        def compress(self, minimum_size=999, level=2):
            should_be_compressed = (
                'gzip' in self.request.accept_encoding and \
                len(self.response.body) > minimum_size
            )
            if should_be_compressed:
                self.response.body = zlib.compress(self.response.body, level)
                self.response.content_encoding = 'gzip'
        
        def __enter__(self):
            return self, {'path': '/'.join(self.route.matches.get('path', ('', )))}
        
        def __call__(self, path):
            if self.request.method.upper() != 'GET':
                # 405 Method Not Allowed
                raise self.method_not_allowed_response
            if self.is_file and path not in ('', None):
                # 404 Not Found
                raise self.not_found_response
            if self.is_file:
                path = self.path
            else:
                # get absolute path for resource requested
                path = os.path.abspath(os.path.join(self.path, path))
            if path < self.path:
                # 403 Forbidden
                raise self.forbidden_response
            # check if path is a file or directory and respond as appropriate
            if os.path.isfile(path):
                # return file to client
                self.response.content_type, _ = mimetypes.guess_type(path)
                with open(path, 'rb') as f:
                    self.response.body = f.read()
            else:
                self.response.body = '\n'.join(os.listdir(path))
            self.compress()
            return self.response
    
    return StaticResource
