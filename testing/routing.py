# standard libraries
import datetime
# third party libraries
import pytest
# first party libraries
import bocce.routing as routing


routes = routing.Routes()
handler = lambda request, handler: None
routes.add_handler('/patients/', handler)
routes.add_handler('/patients/{patient_id}', handler)

print(routes.match('patients/', 'GET'))
print(routes.match('patients/test', 'GET'))
