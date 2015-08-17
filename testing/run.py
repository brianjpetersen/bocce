# standard libraries
import os
import doctest
# third party libraries
pass
# first party libraries
pass


##doctest.testfile('routing.md')

"""
import bocce

routes_1 = bocce.Routes()
routes_1['/a'] = 'routes_1: /a'

routes = bocce.Routes()
routes['/'] = routes_1

for path in routes:
    print(repr(path))
"""

import webob
import cherrypy.wsgiserver
import waitress

def wsgi_app(environ, start_response):
    request = webob.Request(environ)
    response = webob.Response()
    print(request.path)
    return response(environ, start_response)

#waitress.serve(wsgi_app)

d = cherrypy.wsgiserver.WSGIPathInfoDispatcher({'/': wsgi_app})
server = cherrypy.wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8080), d)

try:
  server.start()
except KeyboardInterrupt:
  server.stop()