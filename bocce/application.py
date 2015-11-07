# standard libraries
import os
import sys
import time
import types
import logging
import datetime
import traceback
# third party libraries
import webob
import rocket
# first party libraries
from . import (exceptions, routing, requests, )


__all__ = ('__where__', 'Application', )
__where__ = os.path.dirname(os.path.abspath(__file__))


def indent(string, number=4, char=' '):
    indent = number * char
    return indent + ('\n' + indent).join(string.split('\n'))


def remove_blanks(string):
    return '\n'.join([line for line in string.splitlines() if line.strip()])


class Application:

    def __init__(self):
        self.routes = routing.Routes()
        self.configuration = {}
        # configure default logger
        self.logger = logging.getLogger('bocce')
        handler = logging.NullHandler()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        # exception resources
        self.not_found_resource = exceptions.NotFoundResource
        self.server_error_resource = exceptions.ServerErrorResource
        # allow subclassing of Response class
        self.Request = requests.Request

    def __call__(self, environ, start_response):
        try:
            request = self.Request(environ)
            route = request.route = self.routes.match(request.path)
            if isinstance(route, routing.Detour):
                resource = self.not_found_resource(request)
            else:
                resource = route.resource(request, route)
            with resource as (handler, kwargs):
                response = handler(**kwargs)
        except exceptions.Response as response:
            pass
        except:
            exception = {}
            exception['type'], exception['value'], _ = sys.exc_info()
            exception['traceback'] = traceback.format_exc()
            with self.server_error_resource(request, exception) as (handler, kwargs):
                response = handler(**kwargs)
        finally:
            self.log(request, response)
            return response(environ, start_response)

    def configure(self):
        routes = {}
        for path in self.routes:
            Route = self.routes[path]
            routes[id(Route)] = Route
        do_nothing = lambda configuration: None
        for Route in routes.values():
            configure = getattr(Route, 'configure', do_nothing)
            configure(self.configuration)
        for resource in (self.not_found_resource, self.server_error_resource):
            try:
                configure = getattr(resource, 'configure', do_nothing)
                configure(self.configuration)
            except:
                pass

    def log(self, request, response):
        # collect details from request, response, and exception traceback (if any)
        when = datetime.datetime.utcnow().strftime('%Y-%M-%dT%H:%m:%SZ')
        status = response.status_code
        client_address = request.client_addr
        method = request.method
        path = request.path_qs
        http_details = '{} {} {} {}'.format(when, status, method.ljust(7), path)
        # no error
        if status < 400:
            self.logger.info(http_details)
        # client error
        elif status < 500:
            self.logger.warning(http_details)
        # server error
        else:
            exception = getattr(response, 'exception', {})
            exception_traceback = exception.get('traceback', '')
            formatted_traceback = remove_blanks(indent(exception_traceback))
            specifier = '{}\n\n{}\n'
            exception_details = specifier.format(http_details, formatted_traceback)
            self.logger.error(exception_details)

    def log_to_console(self, level=logging.INFO):
        handler = logging.StreamHandler()
        self.logger.addHandler(handler)
        handler.setLevel(level)

    def serve(self, interfaces=[('0.0.0.0', 8080), ], min_threads=1, max_threads=16, timeout=600):
        server = rocket.Rocket(
            interfaces, 
            'wsgi', 
            {"wsgi_app": self},
            min_threads,
            max_threads,
            None, # queue_size: auto-discover
            timeout,
        )
        # disable server logger for all but errors
        _logger = logging.getLogger('Rocket')
        _logger.setLevel(logging.ERROR)
        # log and start the server
        when = datetime.datetime.utcnow().strftime('%Y-%M-%dT%H:%m:%SZ')
        self.logger.info('Server started at {} on the following interfaces:'.format(when))
        for interface in interfaces:
            ip_address, port = interface[0], interface[1]
            self.logger.info('    {}:{}'.format(ip_address, port))
        self.logger.info('')
        server.start()
