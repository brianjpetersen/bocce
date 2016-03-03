# standard libraries
import os
import abc
import collections
import copy
import json
# third party libraries
import werkzeug
# first party libraries
from . import (surly, utils, headers, )
Headers = headers.Immutable


__where__ = os.path.dirname(os.path.abspath(__file__))


Content = collections.namedtuple(
    'RequestContent', (
        'type', 'mimetype', 'length', 'encoding', 'md5', 'charset', 
    )
)

Accept = collections.namedtuple(
    'RequestAccept', ('charsets', 'encodings', 'languages', 'mimetypes', )
)

Cache = collections.namedtuple(
    'RequestCache', (
        'control', 'if_match', 'if_none_match', 'if_modified_since', 
        'if_unmodified_since', 'if_range',
    )
)

Http = collections.namedtuple(
    'RequestHttp', ('method', 'protocol', 'connection', )
)


class Body:
    
    __slots__ = ('_request', '_stream', 'encoding', )
    
    def __init__(self, _request, encoding='utf-8'):
        self._request = _request
        self._stream = _request.stream
        self.encoding = encoding
    
    @utils.cached_property
    def content(self):
        return self._stream.read()
    
    @utils.cached_property
    def json(self):
        return json.loads(self.text)
    
    @utils.cached_property
    def text(self):
        return self.content.decode(self.encoding)
    
    @utils.cached_property
    def form(self):
        raise NotImplementedError
    
    @utils.cached_property
    def files(self):
        raise NotImplementedError
    
    def to_file(self, filename=None):
        raise NotImplementedError


class Cookies(collections.abc.Mapping):
    
    def __init__(self, **kwargs):
        self._dict = kwargs
    
    @classmethod
    def from_environment(cls, environment):
        raise NotImplementedError
    
    @classmethod
    def from_header(cls, header):
        raise NotImplementedError
    
    def __getitem__(self, key):
        return self._dict[key]
    
    def __iter__(self):
        return iter(self._dict)
    
    def __len__(self):
        return len(self._dict)
    
    def __str__(self):
        return '; '.join(
            '{}={}'.format(key, value) for key, value in self.items()
        )
    
    def __repr__(self):
        return '{}.{}({})'.format(
            self.__module__, self.__class__.__name__, ', '.join(
                "{}='{}'".format(key, value) for key, value in self.items()
            )
        )


def _by_index(index):
    def getter(self):
        return tuple.__getitem__(self, index)
    return getter


class Request(tuple):
    
    @classmethod
    def from_environment(cls, environment):
        with werkzeug.Request(environment, populate_request=False) as request:
            http = Http(
                request.method,
                environment.get('SERVER_PROTOCOL', None),
                environment.get('HTTP_CONNECTION', None),
            )
            headers = Headers.from_environment(environment)
            url = surly.Url.from_environment(environment)
            cookies = Cookies(**request.cookies)
            date = request.date
            content = Content(
                request.content_type,
                request.mimetype,
                request.content_length,
                request.content_encoding,
                request.content_md5,
                request.charset,
            )
            accept = Accept(
                request.accept_charsets,
                request.accept_encodings,
                request.accept_languages,
                request.accept_mimetypes,
            )
            pragma = request.pragma
            user_agent = request.user_agent
            body = Body(request)
            remote_address = request.remote_addr
            is_xhr = request.is_xhr
            range = request.range
            cache = Cache(
                request.cache_control,
                request.if_match,
                request.if_none_match,
                request.if_modified_since, 
                request.if_unmodified_since,
                request.if_range,
            )
        return cls(
            (
                headers, url, cookies, date, content, accept, pragma, 
                user_agent, body, remote_address, is_xhr, range, cache,
                http, environment,
            )
        )
    
    headers = property(_by_index(0))
    url = property(_by_index(1))
    cookies = property(_by_index(2))
    date = property(_by_index(3))
    content = property(_by_index(4))
    accept = property(_by_index(5))
    pragma = property(_by_index(6))
    user_agent = property(_by_index(7))
    body = property(_by_index(8))
    remote_address = property(_by_index(9))
    is_xhr = property(_by_index(10))
    range = property(_by_index(11))
    cache = property(_by_index(12))
    http = property(_by_index(13))
    environment = property(_by_index(14))
    
    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError
    
    def __getnewargs__(self):
        return tuple(self)
