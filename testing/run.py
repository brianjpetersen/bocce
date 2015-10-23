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



import when
__where__ = os.path.dirname(os.path.abspath(__file__))

application = bocce.Application()
application.server_error_resource = bocce.exceptions.DebugServerErrorResource
application.routes['/assets/<path>'] = bocce.StaticResource(os.path.join(__where__, 'assets'))
application.configure()

when.tic()
#request = bocce.Request.blank('http://localhost/assets/server_problem.png')
request = bocce.Request.blank('http://localhost/assets/')
request.method = 'GET'
response = request.get_response(application)
print(response)
print(when.toc())
print('')
