# standard libraries
import os
import types
import logging
import datetime
import traceback
# third party libraries
import webob
import waitress
# first party libraries
from . import (exceptions, routing, requests, )


__all__ = ('Application', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class Application:

    def __init__(self, name):
        # 
        self.name = name
        self.routes = routing.Routes()
        # configure default logger
        logger = logging.getLogger('bocce')
        logger.setLevel(logging.INFO)
        # default configuration
        self.configuration = {
                                 'logger': logger
                             }

    def __call__(self, environ, start_response):
        try:
            request = requests.Request(environ)
            route = self.routes.match(request.path)
            if isinstance(route, routing.Detour):
                raise exceptions.HTTPNotFound()
            resource = route.Resource(request, route)
            with resource:
                response = resource(request)



        except exceptions.HTTPException as response:
            # TK: get response from configuration
            exception_traceback = traceback.format_exc()
        except Exception:
            # TK: get response from configuration
            exception_traceback = traceback.format_exc()
            response = exceptions.HTTPInternalServerError()
        finally:
            self.log(request, response, exception_traceback)
            return response(environ, start_response)

    def configure(self):
        for route, handler in self.routes:
            handler.configure(self.configuration)

    def log(self, request, response, exception_traceback):
        # get logger from configuration
        logger = self.configuration.get('logger', None)
        if logger is None:
            logger = logging.NullHandler()
        # collect details from request, response, and exception traceback (if any)
        when = ':%Y-%m-%dT%H:%M:%SZ'.format(datetime.datetime.utcnow())
        status = response.status_code
        client_address = request.client_addr
        method = request.method
        path = request.path
        http_details = '{} {} {} {} {}'.format(when, client_address.ljust(15),
                                               method.ljust(7), status,
                                               path, exception_traceback)
        # no error
        if status < 400:
            logger.info(http_details)
        # client error
        elif status < 500:
            logger.warning(http_details)
        # server error
        else:
            if exception_traceback is None:
                logger.error(http_details)
            else:
                separator = 15*'='
                specifier = '\n{}\n{}\n{}\n{}\n'
                exception_details = specifier.format(separator, http_details, 
                                                     exception_traceback, separator)
                logger.error(exception_details)

    def serve(self, *args, **kwargs):
        self.configure()
        waitress.serve(self, *args, **kwargs)
