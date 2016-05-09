# standard libraries
import os
import datetime
# third party libraries
pass
# first party libraries
import bocce


__where__ = os.path.dirname(os.path.abspath(__file__))


class Response(bocce.Response):
    
    def __init__(self, c):
        super(Response, self).__init__()
        self.c = c
    
    def handle(self, request, configuration):
        self.status_code = 200
        self.body.text = self.c
        self.compress(force=True)


class FileResponse(bocce.Response):
    
    def handle(self, request, configuration):
        self.status_code = 200
        self.body.file = os.path.join(__where__, 'scratch.py')


class Error(bocce.Response):
    
    def handle(self, request, configuration):
        self.status_code = 200
        raise Exception

a = Response('a')
b = Response('b')
c = Response(1000*'c')
e = Error()
f = FileResponse()
path = os.path.join(__where__, 'static')
start = datetime.datetime.now()
s = bocce.static.Response(path, expose_directory=True, clean=True)
stop = datetime.datetime.now()
print((stop - start).total_seconds())

app = bocce.Application()
app.server_error_response.debug = True
app.routes.add_response('/a', a)
app.routes.add_response('/b', b)
app.routes.add_response('/c', c)
app.routes.add_response('/e', e)
app.routes.add_response('/s/<path>', s)
app.routes.add_response('/f', f)
app.configure()
app.logger.enable()
app.serve(interfaces=({'host': '0.0.0.0', 'port': 8080}, ))
