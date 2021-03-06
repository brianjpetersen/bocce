# standard libraries
import os
import datetime
# third party libraries
pass
# first party libraries
import bocce


__where__ = os.path.dirname(os.path.abspath(__file__))


class Handler:
    
    after = [bocce.middleware.compress, ]
    
    def __init__(self, c):
        super(Handler, self).__init__()
        self.c = c
    
    def __call__(self, request, response, configuration):
        response.status_code = 200
        response.body.text = self.c


class JsonHandler:
    
    after = [bocce.middleware.compress, ]
    
    def __call__(self, request, response, configuration):
        response.status_code = 200
        response.body.json.indent = 4
        response.body.json['a'] = 1000*'a'


class FileHandler:
    
    def __call__(self, request, response, configuration):
        response.status_code = 200
        response.body.file = os.path.join(__where__, 'scratch.py')


class JsonEchoHandler:

    def __call__(self, request, response, configuration):
        response.body.json = request.body.json


class Error:
    
    def __call__(self, request, response, configuration):
        response.status_code = 200
        raise Exception


a = Handler('a')
b = Handler('b')
c = Handler(1000*'c')
e = Error()
f = FileHandler()
j = JsonHandler()
je = JsonEchoHandler()
path = os.path.join(__where__, 'static')
start = datetime.datetime.now()
s = bocce.static.Handler(path, expose_directory=True, clean=True)
stop = datetime.datetime.now()
print((stop - start).total_seconds())

path = os.path.join(__where__, 'static', 'assets', 'jquery.js')
s1 = bocce.static.Handler(path)


app = bocce.Application()
app.server_error_handler.debug = True
app.routes.add_handler('/a', a)
app.routes.add_handler('/b', b)
app.routes.add_handler('/c', c)
app.routes.add_handler('/e', e)
app.routes.add_handler('/s/<path>', s)
app.routes.add_handler('/s1', s1)
app.routes.add_handler('/f', f)
app.routes.add_handler('/j', j)
app.routes.add_handler('/je', je)

app.configure()
app.enable_logging()
app.serve(interfaces=({'host': '0.0.0.0', 'port': 8080}, ))
