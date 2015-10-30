# standard libraries
import os
import doctest
import when
import sys
# third party libraries
pass
# first party libraries
import bocce


#doctest.testfile('routing.md', optionflags=doctest.ELLIPSIS)
#doctest.testfile('application.md', optionflags=doctest.ELLIPSIS)
#doctest.testmod(bocce.surly)


routes = bocce.Routes(cache=False)
routes['/'] = '/'
routes['/assets/public/<path>'] = '/assets/public/<path>'

print(routes.match('').resource)


sys.exit()


__where__ = os.path.dirname(os.path.abspath(__file__))

application = bocce.Application()
application.server_error_resource = bocce.exceptions.DebugServerErrorResource
#static_path = os.path.join(__where__, 'assets')
static_path = '/Users/brianjpetersen/Desktop/podimetrics/frontend_common_assets'
application.routes['/assets/<path>'] = bocce.StaticResource(static_path, expose_directories=True, cleanup_cache=False)
application.configure()

application.serve()

"""
when.tic()
request = bocce.Request.blank('http://localhost/assets/server_problem.png')
#request = bocce.Request.blank('http://localhost/assets')
request.method = 'GET'
response = request.get_response(application)

#with open('test.png', 'wb') as f:
#    f.write(response.body)

#mpl.figure()
#mpl.imshow(img.imread('test.png'))
#mpl.show()

#print(response)
print(when.toc())
print('')
"""