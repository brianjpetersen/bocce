# standard libraries
import os
import abc
# third party libraries
pass
# first party libraries
from . import (responses, )


__where__ = os.path.dirname(os.path.abspath(__file__))


template = \
'''
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <title>{status}</title>
        <link href='https://fonts.googleapis.com/css?family=Varela+Round'
              rel='stylesheet' type='text/css'>
        <link href='https://fonts.googleapis.com/css?family=Roboto+Mono' 
              rel='stylesheet' type='text/css'>
        <style type="text/css">
            body{{
                background-color: #f1f1f1;
                font-family: 'Varela Round', sans-serif;
                color: #252226;
            }}
            .traceback{{
                font-family: 'Roboto Mono', monospace;
            }}
            hr{{
                color: #252226;
                background-color: #252226;
            }}
        </style>
    </head>
    <body>
        <h1>{status}</h1>
        <p>{message}</p>
        {traceback}
    </body>
</html>
'''


class Handler(Exception, metaclass=abc.ABCMeta):
    
    def __init__(self):
        super(Handler, self).__init__()
    
    @abc.abstractmethod
    def __call__(self, request, response, configuration):
        pass


class NotFoundHandler(Handler):
    
    def __call__(self, request, response, configuration):
        response.status_code = 404
        message = 'The requested URL /{} for method {} was not found on this server.'
        message = message.format(request.url.path, request.http.method)
        response.body.html = template.format(
            status=response.status, message=message, traceback=''
        )


class ServerErrorHandler(Handler):
    
    def __init__(self, debug=False):
        super(ServerErrorHandler, self).__init__()
        self.debug = debug
    
    def __call__(self, request, response, configuration, traceback=None):
        response.status_code = 500
        message = 'An unknown server error has occurred.'
        if self.debug and traceback is not None:
            traceback = '<pre id="traceback">{}</pre>'.format(traceback)
        response.body.html = template.format(
            status=response.status, message=message, traceback=traceback
        )
