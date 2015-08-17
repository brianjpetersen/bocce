# standard libraries
import os
# third party libraries
pass
# first party libraries
pass


__all__ = ('Resource', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class Resource(object):

    @classmethod
    def configure(cls, configuration):
        pass

    def wsgify(self, environ, start_response):
        request = requests.Request(environ)
        with self:
            response = self()
        return response(environ, start_response)

    def __call__(self, request, route):
        pass

    def __enter__(self):
        pass

    def __exit__(self, *exception_tuple):
        pass
