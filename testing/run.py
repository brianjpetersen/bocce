# standard libraries
import os
import doctest
# third party libraries
pass
# first party libraries
pass

import bocce
#doctest.testfile('routing.md')
#doctest.testfile('resources.md')

routes = bocce.Routes()
routes['a/{b}'] = 'a/{b}'
routes['{a}/{b}'] = '{a}/{b}'
routes['<a>'] = '<a>'
match = routes.match('a/b')
print(match.resource)
'a/{b}'
print(match.segments)
{'b': 'b'}
