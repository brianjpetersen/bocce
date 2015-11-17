# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (requests, responses, )


__all__ = ('Resource', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class Resource(object):

    def __init__(self, request, route):
        self.request = request
        self.route = route
        self.response = responses.Response()
        # ideally, this would be imported above; however, this leads to a 
        # circular import (because exceptions relies on the base resource,
        # and the base resource handler needs access to the exceptions base
        # response).
        from . import exceptions
        self.exceptions = exceptions

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

    def require_https(self):
        if self.request.url.scheme != 'https':
            response = self.exceptions.Response()
            response.status = '301 Moved Permanently'
            response.location = str(
                self.request.url.replace(scheme='https', port=443)
            )
            raise response
        # require https for all future requests on this domain
        self.response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    
    def secure(self):
        response = self.response
        # enable cross-site-scripting filter (on by default in most cases)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # click-jacking protection
        response.headers['X-Frame-Options'] = 'sameorigin'
        response.headers['Frame-Options'] = 'sameorigin'
        """
        # content security policy; deny from all except this domain
        content_security_policy = 'script-src {0}; child-src {0}; connect-src {0}; ' \
            'font-src {0}; media-src {0}; object-src {0}; style-src {0}; ' \
            'upgrade-insecure-requests'.format(
                self.url.replace()
        ) #'*.example.com:*'
        """

    def __call__(self, **kwargs):
        if self.configuration.get('secure', False):
            self.require_https()
            self.secure()
        return self.response

    def __enter__(self):
        return self, {}

    def __exit__(self, exception_type, exception_value, exception_traceback):
        pass
