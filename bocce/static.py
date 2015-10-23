# standard libraries
import os
import mimetypes
import zlib
# third party libraries
pass
# first party libraries
from . import (responses, resources, exceptions, )


__all__ = ('Resource', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults


def Resource(path):#, cache=True):
    
    class Resource(resources.Resource):
        
        @classmethod
        def configure(cls, configuration):
            super(Resource, cls).configure(configuration)

        def __init__(self, request, route):
            super(Resource, self).__init__(request, route)
            self.response = responses.Response()

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
            print(path)
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
    
    Resource.path = os.path.abspath(path)
    Resource.is_file = os.path.isfile(path)
    
    return Resource
