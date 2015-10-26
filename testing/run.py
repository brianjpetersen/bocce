# standard libraries
import os
import doctest
# third party libraries
pass
# first party libraries
import bocce


doctest.testfile('routing.md', optionflags=doctest.ELLIPSIS)
doctest.testfile('application.md', optionflags=doctest.ELLIPSIS)
doctest.testmod(bocce.surly)

import sys

sys.exit()

class EchoPathResource(bocce.Resource):
    
    def __call__(self):
        response = bocce.Response()
        response.body = str(self.route.segments)
        return response


routes = bocce.Routes(cache=False)
routes['/<test>'] = '/<test>'
routes['/a/<test>'] = '/a/<test>'
match = routes.match('/')
print(match.resource, match.segments)



import when
import matplotlib.image as img
import matplotlib.pyplot as mpl
__where__ = os.path.dirname(os.path.abspath(__file__))

application = bocce.Application()
application.server_error_resource = bocce.exceptions.DebugServerErrorResource
application.routes['/assets/<path>'] = bocce.StaticResource(os.path.join(__where__, 'assets'))
#application.routes['/assets/<path>'] = bocce.StaticResource(os.path.join(__where__, 'assets'))
#application.routes['/assets/'] = bocce.StaticResource(os.path.join(__where__, 'assets'))
application.configure()

application.serve()

sys.exit()

when.tic()
#request = bocce.Request.blank('http://localhost/assets/server_problem.png')
request = bocce.Request.blank('http://localhost/assets/')
request.method = 'GET'
response = request.get_response(application)

#with open('test.png', 'wb') as f:
#    f.write(response.body)

#mpl.figure()
#mpl.imshow(img.imread('test.png'))
#mpl.show()

print(response)
print(when.toc())
print('')
