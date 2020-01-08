# standard libraries
import os
import traceback
import warnings
import logging
import signal
import sys
# third party libraries
import cherrypy
# first party libraries
from . import (routing, exceptions, requests, responses, utils, )


__where__ = os.path.dirname(os.path.abspath(__file__))


class Application:
    
    Request = requests.Request
    Response = responses.Response
    
    def __init__(self):
        self.routes = routing.Routes()
        self.configuration = {}
        # exceptions
        self.not_found_handler = exceptions.NotFoundHandler()
        self.server_error_handler = exceptions.ServerErrorHandler(debug=False)
        # logging
        self.logger = logging.getLogger('bocce')
        #self.logger.addHandler(logging.NullHandler())
        self.logger.setLevel(logging.INFO)
    
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
                raise self.not_found_handler
            request.route, request.segments = match
            handler = request.route.handler
            response = self.Response()
            for before in getattr(handler, 'before', []):
                before(request, response, configuration)
            handler(request, response, configuration)
        except exceptions.Handler as exception:
            handler = exception
            response = self.Response()
            response.traceback = traceback.format_exc()
            for before in getattr(handler, 'before', []):
                before(request, response, configuration)
            handler(request, response, configuration)
        except:
            handler = self.server_error_handler
            response = self.Response()
            response.traceback = traceback.format_exc()
            for before in getattr(handler, 'before', []):
                before(request, response, configuration)
            handler(request, response, configuration, traceback.format_exc())
        finally:
            for after in reversed(getattr(handler, 'after', [])):
                try:
                    after(request, response, configuration)
                except:
                    continue
            self.log(request, response, configuration)
            return response.start(start_response)
    
    def configure(self):
        for route in self.routes:
            for configure in getattr(route.handler, 'configure', []):
                configure(self.configuration)
        for configure in getattr(self.not_found_handler, 'configure', []):
            configure(self.configuration)
        for configure in getattr(self.server_error_handler, 'configure', []):
            configure(self.configuration)
    
    def log(self, request, response, configuration):
        # collect details from request, response, and exception traceback (if any)
        http_details = '{} {} {} {}'.format(
            utils.When.timestamp(),
            response.status_code,
            request.http.method.ljust(7),
            '/{}'.format(request.url.path),
        )
        # no error
        if response.status_code < 400:
            self.logger.info(http_details)
        # client error
        elif response.status_code < 500:
            self.logger.warning(http_details)
        # server error
        else:
            traceback = getattr(response, 'traceback', '')
            formatted_traceback = '    ' + ('\n    ').join(traceback.split('\n'))
            formatted_traceback = '\n'.join(
                [line for line in formatted_traceback.splitlines() if line.strip()]
            )
            specifier = '{}\n\n{}\n'
            exception_details = specifier.format(http_details, formatted_traceback)
            self.logger.error(exception_details)
    
    def enable_logging(self, handler=logging.StreamHandler(), level=logging.INFO):
        handler.setLevel(level)
        self.logger.addHandler(handler)
    
    def daemonize(self, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        sys.stdout.flush()
        sys.stderr.flush()
        pid = os.fork()
        if pid > 0:
            # this is the parent process
            os._exit(0)
        os.setsid()
        pid = os.fork()
        if pid > 0:
            # this is the parent process
            os._exit(0)
        os.chdir('/')
        os.umask(0)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        stdin = open(stdin, 'r')
        stdout = open(stdout, 'a+')
        stderr = open(stderr, 'a+')
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())
        
    def serve(self, interfaces=({'host': '127.0.0.1', 'port': 8080}, ), drop_privileges=True):
        
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
        
        with open('PID', 'wb') as f:
            f.write(pid.encode('ascii'))
        
        for interface in interfaces:
            host = interface.get('host', '127.0.0.1')
            port = interface.get('port', 8080)
            threads = interface.get('threads', 16)
            ssl_certificate = interface.get('ssl_certificate', None)
            ssl_private_key = interface.get('ssl_private_key', None)
            
            self.logger.info('    {}:{}'.format(host, port))
            server = cherrypy._cpserver.Server()
            server.socket_host = host
            server.socket_port = port
            server.thread_pool = threads
            
            if ssl_certificate is not None and ssl_private_key is not None:
                server.ssl_module = 'builtin'
                server.ssl_certificate = ssl_certificate
                server.ssl_private_key = ssl_private_key
            
            server.subscribe()
        
        cherrypy.log.access_log.setLevel(logging.ERROR)
        cherrypy.log.error_log.setLevel(logging.ERROR)
        cherrypy.engine.autoreload.unsubscribe()

        if drop_privileges:
            uid = int(os.environ['SUDO_UID'])
            gid = int(os.environ['SUDO_GID'])
            if uid == 0:
                uid = 1000
            if gid == 0:
                gid = 1000
            cherrypy.process.plugins.DropPrivileges(cherrypy.engine, uid=uid, gid=gid).subscribe()

        try:
            cherrypy.engine.start()
            cherrypy.engine.block()
        finally:
            when = utils.When.timestamp()
            self.logger.info('Server stopped at {}.'.format(when))
