# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (application, exceptions, caching, routing, paths, resources, static,
               requests, responses, surly)


__where__ = os.path.dirname(os.path.abspath(__file__))
__all__ = ('Application', 'Routes', 'Path', 'Resource', 'StaticResource', 'Request', 
           'application', 'exceptions', 'routing', 'caching', 'paths', 
           'Response', 'resources', 'surly',
           '__where__', '__version__', )


with open(os.path.join(__where__, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()


Application = application.Application
Routes = routing.Routes
Path = paths.Path
Resource = resources.Resource
StaticResource = static.Resource
Request = requests.Request
Response = responses.Response
