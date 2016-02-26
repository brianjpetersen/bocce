# standard libraries
import os
import abc
import collections
import copy
# third party libraries
import werkzeug
# first party libraries
from . import (logging, surly, )


__where__ = os.path.dirname(os.path.abspath(__file__))


Content = collections.namedtuple(
    'Content', ('type', 'mimetype', 'length', 'encoding', 'md5', 'charset', )
)


Accept = collections.namedtuple(
    'Accept', ('charsets', 'encodings', 'languages', 'mimetypes', )
)

class Request(tuple):
    
    __slots__ = ()
    
    def __new__(cls, environment):
        _request = werkzeug.Request(environment)
        method = _request.method
        headers = _request.headers
        url = surly.Url.from_string(_request.url)
        cookies = _request.cookies
        date = _request.date
        content = Content(
            _request.content_type,
            _request.mimetype,
            _request.content_length,
            _request.content_encoding,
            _request.content_md5,
            _request.charset,
        )
        accept = Accept(
            _request.accept_charsets,
            _request.accept_encodings,
            _request.accept_languages,
            _request.accept_mimetypes,
        )
        pragma = _request.pragma
        user_agent = _request.user_agent
        self.close = self._request.close # is this necessary?
        #self.files = self._request.files
        #self.form = self._request.form
    
    @property
    def body(self):
        return 
    
    def __getnewargs__(self):
        return tuple(self)


class Response(metaclass=abc.ABCMeta):
    
    configure = []
    before = []
    after = [logging.log_http, ]
    
    def __init__(self):
        self.configure = copy.deepcopy(self.configure)
        self.before = copy.deepcopy(self.before)
        self.after = copy.deepcopy(self.after)
        # abstract over response
        self._response = werkzeug.Response()
        self.headers = self._response.headers
        self.cookies = self._response.cookies
    
    
    
    
    @abc.abstractmethod
    def handle(self, request, configuration):
        pass
    
    def respond(self, environment, start_response):
        pass
