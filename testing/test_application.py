# standard libraries
import json
# third party libraries
pass
# first party libraries
import bocce


class Response(bocce.Response):
    
    def __init__(self, c):
        super(Response, self).__init__()
        self.c = c
    
    def handle(self, request, configuration):
        self.status_code = 200
        self.body.text = self.c

class Error(bocce.Response):
    
    def handle(self, request, configuration):
        self.status_code = 200
        raise Exception

a = Response('a')
b = Response('b')
e = Error()


app = bocce.Application()
app.server_error_response.debug = True
app.routes.add_response('/a', a, subdomains=('podimetrics-brianjpetersen', ))
app.routes.add_response('/b', b, subdomains=('podimetrics-brianjpetersen', ))
app.routes.add_response('/e', e, subdomains=('podimetrics-brianjpetersen', ))
app.configure()
app.logger.enable()
app.serve(interfaces=({'host': '0.0.0.0', 'port': 8080}, ))
