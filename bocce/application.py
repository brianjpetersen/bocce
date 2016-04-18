# standard libraries
import os
import traceback
import warnings
# third party libraries
import cherrypy
# first party libraries
from . import (routing, exceptions, requests, responses, utils, logging, )


__where__ = os.path.dirname(os.path.abspath(__file__))


class Application:
    
    Request = requests.Request
    
    def __init__(self):
        self.logger = logging.logger
        self.routes = routing.Routes()
        self.configuration = {}
        self.not_found_response = exceptions.NotFoundResponse()
        self.server_error_response = exceptions.ServerErrorResponse(debug=False)
    
    def __call__(self, environment, start_response):
        try:
            configuration = self.configuration
            request = self.Request.from_environment(environment)
            match = self.routes.match(
                request.url.path,
                request.http.method,
                request.url.subdomain,
            )
            if match is None:
                request.route = request.segments = None
                raise self.not_found_response
            request.route, request.segments = match
            response = request.route.response
            for before in response.before:
                before(request, response, configuration)
            response.handle(request, configuration)
        except exceptions.Response as exception:
            response = exception
            response.traceback = traceback.format_exc()
            response.handle(request, configuration)
        except:
            response = self.server_error_response
            response.traceback = traceback.format_exc()
            response.handle(request, configuration)
        finally:
            for after in reversed(response.after):
                try:
                    after(request, response, configuration)
                except:
                    continue
            return response.start(start_response)
    
    def configure(self):
        for route in self.routes:
            configure = getattr(route.response, 'configure', [])
            for f in configure:
                f(self.configuration)
        configure = getattr(self.not_found_response, 'configure', [])
        for f in configure:
            f(self.configuration)
        configure = getattr(self.server_error_response, 'configure', [])
        for f in configure:
            f(self.configuration)
    
    def serve(self, interfaces=({'host': '127.0.0.1', 'port': 8080}, )):
        
        if tuple(cherrypy.__version__.split('.')) < ('3', '8', '0'):
            warnings.warn(
                'Upgrade to a newer version of cherrypy (> v3.8.0) to avoid '
                'buggy behavior.'
            )
        
        cherrypy.tree.graft(self, '/')
        cherrypy.server.unsubscribe()
        
        when = utils.When.timestamp()
        pid = str(os.getpid())
        self.logger.info(
            'Started at {} in PID {} on the following interfaces:'.format(
                when, pid
            )
        )
        
        for interface in interfaces:
            host = interface.get('host', '127.0.0.1')
            port = interface.get('port', 8080)
            threads = interface.get('threads', 16)
            ssl_certificate = interface.get('ssl_certificate', None)
            ssl_private_key = interface.get('ssl_private_key', None)
            
            logging.logger.info('    {}:{}'.format(host, port))
            server = cherrypy._cpserver.Server()
            server.socket_host = host
            server.socket_port = port
            server.thread_pool = threads
            
            if ssl_certificate is not None and ssl_private_key is not None:
                server.ssl_module = 'builtin'
                server.ssl_certificate = ssl_certificate
                server.ssl_private_key = ssl_private_key
            
            server.subscribe()
        
        cherrypy.log.access_log.setLevel(logging.logging.ERROR)
        cherrypy.log.error_log.setLevel(logging.logging.ERROR)
        cherrypy.engine.autoreload.unsubscribe()
        
        try:
            cherrypy.engine.start()
            cherrypy.engine.block()
        finally:
            when = utils.When.timestamp()
            self.logger.info('Server stopped at {}.'.format(when))
