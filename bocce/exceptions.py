# standard libraries
import os
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


class Response(responses.Response, Exception):
    
    def __init__(self):
        super(Response, self).__init__()


class NotFoundResponse(Response):
        
    def handle(self):
        self.status = status = '404 Not Found'
        self.content_type = 'text/html'
        self.body = template.format(status, message, traceback=None)


class ServerErrorResponse(Response):
    
    def __init__(self, debug=False):
        super(ServerErrorResponse, self).__init__()
        self.debug = debug
        
    def handle(self):
        self.status = status = '500 Internal Server Error'
        self.content_type = 'text/html'
        if self.debug:
            traceback = '<pre id="traceback">{traceback}</pre>'.format(
                self.traceback
            )
        else:
            traceback = ''
        self.body = template.format(status, message, traceback)
