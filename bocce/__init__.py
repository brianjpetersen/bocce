# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (application, routing, static, surly, requests, responses, 
               utils, cookies, exceptions, middleware, )


__where__ = os.path.dirname(os.path.abspath(__file__))
__all__ = ('Application', 'application', 'routing', 'Route', 'Routes',
           'Request', 'Response', 'exceptions', 'surly', 'Url')


with open(os.path.join(__where__, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()


Route = routing.Route
Routes = routing.Routes
Application = application.Application
Url = surly.Url
Request = requests.Request
Response = responses.Response
