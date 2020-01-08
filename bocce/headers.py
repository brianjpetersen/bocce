# standard libraries
import os
import collections
# third party libraries
pass
# first party libraries
from . import (cookies, )


__where__ = os.path.dirname(os.path.abspath(__file__))


class RequestHeaders:
    
    def __init__(self, *items):
        self._headers = {}
        for key, value in items:
            key = str(key)
            titlecase_key = key.title()
            value = str(value)
            if titlecase_key not in self._headers:
                self._headers[titlecase_key] = []
            self._headers[titlecase_key].append(value)
        self.cookies = cookies.RequestCookies.from_header(
            self.get('cookie', '')
        )
    
    @classmethod
    def from_environment(cls, environment):
        items = []
        if 'CONTENT_LENGTH' in environment:
            items.append(('Content-Length', environment['CONTENT_LENGTH']))
        if 'CONTENT_TYPE' in environment:
            items.append(('Content-Type', environment['CONTENT_TYPE']))
        for key, value in environment.items():
            if key.startswith('HTTP_'):
                if key == 'HTTP_CONTENT_LENGTH' and 'CONTENT_LENGTH' in environment:
                    continue
                if key == 'HTTP_CONTENT_TYPE' and 'CONTENT_TYPE' in environment:
                    continue
                key = key[5:].replace('_', '-').title()
                items.append((key, value))
        return cls(*items)
    
    def __iter__(self):
        for key in sorted(self.keys()):
            values = self._headers[key]
            for value in values:
                yield (key, value)
    
    def keys(self):
        return self._headers.keys()
    
    def items(self):
        return list(self)
        
    def __getitem__(self, key):
        titlecase_key = key.title()
        values = self._headers[titlecase_key]
        if len(values) == 1:
            value, = values
            return value
        else:
            return values
    
    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default
    
    def get_first(self, key, default=None):
        if key in self:
            return self[key][0]
        else:
            return default
    
    def get_last(self, key, default=None):
        if key in self:
            return self[key][-1]
        else:
            return default
    
    def __contains__(self, key):
        return key.title() in self._headers
    
    def __len__(self):
        length = 0
        for _ in self:
            length += 1
        return length
    
    def __repr__(self):
        return '{}.{}{}'.format(
            self.__module__, self.__class__.__name__, tuple(self)
        )
    
    def __str__(self):
        return '\n'.join(
            '{}: {}'.format(key, value) for key, value in self
        )


class BaseResponseHeaders:
    
    def __init__(self, *items):
        self._headers = {}
        for key, value in items:
            self[key] = value
    
    def __iter__(self):
        for key in sorted(self.keys()):
            values = self[key]
            for value in values:
                yield (key, value)
    
    def __len__(self):
        return sum(1 for _ in self)
    
    def replace(self, key, value):
        try:
            del self[key]
        except:
            pass
        finally:
            self[key] = value
    
    def delete(self, key, index=-1):
        titlecase_key = str(key).title()
        if isinstance(index, (int, slice)):
            values = self[titlecase_key]
            del values[index]
        else:
            raise TypeError
    
    def items(self):
        return list(self)
    
    def get(self, key, index=None, default=None):
        if key in self:
            values = self[key]
            if index is None:
                return values
            elif isinstance(index, (int, slice)):
                return values[index]
            else:
                raise TypeError
            return 
        else:
            return default
    
    def get_all(self, default=None):
        return self.get(key, default=default)
    
    def get_first(self, key, default=None):
        return self.get(key, index=0, default=default)
    
    def get_last(self, key, default=None):
        return self.get(key, index=-1, default=default)
    
    def __repr__(self):
        return '{}.{}{}'.format(
            self.__module__, self.__class__.__name__, tuple(self)
        )
    
    def __str__(self):
        return '\n'.join(
            '{}: {}'.format(key, value) for key, value in self
        )


class ResponseHeaders(BaseResponseHeaders):
    
    def __getitem__(self, key):
        titlecase_key = str(key).title()
        return self._headers[titlecase_key]
    
    def __setitem__(self, key, value):
        titlecase_key = str(key).title()
        value = str(value)
        if titlecase_key not in self._headers:
            self._headers[titlecase_key] = []
        self._headers[titlecase_key].append(value)
    
    def __delitem__(self, key):
        titlecase_key = str(key).title()
        del self._headers[titlecase_key]
    
    def __contains__(self, key):
        titlecase_key = str(key).title()
        return titlecase_key in self._headers
    
    def keys(self):
        return self._headers.keys()


class BodyResponseHeadersView(ResponseHeaders):
    
    def __init__(self, body):
        self._body = body
    
    @property
    def _headers(self):
        _headers = {}
        keys_and_attribute_names = (
            ('Content-Type', 'content_type'),
            ('Content-Length', 'content_length'),
            ('Content-Encoding', 'content_encoding'),
        )
        for key, attribute_name in keys_and_attribute_names:
            attribute = getattr(self._body, attribute_name, None)
            if attribute is not None:
                _headers[key] = [attribute, ]
        return _headers
    
    def __setitem__(self, key, value):
        raise AttributeError
        
    def __delitem__(self, key):
        raise AttributeError


class CookiesResponseHeadersView(ResponseHeaders):
    
    def __init__(self, cookies):
        self._cookies = cookies
    
    @property
    def _headers(self):
        _headers = {}
        _headers['Set-Cookie'] = [str(cookie) for cookie in self._cookies.values()]
        return _headers
    
    def __setitem__(self, key, value):
        raise AttributeError
        
    def __delitem__(self, key):
        raise AttributeError


class DelegatedResponseHeaders(ResponseHeaders):
    
    def __init__(self, *delegated_headers):
        self._delegated_headers = delegated_headers
        self._headers = {}
        self._all_headers = [self._headers, ]
        self._all_headers.extend(self._delegated_headers)
    
    def __getitem__(self, key):
        titlecase_key = str(key).title()
        for _headers in self._all_headers:
            try:
                return _headers[titlecase_key]
            except:
                continue
        raise KeyError
    
    def __setitem__(self, key, value):
        if any(key in _header for _header in self._delegated_headers):
            raise AttributeError
        super(DelegatedResponseHeaders, self).__setitem__(key, value)
    
    def __delitem__(self, key):
        if any(key in _header for _header in self._delegated_headers):
            raise AttributeError
        super(DelegatedResponseHeaders, self).__delitem__(key)
    
    def __contains__(self, key):
        titlecase_key = str(key).title()
        for _headers in self._all_headers:
            if titlecase_key in _headers:
                return True
        return False
    
    def keys(self):
        keys = set()
        for _headers in self._all_headers:
            for key in _headers.keys():
                keys.add(key)
        return collections.KeysView(keys)
