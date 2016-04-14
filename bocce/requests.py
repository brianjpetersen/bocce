# standard libraries
import os
import abc
import collections
import copy
import json
# third party libraries
import werkzeug
# first party libraries
from . import (surly, utils, headers, cookies, )


__where__ = os.path.dirname(os.path.abspath(__file__))


class Content:
    
    def __init__(self, type, mimetype, length, encoding, md5, charset):
        self.type = type
        self.mimetype = mimetype
        self.length = length
        self.encoding = encoding
        self.md5 = md5
        self.charset = charset


class Accept:
    
    def __init__(self, charsets, encodings, languages, mimetypes):
        self.charsets = charsets
        self.encodings = encodings
        self.languages = languages
        self.mimetypes = mimetypes


class Cache:
    
    def __init__(self, control, if_match, if_none_match, if_modified_since,
                 if_unmodified_since, if_range):
        self.control = control
        self.if_match = if_match
        self.if_none_match = if_none_match
        self.if_modified_since = if_modified_since
        self.if_unmodified_since = if_unmodified_since
        self.if_range = if_range


class Http:
    
    def __init__(self, method, protocol, connection):
        self.method = method
        self.protocol = protocol
        self.connection = connection


class Body:
    
    __slots__ = ('_request', '_stream', 'encoding', )
    
    def __init__(self, _request, encoding='utf-8'):
        self._request = _request
        self._stream = _request.stream
        self.encoding = encoding
    
    @utils.cached_getter(allow_set=False, allow_delete=False)
    def content(self):
        return self._stream.read()
    
    @utils.cached_getter(allow_set=False, allow_delete=False)
    def json(self):
        return json.loads(self.text)
    
    @utils.cached_getter(allow_set=False, allow_delete=False)
    def text(self):
        return self.content.decode(self.encoding)
    
    @utils.cached_getter(allow_set=False, allow_delete=False)
    def form(self):
        raise NotImplementedError
    
    @utils.cached_getter(allow_set=False, allow_delete=False)
    def files(self):
        raise NotImplementedError
    
    def to_file(self, filename=None):
        raise NotImplementedError


class Request:
    
    def __init__(self, request):
        self._request = request
        self.http = Http(
            request.method,
            request.environ.get('SERVER_PROTOCOL', None),
            request.environ.get('HTTP_CONNECTION', None),
        )
        self.headers = headers.RequestHeaders.from_environment(request.environ)
        self.cookies = self.headers.cookies
        self.url = surly.Url.from_environment(request.environ)
        self.date = request.date
        self.content = Content(
            request.content_type,
            request.mimetype,
            request.content_length,
            request.content_encoding,
            request.content_md5,
            request.charset,
        )
        self.accept = Accept(
            request.accept_charsets,
            request.accept_encodings,
            request.accept_languages,
            request.accept_mimetypes,
        )
        self.pragma = request.pragma
        self.user_agent = request.user_agent
        self.body = Body(request)
        self.remote_address = request.remote_addr
        self.is_xhr = request.is_xhr
        self.range = request.range
        self.cache = Cache(
            request.cache_control,
            request.if_match,
            request.if_none_match,
            request.if_modified_since, 
            request.if_unmodified_since,
            request.if_range,
        )
    
    @classmethod
    def from_environment(cls, environment):
        with werkzeug.Request(environment, populate_request=False) as request:
            return cls(request)
    
    def __str__(self):
        raise NotImplementedError
    
    def __repr__(self):
        raise NotImplementedError
    
    def __getnewargs__(self):
        return (self._request, )
